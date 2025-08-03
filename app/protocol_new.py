
import asyncio
import struct
import hashlib
import bitstring

# Message IDs (as per BitTorrent protocol)
CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
CANCEL = 8
PORT = 9

# The default block size for piece requests
BLOCK_SIZE = 2**14  # 16 KB

class PeerConnection:
    """
    Manages the connection and communication with a single peer.
    """
    def __init__(self, torrent, ip, port):
        self.torrent = torrent
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.bitfield = None  # Peer's bitfield of available pieces
        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.peer_id = None

    async def connect(self, handshake_only=False):
        """
        Establishes a TCP connection with the peer and performs the handshake.
        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout=10)
            await self._perform_handshake()
            if not handshake_only:
                self.bitfield = await self._receive_bitfield()
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            print(f"Failed to connect to {self.ip}:{self.port}: {e}")
            raise

    async def _perform_handshake(self):
        """
        Sends and receives the initial BitTorrent handshake.
        """
        pstr = b'BitTorrent protocol'
        handshake = struct.pack(
            '>B19s8x20s20s',
            19,  # Length of protocol string
            pstr,
            self.torrent.info_hash,
            b'-PC0001-123456789012'  # A common peer ID format
        )
        self.writer.write(handshake)
        await self.writer.drain()

        response = await self.reader.readexactly(68)

        self.peer_id = response[48:]
        # Note: A more robust client would validate the info_hash from the peer
        if response[1:20] != pstr:
            raise ValueError("Invalid protocol in handshake response.")

    async def _receive_message(self):
        """
        Receives a message from the peer and returns its ID and payload.
        """
        header = await self.reader.readexactly(4)
        length = struct.unpack(">I", header)[0]
        if length == 0:
            return None, None  # Keep-alive message

        msg_id = (await self.reader.readexactly(1))[0]
        payload = await self.reader.readexactly(length - 1)
        return msg_id, payload

    async def _send_message(self, msg_id, payload=b''):
        """
        Constructs and sends a message to the peer.
        """
        length = 1 + len(payload)
        message = struct.pack(">I", length) + bytes([msg_id]) + payload
        self.writer.write(message)
        await self.writer.drain()

    async def _receive_bitfield(self):
        """
        Receives the peer's bitfield message.
        """
        msg_id, payload = await self._receive_message()
        if msg_id != BITFIELD:
            # Some clients might send HAVE messages instead of a bitfield initially
            print("Warning: First message was not BITFIELD. Peer may not have any pieces yet.")
            return None
        return bitstring.BitArray(payload)

    async def send_interested(self):
        """
        Sends an 'interested' message to the peer.
        """
        await self._send_message(INTERESTED)
        self.am_interested = True

    async def download_piece(self, piece_index):
        """
        Downloads a complete piece from the peer by requesting its blocks.
        """
        if not self.bitfield or not self.bitfield[piece_index]:
            raise ValueError(f"Peer does not have piece {piece_index}")

        # Wait for the peer to unchoke us
        while self.peer_choking:
            msg_id, _ = await self._receive_message()
            if msg_id == UNCHOKE:
                self.peer_choking = False
            # A real client would handle other messages here too (HAVE, etc.)

        piece_size = self.torrent.pieces_length
        piece_data = bytearray(piece_size)
        offset = 0

        while offset < piece_size:
            block_size = min(BLOCK_SIZE, piece_size - offset)
            await self._send_message(REQUEST, struct.pack(">III", piece_index, offset, block_size))

            msg_id, payload = await self._receive_message()
            if msg_id == PIECE:
                p_index, p_begin, block_data = self._parse_piece_message(payload)
                if p_index == piece_index:
                    piece_data[p_begin:p_begin + len(block_data)] = block_data
                    offset += len(block_data)
            else:
                # Handle other messages or errors
                print(f"Received unexpected message ID {msg_id} while downloading piece.")
                continue

        if self._verify_piece(piece_index, piece_data):
            print(f"Piece {piece_index} downloaded and verified successfully.")
            return piece_data
        else:
            raise ValueError(f"Piece {piece_index} failed verification.")

    def _parse_piece_message(self, payload):
        """
        Parses a PIECE message payload.
        """
        index = struct.unpack(">I", payload[:4])[0]
        begin = struct.unpack(">I", payload[4:8])[0]
        block_data = payload[8:]
        return index, begin, block_data

    def _verify_piece(self, piece_index, piece_data):
        """
        Verifies the hash of a downloaded piece.
        """
        expected_hash = self.torrent.pieces[piece_index]
        actual_hash = hashlib.sha1(piece_data).digest()
        return actual_hash == expected_hash

    def close(self):
        """
        Closes the connection with the peer.
        """
        if self.writer:
            self.writer.close()

