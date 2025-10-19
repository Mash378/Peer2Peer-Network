import logging
from datetime import datetime
import os

class Logger:
    def __init__(self, peer_id, log_dir="."):
        self.peer_id = peer_id
        self.log_path = os.path.join(log_dir, f"log_peer_{peer_id}.log")

        logging.basicConfig(filename=self.log_path, level=logging.INFO, format="%(message)s")

    def timestamp(self):
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def log_connection_made(self, peer_id_2):
        """When this peer makes a TCP connection to another peer."""
        message = f"[{self._timestamp()}]: Peer {self.peer_id} makes a connection to Peer {peer_id_2}."
        logging.info(message)

    def log_connection_received(self, peer_id_2):
        """When this peer is connected from another peer."""
        message = f"[{self._timestamp()}]: Peer {self.peer_id} is connected from Peer {peer_id_2}."
        logging.info(message)

    def log_preferred_neighbors(self, preferred_list):
        """
        When this peer changes preferred neighbors.
        preferred_list: list of peer IDs.
        """
        neighbor_str = ", ".join(map(str, preferred_list))
        message = f"[{self._timestamp()}]: Peer {self.peer_id} has the preferred neighbors [{neighbor_str}]."
        logging.info(message)
