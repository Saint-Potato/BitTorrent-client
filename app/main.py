import json
import sys
import bencodepy
import app.torrent
import app.tracker
import app.protocol_new
import app.download_manager
import asyncio



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
        tor = app.torrent.Torrent(torrent_path)
        print(tor)

    elif command == "peers":
        torrent_path = sys.argv[2]
        tor = app.torrent.Torrent(torrent_path)
        tor_tracker = app.tracker.Tracker(tor)
        response = asyncio.run(tor_tracker.connect())
        print(response)

    elif command == "handshake":
        torrent_path = sys.argv[2]
        peer_address = sys.argv[3]
        peer_ip, peer_port = peer_address.split(":")

        async def perform_handshake():
            tor = app.torrent.Torrent(torrent_path)
            peer_connection = app.protocol_new.PeerConnection(tor, peer_ip, int(peer_port))
            await peer_connection.connect(handshake_only=True)
            print(f"Peer ID: {peer_connection.peer_id.hex()}")

        asyncio.run(perform_handshake())
    
    elif command == "download_piece":
        output_path = sys.argv[3]
        torrent_path = sys.argv[4]
        piece_index = int(sys.argv[5])

        async def download_piece_and_save():
            tor = app.torrent.Torrent(torrent_path)
            tor_tracker = app.tracker.Tracker(tor)
            peers = await tor_tracker.connect()

            peer_ip, peer_port = peers.peers[0]
            peer_connection = app.protocol_new.PeerConnection(tor, peer_ip, peer_port)
            
            try:
                await peer_connection.connect()
                await peer_connection.send_interested()
                piece_data = await peer_connection.download_piece(piece_index)
                
                with open(output_path, "wb") as f:
                    f.write(piece_data)
                print(f"Piece {piece_index} downloaded to {output_path}")

            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                peer_connection.close()

        asyncio.run(download_piece_and_save())

    elif command == "download":
        output_path = sys.argv[2]
        torrent_path = sys.argv[3]

        async def download_torrent():
            tor = app.torrent.Torrent(torrent_path)
            tor_tracker = app.tracker.Tracker(tor)
            peers_info = await tor_tracker.connect()

            download_manager = app.download_manager.DownloadManager(tor)

            # Add peers to the download manager
            for peer_ip, peer_port in peers_info.peers:
                await download_manager.add_peer(peer_ip, peer_port)

            # Start the download
            await download_manager.start_download()

            # After download is complete, you would assemble the pieces into a file
            print("Download complete!")

        asyncio.run(download_torrent())

    else:
        raise NotImplementedError(f"Unknown command {command}")

if __name__ == "__main__":
    main()