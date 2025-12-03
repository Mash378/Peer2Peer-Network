import sys
import time
import threading
from bitarray import bitarray
from config import Config, PeerInfoList
from peer import Peer
from LogFunct import Logger

def main():
    #Parse CLI for peer id
    if len(sys.argv) != 2:
        print("Usage: python peerProcess.py <peer_id>")
        sys.exit(1)

    try:
        peer_id = int(sys.argv[1])
    except ValueError:
        print("Error: peer_id must be an integer")
        sys.exit(1)
    
    #loads the config files
    config = Config()
    config.parse_common_config('Common.cfg')

    peer_info = PeerInfoList()
    peer_info.parse_peer_info_config('PeerInfo.cfg')

    peer_data = peer_info.get_peer(peer_id)
    if peer_data is None:
        print(f"Error: Peer ID {peer_id} not found in PeerInfo.cfg")
        sys.exit(1)

    log_filename = f'log_peer_{peer_id}.log'
    logger = Logger(log_filename)

    #init bitfield based on if peer has file
    bitfield = bitarray(config.num_pieces)
    if peer_data['has_file']:
        bitfield.setall(1)
    else:
        bitfield.setall(0)

    #config preferences
    host = peer_data['host']
    port = peer_data['port']
    k = config.num_preferred_neighbors
    p = config.unchoking_interval
    m = config.optimistic_unchoking_interval

    peer = Peer(host, port, peer_id, bitfield, k, p, m, logger, config, peer_info)

    if peer_data['has_file']:
        peer.all_peers_complete_bitfields[peer_id] = True

    #listen for connections
    listener_thread = threading.Thread(target=peer.listen_for_connections, daemon=False)
    listener_thread.start()
    print(f"Peer {peer_id} started listening on {host}:{port}")

    peer.start_unchoking_intervals()

    peers_before = peer_info.get_peers_started_before(peer_id)
    for other_peer_id in peers_before:
        other_peer_data = peer_info.get_peer(other_peer_id)
        print(f"Connecting to peer {other_peer_id} at {other_peer_data['host']}:{other_peer_data['port']}")
        try:
            peer.connect_to_peers(other_peer_data['host'], other_peer_data['port'])
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to connect to peer {other_peer_id}: {e}")

    #check if peers complete and shutdown
    while not peer.should_terminate():
        peer._check_all_done()
        time.sleep(1)

    peer.shutdown()
    print(f"Peer {peer_id} has terminated")

if __name__ == '__main__':
    main()
