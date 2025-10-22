#still need to incorporate this file into the peer.py file
class Config:
    def __init__(self):
        self.num_preferred_neighbors = None
        self.unchoking_interval = None
        self.optimistic_unchoking_interval = None
        self.file_name = None
        self.file_size = None
        self.piece_size = None
        self.num_pieces = None

    def parse_common_config(self, filepath):
        #parses Common.cfg/loads configuration values
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                key = parts[0]
                value = parts[1]
                match key:
                    case "NumberOfPreferredNeighbors":
                        self.num_preferred_neighbors = int(value)
                    case "UnchokingInterval":
                        self.unchoking_interval = int(value)
                    case "OptimisticUnchokingInterval":
                        self.optimistic_unchoking_interval = int(value)
                    case "FileName":
                        self.file_name = value
                    case "FileSize":
                        self.file_size = int(value)
                    case "PieceSize":
                        self.piece_size = int(value)
        self.num_pieces = ((self.file_size + self.piece_size - 1) // self.piece_size)


class PeerInfoList:
    def __init__(self):
        self.peers = {}

    def parse_peer_info_config(self, filepath):
        #parses PeerInfo.cfg/loads peer information
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) != 4:
                    continue
                try:
                    peer_id = int(parts[0])
                    host = parts[1]
                    port = int(parts[2])
                    has_file = bool(int(parts[3]))

                    self.peers[peer_id] = {'host': host, 'port': port, 'has_file': has_file}
                except ValueError:
                    continue

    def get_peer(self, peer_id):
        #returns peer info dictionary for a specific peer
        if peer_id in self.peers:
            return self.peers[peer_id]
        else:
            return None

    def get_all_peers(self):
        #returns sorted list of all peer IDs
        result = []
        for peer_id in sorted(self.peers.keys()):
            result.append(peer_id)
        return result

    def get_peers_with_file(self):
        #returns list of peer IDs that have the complete file
        result = []
        for pid, peer_info in self.peers.items():
            if peer_info['has_file']:
                result.append(pid)
            else:
                continue
        return result

    def get_peers_without_file(self):
        #returns list of peer IDs that need to download the file
        result = []
        for pid, peer_info in self.peers.items():
            if not peer_info['has_file']:
                result.append(pid)
            else:
                continue
        return result

    def get_other_peers(self, my_peer_id):
        #returns list of all peers except my_peer_id
        result = []
        for pid in self.peers.keys():
            if pid != my_peer_id:
                result.append(pid)
            else:
                continue
        return result

    def get_peers_started_before(self, my_peer_id):
        #returns list of peers with IDs less than my_peer_id
        result = []
        for pid in sorted(self.peers.keys()):
            if pid < my_peer_id:
                result.append(pid)
            else:
                continue
        return result

    def num_peers(self):
        #returns total number of peers
        return len(self.peers)
