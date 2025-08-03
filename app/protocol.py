import asyncio
import struct
import hashlib

# Message Types (as per BitTorrent protocol)
CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
CANCEL = 8

class PeerConnection:
    def __init__(self, ip, port, info_hash, peer_id):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        await self.send_handshake()
        await self.receive_handshake()

    async def send_handshake(self):
        pstr = b'BitTorrent protocol'
        reserved = b'\x00' * 8
        handshake = struct.pack('>B', len(pstr)) + pstr + reserved + self.info_hash + self.peer_id
        self.writer.write(handshake)
        await self.writer.drain()

    async def receive_handshake(self):
        response = await self.reader.read(68)
        if len(response) < 68 or response[1:20] != b'BitTorrent protocol':
            raise Exception("Invalid handshake")
        # Optional: validate info_hash matches

    async def send_interested(self):
        self._send_message(INTERESTED)

    def _send_message(self, msg_id, payload=b''):
        length = struct.pack(">I", 1 + len(payload))
        message = length + bytes([msg_id]) + payload
        self.writer.write(message)

    async def receive_message(self):
        header = await self.reader.readexactly(4)
        length = struct.unpack(">I", header)[0]
        if length == 0:
            return None, None  # Keep-alive
        msg_id = await self.reader.readexactly(1)
        payload = await self.reader.readexactly(length - 1)
        return msg_id[0], payload

    async def request_piece(self, index, begin, length):
        payload = struct.pack(">III", index, begin, length)
        self._send_message(REQUEST, payload)
        await self.writer.drain()

    async def read_piece(self):
        while True:
            msg_id, payload = await self.receive_message()
            if msg_id == PIECE:
                index = struct.unpack(">I", payload[:4])[0]
                begin = struct.unpack(">I", payload[4:8])[0]
                block = payload[8:]
                return index, begin, block