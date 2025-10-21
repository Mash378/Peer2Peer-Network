import logging
from datetime import datetime
import os

class Logger:
    def __init__(self, peer_id, log_dir="."):
        self.peer_id = peer_id
        self.peer_dir = os.path.join(log_dir, self.peer_id)
        os.makedirs(self.peer_dir, exist_ok=True)

        self.log_path = os.path.join(self.peer_dir, f"log_peer_{self.peer_id}.log")

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


    #------Choking/Unchoking-------------------
    def log_optimistic_unchoke(self, peer_id_2):
        logging.info(
            f"[{self._timestamp()}]: Peer {self.peer_id} has the optimistically unchoked neighbor [{peer_id_2}].")

    #choked log message
    def log_choked(self, peer_id_2):
        logging.info(f"[{self._timestamp()}]: Peer {self.peer_id} is choked by Peer {peer_id_2}.")

    #unchoked log message
    def log_unchoked(self, peer_id_2):
        logging.info(f"[{self._timestamp()}]: Peer {self.peer_id} is unchoked by Peer {peer_id_2}.")

    #interest log message
    def log_interested(self, peer_id_2):
        logging.info(
            f"[{self._timestamp()}]: Peer {self.peer_id} received the 'interested' message from [{peer_id_2}].")

    #not interested log message
    def log_not_interested(self, peer_id_2):
        logging.info(
            f"[{self._timestamp()}]: Peer {self.peer_id} received the 'not interested' message from [{peer_id_2}].")

    #piece downloaded log message
    def log_piece_downloaded(self, peer_id_2, piece_index, total_pieces):
        logging.info(
            f"[{self._timestamp()}]: Peer {self.peer_id} has downloaded the piece [{piece_index}] "
            f"from Peer {peer_id_2}. Now the number of pieces it has is {total_pieces}."
        )

    #download complete log message
    def log_download_complete(self):
        logging.info(f"[{self._timestamp()}]: Peer {self.peer_id} has downloaded the complete file.")
