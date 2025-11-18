import os

# This handles reading and writing of file pieces to/from peer directories.
class FileManager:
    def __init__(self, peer_id, config):
        self.peer_id = peer_id
        self.peer_dir = f'peer_{peer_id}'
        self.file_name = config.file_name
        self.file_size = config.file_size
        self.piece_size = config.piece_size
        self.num_pieces = config.num_pieces
        self.file_path = os.path.join(self.peer_dir, self.file_name)
        
        # Ensure peer directory exists
        if not os.path.exists(self.peer_dir):
            os.makedirs(self.peer_dir)
    
    # This reads a specific piece from the file.
    def read_piece(self, piece_index):
        if piece_index < 0 or piece_index >= self.num_pieces:
            raise ValueError(f"Invalid piece index: {piece_index}")
        
        # Calculate the size of the piece
        if piece_index == self.num_pieces - 1:  # Last piece
            current_piece_size = self.file_size - (piece_index * self.piece_size)
        else:
            current_piece_size = self.piece_size
        
        # Read the piece
        with open(self.file_path, 'rb') as f:
            f.seek(piece_index * self.piece_size)
            piece_data = f.read(current_piece_size)
        
        if len(piece_data) != current_piece_size:
            raise IOError(f"Failed to read complete piece {piece_index}")
        
        return piece_data
    
    # This writes a specific piece to the file.
    def write_piece(self, piece_index, piece_data):
        if piece_index < 0 or piece_index >= self.num_pieces:
            raise ValueError(f"Invalid piece index: {piece_index}")
        
        # Calculate expected size for this piece
        if piece_index == self.num_pieces - 1:
            expected_size = self.file_size - (piece_index * self.piece_size)
        else:
            expected_size = self.piece_size
        
        if len(piece_data) != expected_size:
            raise ValueError(
                f"Piece {piece_index} has wrong size: {len(piece_data)} != {expected_size}"
            )
        
        # If file doesn't exist, create it with the full size filled with 0s
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'wb') as f:
                f.write(b'\x00' * self.file_size)
        
        # Write the piece at the correct position
        with open(self.file_path, 'r+b') as f:
            f.seek(piece_index * self.piece_size)
            f.write(piece_data)
    
    # This checks if the complete file exists and has correct size.
    def has_complete_file(self):
        if not os.path.exists(self.file_path):
            return False
        
        actual_size = os.path.getsize(self.file_path)
        return actual_size == self.file_size
    
    # This verifies the file exists with all pieces marked in bitfield.
    def create_file_from_pieces(self, bitfield):
        if bitfield.all():
            if not self.has_complete_file():
                raise FileNotFoundError(
                    f"Peer {self.peer_id} marked as having complete file, "
                    f"but {self.file_path} not found or has wrong size"
                )
