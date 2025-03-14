import bencodepy

def decode_bencode(bencoded_value):
    return bencodepy.decode(bencoded_value)
 

file_path = "sample.torrent"
f = open(file_path, "rb")
meta_info = f.read()
result = decode_bencode(meta_info)
tracker_url = result[b'announce'].decode()
file_size = result[b'info'][b'length']
print("Tracker URL: ",tracker_url)
print("Length: ", file_size)