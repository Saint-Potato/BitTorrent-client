import hashlib
from collections import namedtuple
import bencodepy
# from bencodepy import Decoder

TorrentFile = namedtuple('TorrentFile', ['name', 'length'])

class Torrent:

    # Represent Torrent meta-data

    def __init__(self, filename):

        self.filename = filename
        self.files = []

        with open(self.filename, 'rb') as f:
            meta_info = f.read()
            # self.meta_info = bencodepy.Decoder().decode(meta_info)
            self.meta_info = bencodepy.decode(meta_info)
            info = bencodepy.encode(self.meta_info[b'info'])
            self.name = self.meta_info[b'info'][b'name'].decode('utf-8')
            self.announce = self.meta_info[b'announce'].decode('utf-8')
            self.pieces_length = self.meta_info[b'info'][b'piece length']
            self.file_size = self.meta_info[b'info'][b'length']
            self.info_hash = hashlib.sha1(info).digest()
            self._identify_files()
        
    @property
    def multi_file(self) -> bool:
        # If the info dict contains a files element then it is a multi-file
        return b'files' in self.meta_info[b'info']

    def __str__(self):
        piece_hashes = "\n".join(hash.hex() for hash in self.pieces)
        return f"Tracker URL: {self.announce}\n" \
                f"Length: {self.file_size}\n" \
                f"Info Hash: {self.info_hash.hex()}\n" \
                f"Piece Length: {self.pieces_length}\n" \
                f"Piece Hashes: \n{piece_hashes}"
    
    def _identify_files(self):
        if self.multi_file:
            raise RuntimeError('Multi-file torrents aren\'t supported yet')
        self.files.append(TorrentFile(self.meta_info[b'info'][b'name'].decode('utf-8'), self.meta_info[b'info'][b'length']))

    @property
    def pieces(self):
        # The info pieces is a string representing all pieces SHA1 hashes (each 20 bytes long). Read that data and slice it up into the actual pieces
        data = self.meta_info[b'info'][b'pieces']
        pieces = []
        offset = 0
        length = len(data)

        while offset < length:
            pieces.append(data[offset:offset + 20])
            offset += 20
        return pieces
    

    # def extract_info_section(raw_data):
        
    #     decoder = bencodepy.BencodeDecoder()
    #     stream = memoryview(raw_data)
    #     idx = 0

    #     # Decode top-level dictionary
    #     if stream[idx:idx+1] != b'd':
    #         raise ValueError("Torrent file does not start with a dictionary")
    #     idx += 1

    #     while idx < len(stream):
    #         key, key_len = decoder._decode_next(stream[idx:])
    #         idx += key_len

    #         if key == b'info':
    #             info_start = idx
    #             _, info_len = decoder._decode_next(stream[idx:])
    #             info_end = idx + info_len
    #             return bytes(stream[info_start:info_end])

    #         # Skip the value associated with this key
    #         _, val_len = decoder._decode_next(stream[idx:])
    #         idx += val_len

    #     raise ValueError("'info' key not found in torrent")

# def parse_torrent(torrent_path):
#     with open(torrent_path, 'rb') as f:
#         raw = f.read()
#     torrent = bencodepy.decode(raw)

#     # Extract fields
#     info = torrent[b'info']
#     announce = torrent[b'announce']
#     length = info.get(b'length') or sum(f[b'length'] for f in info[b'files'])  # support multi-file

#     # Re-encode the info dictionary
#     encoded_info = bencodepy.encode(info)

#     # Compute SHA-1 hash
#     info_hash = hashlib.sha1(encoded_info).hexdigest()
#     # Extract piece length and pieces
#     piece_length = info[b'piece length']
#     pieces = info[b'pieces']
#     piece_hashes = [pieces[i:i+20].hex() for i in range(0, len(pieces), 20)]

#     return announce.decode(), length, info_hash, piece_length, piece_hashes


def bdecode_to_str(obj):
    if isinstance(obj, dict):
        return {k.decode() if isinstance(k, bytes) else k: bdecode_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [bdecode_to_str(i) for i in obj]
    elif isinstance(obj, bytes):
        try:
            return obj.decode()
        except:
            return obj  # if it can't be decoded as UTF-8
    else:
        return obj
