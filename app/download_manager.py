
import asyncio
from collections import deque
from .protocol_new import PeerConnection

class DownloadManager:
    def __init__(self, torrent):
        self.torrent = torrent
        self.peers = deque()
        self.pieces = [False] * len(self.torrent.pieces)
        self.downloaded_pieces = 0

    async def add_peer(self, ip, port):
        peer = PeerConnection(self.torrent, ip, port)
        try:
            await peer.connect()
            self.peers.append(peer)
            return True
        except Exception as e:
            print(f"Failed to connect to peer {ip}:{port}: {e}")
            return False

    async def start_download(self):
        print("Starting download...")
        # Get peers from tracker
        # For now, we'll assume peers are added manually

        # Create a task for each peer to download pieces
        tasks = [self._start_peer_session(peer) for peer in self.peers]
        await asyncio.gather(*tasks)

    async def _start_peer_session(self, peer):
        await peer.send_interested()

        while self.downloaded_pieces < len(self.pieces):
            if peer.peer_choking:
                # If the peer is choking us, wait for an unchoke message
                msg_id, _ = await peer._receive_message()
                if msg_id == 1: # Unchoke
                    peer.peer_choking = False
                else:
                    # Handle other messages if necessary
                    continue

            # Find a piece to download
            piece_index = self._find_piece_to_download(peer)
            if piece_index is None:
                # No available pieces to download from this peer for now
                # In a real client, we might wait or try another peer
                await asyncio.sleep(1) # a small delay
                continue

            try:
                piece_data = await peer.download_piece(piece_index)
                if piece_data:
                    self.pieces[piece_index] = True
                    self.downloaded_pieces += 1
                    print(f"Downloaded piece {piece_index}. Total downloaded: {self.downloaded_pieces}/{len(self.pieces)}")
                    # Here you would save the piece to a file
            except Exception as e:
                print(f"Error downloading piece {piece_index} from peer {peer.ip}: {e}")
                # Mark the piece as not downloaded so another peer can try
                self.pieces[piece_index] = False
                # It might be good to disconnect from this peer if it consistently fails
                break

    def _find_piece_to_download(self, peer):
        for i, piece in enumerate(self.pieces):
            if not piece and peer.bitfield and i < len(peer.bitfield) and peer.bitfield[i]:
                return i
        return None
