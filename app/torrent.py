import bencodepy
import hashlib

class Torrent:
    def __init__(self):
        self.name = None              # Name of the torrent (from metadata)
        self.length = None          # Total size of the file(s)
        self.info_hash = None    # SHA-1 hash of the 'info' dictionary

    def __str__(self):
        return f"Torrent(name='{self.name}', length={self.length}, info_hash='{self.info_hash}')"
    

def extract_info_section(raw_data):
    """
    Extracts the exact bencoded byte string of the 'info' dictionary
    so we can compute the info hash.
    """
    decoder = bencodepy.BencodeDecoder()
    stream = memoryview(raw_data)
    idx = 0

    # Decode top-level dictionary
    if stream[idx:idx+1] != b'd':
        raise ValueError("Torrent file does not start with a dictionary")
    idx += 1

    while idx < len(stream):
        key, key_len = decoder._decode_next(stream[idx:])
        idx += key_len

        if key == b'info':
            info_start = idx
            _, info_len = decoder._decode_next(stream[idx:])
            info_end = idx + info_len
            return bytes(stream[info_start:info_end])

        # Skip the value associated with this key
        _, val_len = decoder._decode_next(stream[idx:])
        idx += val_len

    raise ValueError("'info' key not found in torrent")

def parse_torrent(torrent_path):
    with open(torrent_path, 'rb') as f:
        raw = f.read()
    torrent = bencodepy.decode(raw)

    # Extract fields
    info = torrent[b'info']
    announce = torrent[b'announce']
    length = info.get(b'length') or sum(f[b'length'] for f in info[b'files'])  # support multi-file

    # Re-encode the info dictionary
    encoded_info = bencodepy.encode(info)

    # Compute SHA-1 hash
    info_hash = hashlib.sha1(encoded_info).hexdigest()
    # Extract piece length and pieces
    piece_length = info[b'piece length']
    pieces = info[b'pieces']
    piece_hashes = [pieces[i:i+20].hex() for i in range(0, len(pieces), 20)]

    return announce.decode(), length, info_hash, piece_length, piece_hashes


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
