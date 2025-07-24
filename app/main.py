import json
import sys
import bencodepy
import app.torrent



def main():
    command = sys.argv[1]

    print("Logs from your program will appear here!", file=sys.stderr)

    if command == "decode":
        bencoded_value = sys.argv[2].encode()

        def bytes_to_str(data):
            if isinstance(data, bytes):
                return data.decode(errors="replace")
            raise TypeError(f"Type not serializable: {type(data)}")

        result = bencodepy.decode(bencoded_value)
        print(json.dumps(app.torrent.bdecode_to_str(result)))

    elif command == "info":
        torrent_path = sys.argv[2]
        tracker_url, file_size, info_hash = app.torrent.parse_torrent(torrent_path)
        print(f"Tracker URL: {tracker_url}")
        print(f"Length: {file_size}")
        print(f"Info Hash: {info_hash}")

    else:
        raise NotImplementedError(f"Unknown command {command}")

if __name__ == "__main__":
    main()