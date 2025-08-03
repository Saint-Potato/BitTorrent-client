# BitTorrent Client in Python

This is a simple BitTorrent client written in Python. It can be used to download files from the BitTorrent network.

## Features

* Decode bencoded files
* Get information about a torrent file
* Find peers for a torrent
* Download pieces of a file
* Download a complete file

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/Saint-Potato/BitTorrent-client.git
   ```
2. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

```sh
./your_bittorrent.sh <command> <args>
```

### Commands

* `decode <bencoded_string>`: Decode a bencoded string.
* `info <torrent_file>`: Get information about a torrent file.
* `peers <torrent_file>`: Find peers for a torrent.
* `handshake <torrent_file> <peer_ip>:<peer_port>`: Perform a handshake with a peer.
* `download_piece -o <output_file> <torrent_file> <piece_index>`: Download a piece of a file.
* `download -o <output_file> <torrent_file>`: Download a complete file.
