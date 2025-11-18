import logging
from datetime import datetime
import os

class Logger:
    # Initialize logger with a log filename.
    def __init__(self, log_filename):
        if "peer_" in log_filename:
            try:
                self.peer_id = log_filename.split("peer_")[1].split(".")[0]
            except:
                self.peer_id = "unknown"
        else:
            self.peer_id = "unknown"
        
        self.log_path = log_filename
        
        # Create logger instance specific to this file
        self.logger = logging.getLogger(log_filename)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []  # Avoid duplicates
        
        # Create file handler
        handler = logging.FileHandler(self.log_path)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def timestamp(self):
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def log_connection_made(self, peer_id_2):
        """When this peer makes a TCP connection to another peer."""
        message = f"[{self.timestamp()}]: Peer {self.peer_id} makes a connection to Peer {peer_id_2}."
        self.logger.info(message)

    def log_connection_received(self, peer_id_2):
        """When this peer is connected from another peer."""
        message = f"[{self.timestamp()}]: Peer {self.peer_id} is connected from Peer {peer_id_2}."
        self.logger.info(message)

    def log_preferred_neighbors(self, preferred_list):
        """
        When this peer changes preferred neighbors.
        preferred_list: list of peer IDs.
        """
        neighbor_str = ", ".join(map(str, preferred_list))
        message = f"[{self.timestamp()}]: Peer {self.peer_id} has the preferred neighbors [{neighbor_str}]."
        self.logger.info(message)

    #------Choking/Unchoking-------------------
    def log_optimistic_unchoke(self, peer_id_2):
        self.logger.info(
            f"[{self.timestamp()}]: Peer {self.peer_id} has the optimistically unchoked neighbor [{peer_id_2}].")

    #choked log message
    def log_choked(self, peer_id_2):
        self.logger.info(f"[{self.timestamp()}]: Peer {self.peer_id} is choked by Peer {peer_id_2}.")

    #unchoked log message
    def log_unchoked(self, peer_id_2):
        self.logger.info(f"[{self.timestamp()}]: Peer {self.peer_id} is unchoked by Peer {peer_id_2}.")

    #interest log message
    def log_interested(self, peer_id_2):
        self.logger.info(
            f"[{self.timestamp()}]: Peer {self.peer_id} received the 'interested' message from [{peer_id_2}].")

    #not interested log message
    def log_not_interested(self, peer_id_2):
        self.logger.info(
            f"[{self.timestamp()}]: Peer {self.peer_id} received the 'not interested' message from [{peer_id_2}].")

    #piece downloaded log message
    def log_piece_downloaded(self, peer_id_2, piece_index, total_pieces):
        self.logger.info(
            f"[{self.timestamp()}]: Peer {self.peer_id} has downloaded the piece [{piece_index}] "
            f"from Peer {peer_id_2}. Now the number of pieces it has is {total_pieces}."
        )

    #download complete log message
    def log_download_complete(self):
        self.logger.info(f"[{self.timestamp()}]: Peer {self.peer_id} has downloaded the complete file.")
    
    # Log when a HAVE message is received.
    def log_have_received(self, peer_id_2, piece_index):
        self.logger.info(
            f"[{self.timestamp()}]: Peer {self.peer_id} received the 'have' message from "
            f"[{peer_id_2}] for the piece [{piece_index}]."
        )
