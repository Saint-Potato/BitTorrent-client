import json
import sys
import bencodepy
# import bencodepy - available if you need it!
# import requests - available if you need it!

# Examples:
#
# - decode_bencode(b"5:hello") -> b"hello"
# - decode_bencode(b"10:hello12345") -> b"hello12345"

def decode_bencode(bencoded_value):
    #decode strings
    # bc = bencodepy.Bencode(encoding = "utf-8")
    # return bc.decode(bencoded_value)
    decoded = bencodepy.decode(bencoded_value)
    def bytes_to_str(data):
        if isinstance(data, dict):
            return {k.decode(): bytes_to_str(v) for k, v in data.items()}  # Convert keys
        elif isinstance(data, list):
            return [bytes_to_str(i) for i in data]  # Convert list elements
        elif isinstance(data, bytes):
            return data.decode(errors="ignore")  # Convert bytes to string safely
        return data  # Leave other data types unchanged

    return bytes_to_str(decoded)

    # def extract_string(data):
    #     length, rest = data.split(b":", 1)
    #     length = int(length)
    #     return rest[:length], rest[length:]
    # def decode(data):
    #     if chr(data[0]).isdigit():
    #         decoded_str, rest = extract_string(data)
    #         return decoded_str, rest
    #     elif chr(data[0]) == 'i':
    #         end = data.find(b"e")
    #         return int(data[1:end]), data[end+1:]
    #     elif chr(data[0]) == 'l':
    #         data = data[1:]
    #         list_decoded = []
    #         while not data.startswith(b"e"):
    #             item, data = decode(data)
    #             list_decoded.append(item)
    #         return list_decoded, data[1:]
    #     elif chr(data[0] == 'd'):
    #         data = b"l" + data[1:]
    #         res_list = decode_bencode(data)
    #         decoded_dictionary = {}
    #         for i in range(len(res_list)):
    #             decoded_dictionary[res_list[i]] = res_list[i+1]
    #             i+=1
    #         return decoded_dictionary
    #     else:
    #         raise NotImplementedError("Only strings are supported at the moment")
    # decoded_value, _ = decode(bencoded_value)
    # return decoded_value

def parse_torrent(torrent_path):
    f = open(torrent_path, "rb")
    meta_info = f.read()
    result = decode_bencode(meta_info)
    tracker_url = result['announce']
    file_size = result['info']['length']
    return tracker_url,file_size




def main():
    command = sys.argv[1]

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    if command == "decode":
        bencoded_value = sys.argv[2].encode()  #converts string to bstring

        # json.dumps() can't handle bytes, but bencoded "strings" need to be
        # bytestrings since they might contain non utf-8 characters.
        #
        # Let's convert them to strings for printing to the console.
        def bytes_to_str(data):
            if isinstance(data, bytes):
                return data.decode()

            raise TypeError(f"Type not serializable: {type(data)}")

        # Uncomment this block to pass the first stage
        print(json.dumps(decode_bencode(bencoded_value), default=bytes_to_str))

    elif command == "info":
        torrent_path = sys.argv[2]
        tracker_url, file_size = parse_torrent(torrent_path)
        print(f"Tracker URL: {tracker_url}")
        print(f"Length: {file_size}" )

    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
