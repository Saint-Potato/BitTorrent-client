import app.torrent
import random
import bencodepy
import socket
from struct import unpack
import aiohttp
from urllib.parse import urlencode

class TrackerResponse:

    def __init__(self, response: dict):
        self.response = response

    
    @property
    def failure(self):
        if(b'failure reason' in self.response):
            return self.response[b'failure response'].decode('utf-8')
        return None
    
    @property
    def interval(self) -> int:
        #interval to wait before sending requests to tracker
        return self.response.get(b'interval', 0)
    
    @property
    def complete(self) -> int:
        #peers with complete files -> seeders
        return self.response.get(b'complete', 0)
    
    @property
    def incomplete(self) -> int:
        #number of leechers
        return self.response.get(b'incomplete', 0)
    
    @property
    def peers(self):
        peers = self.response[b'peers']
        peers_ = []
        if(type(peers) == list):
            for peer in peers:
                ip = peer[b'ip'].decode('utf-8')
                port = peer[b'port']
                peers_.append((ip, port))
            return peers_
        else:
            peers_ = [peers[i:i+6] for i in range(0, len(peers), 6)]

            return [(socket.inet_ntoa(p[:4]), _decode_port(p[4:])) for p in peers_]
        
    def __str__(self):
        res = ""
        for p in self.peers:
            res += (p[0] + ':' + str(p[1]) + '\n')
        return res
        
class Tracker:

    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = _calculate_peer_id()
        # self.http_client = aiohttp.ClientSession()

    async def connect(self, 
                      first: bool = None,
                      uploaded: int = 0,
                      downloaded: int = 0):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'port': 6889,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.file_size - downloaded,
            'compact': 1
        }
        if(first):
            params['event'] = 'started'

        url = self.torrent.announce + '?' + urlencode(params)
        print('Establishing connection to: ' + url)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if not response.status == 200:
                    raise ConnectionError(f'Unable to connect. Status: {response.status}')
                data = await response.read()
                self.check_for_failure(data) #tries to decode data and find 'failure'
                return TrackerResponse(bencodepy.decode(data))
        
    def close(self):
        self.http_client.close()

    def check_for_failure(self, tracker_response):
        #tracker message in case of error contains utf-8 message
        try:
            message = tracker_response.decode("utf-8")
            if "failure" in message:
                raise ConnectionError("Unable to connect: {message}")
        #unicodedecode error signals no utf-8 message hence no error
        except UnicodeDecodeError:
            pass
        


#format :  -XXYYYY-<random> 
#XX -> client, YYYY -> version
def _calculate_peer_id():
    unique = ""
    for _ in range(12):
        unique+= str(random.randint(0,9))

    return '-PC0001-' + unique

def _decode_port(port):
    
    #Converts a 32-bit packed binary port number to int
    
    # Convert from C style big-endian encoded as unsigned short
    return unpack(">H", port)[0]