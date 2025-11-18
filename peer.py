import socket
import threading
import time
import struct
from bitarray import bitarray
from protocol import *
from file_manager import FileManager
import random

class PeerConnection:
    def __init__(self, conn, peer_id: int, addr):
        self.conn = conn
        self.peer_id = peer_id
        self.addr = addr
        self.interested_in_peer = False
        self.is_interested_in_user = False
        self.is_choked_by_user = True
        self.is_choking_user = True
        self.bitfield = None
        
        self.bytes_downloaded = 0
        self.download_start_time = time.time()
        self.requested_pieces = set()
        self.lock = threading.Lock()
    
    # This calculates download rate in bytes per second.
    def get_download_rate(self):
        elapsed = time.time() - self.download_start_time
        if elapsed == 0:
            return 0
        return self.bytes_downloaded / elapsed
    
    # This resets the tracking for download rate.
    def reset_download_rate(self):
        self.bytes_downloaded = 0
        self.download_start_time = time.time()

class Peer:
    def __init__(self, host, port, peer_id: int, bitfield: bitarray, k: int, p: int, m: int, logger, config, peer_info):
        self.host = host
        self.port = port
        self.peer_id = peer_id
        self.bitfield = bitfield
        self.num_preferred_neighbors = k
        self.unchoking_interval = p
        self.optimistic_unchoking_interval = m
        self.logger = logger
        self.config = config
        self.peer_info = peer_info

        self.peers = {}
        self.peers_lock = threading.Lock()
        self.preferred_neighbors = set()
        self.optimistically_unchoked = None
        
        # File manager
        self.file_manager = FileManager(peer_id, config)
        
        # Verify file exists if we're supposed to have it.
        if bitfield.all():
            self.file_manager.create_file_from_pieces(bitfield)
        
        # Termination tracking
        self.running = True
        self.all_done = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket successfully created")
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Number of pending reqs set to 5
        print(f"Peer {self.peer_id} listening on {self.host}:{self.port}")

    # This accepts incoming connections.
    def listen_for_connections(self):
        while self.running:
            conn, addr = self.server_socket.accept() # Accept and establish TCP connection
            print(f"Accepted connection from {addr}")
            self.logger.log_connection_received("unknown")
            # Start a new thread to handle communication with this peer
            threading.Thread(target=self.handler, args=(conn, addr), daemon=True).start()
    
    # This lets the user/client try to connect with other users.
    def connect_to_peers(self, peer_host, peer_port):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((peer_host, peer_port))
        print(f"Connection successful with Peer at {peer_host}:{peer_port}")
        threading.Thread(target=self.handler, args=(conn, (peer_host, peer_port)), daemon=True).start()

    # This handles communication with a peer.
    def handler(self, conn, addr):
        peer_id = None
        try:
            # === Handshake Message ===
            user_msg = handshake_message(self.peer_id)
            conn.sendall(user_msg.encode())  # Send handshake message
            data = conn.recv(32)  # Receive handshake message
            peer_handshake_msg = handshake_message.decode(data)
            peer_id = peer_handshake_msg.Peer_ID
            
            print(f"Handshake complete with peer {peer_id}")
            self.logger.log_connection_made(peer_id)

            peer_conn = PeerConnection(conn, peer_id, addr)  # Connection object
            self.peers[peer_id] = peer_conn
            
            # === Bitfield Message ===
            # User sending bitfield message
            bitfield_bytes = self.bitfield.tobytes()  # Convert bitarray to bytes
            user_bitfield_msg = actual_message(BITFIELD, bitfield_bytes)
            conn.sendall(user_bitfield_msg.encode())
            
            # User receiving bitfield message
            bitfield_data = self._recv_exact(conn, 5)  # Min header size
            bitfield_length = struct.unpack(">I", bitfield_data[:4])[0]
            if bitfield_length > 1:
                remaining = bitfield_length - 1
                bitfield_data += self._recv_exact(conn, remaining)
            peer_bitfield_msg = actual_message.decode(bitfield_data)

            if peer_bitfield_msg.message_payload:
                # Check for interesting pieces
                peer_bitfield = bitarray()
                peer_bitfield.frombytes(peer_bitfield_msg.message_payload)
                peer_conn.bitfield = peer_bitfield
                is_interested = self._has_interesting_pieces(peer_bitfield)
                
                # === Interest message ===
                if is_interested:
                    interested_msg = actual_message(INTERESTED)
                    conn.sendall(interested_msg.encode())
                    peer_conn.interested_in_peer = True
                    print(f"INTEREST msg sent to peer {peer_id}")
                else:
                    not_interested_msg = actual_message(NOT_INTERESTED)
                    conn.sendall(not_interested_msg.encode())
                    print(f"NOT INTERESTED msg to peer {peer_id}")
            else:
                # Peer has no pieces
                peer_conn.bitfield = bitarray(self.config.num_pieces)
                peer_conn.bitfield.setall(0)
                not_interested_msg = actual_message(NOT_INTERESTED)
                conn.sendall(not_interested_msg.encode())
                print(f"NOT INTERESTED msg sent to peer {peer_id} (empty bitfield)")

            # === Message Loop ===
            while self.running:
                try:
                    # Receive the message header.
                    header = self._recv_exact(conn, 5)
                    if not header:
                        break
                    
                    msg_length = struct.unpack(">I", header[:4])[0]
                    msg_type = header[4]
                    
                    # Receive the payload if any.
                    if msg_length > 1:
                        msg_payload = self._recv_exact(conn, msg_length - 1)
                    else:
                        msg_payload = b''
                    
                    self._handle_message(peer_conn, msg_type, msg_payload)
                    
                except Exception as e:
                    print(f"Error in message loop with peer {peer_id}: {e}")
                    break

        except ConnectionError as e:
            print(f"Connection error with {addr}: {e}")
        except Exception as e:
            print(f"Unexpected error with {addr}: {e}")
        finally:
            if peer_id:
                with self.peers_lock:
                    if peer_id in self.peers:
                        del self.peers[peer_id]
            conn.close()
            print(f"Connection closed with peer {peer_id}")
    
    # Receive exactly num_bytes from connection.
    def _recv_exact(self, conn, num_bytes):
        data = b''
        while len(data) < num_bytes:
            chunk = conn.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    # Check if peer has any pieces we're missing.
    def _has_interesting_pieces(self, peer_bitfield):
        for i in range(min(len(peer_bitfield), len(self.bitfield))):
            if peer_bitfield[i] and not self.bitfield[i]:
                return True
        return False
    
    # Handle different message types.
    def _handle_message(self, peer_conn, msg_type, msg_payload):
        if msg_type == CHOKE:
            peer_conn.is_choking_user = True
            self.logger.log_choked(peer_conn.peer_id)
            print(f"Choked by peer {peer_conn.peer_id}")
            
        # Send a request for a piece.
        elif msg_type == UNCHOKE:
            peer_conn.is_choking_user = False
            self.logger.log_unchoked(peer_conn.peer_id)
            print(f"Unchoked by peer {peer_conn.peer_id}")
            self._send_request(peer_conn)
            
        elif msg_type == INTERESTED:
            peer_conn.is_interested_in_user = True
            self.logger.log_interested(peer_conn.peer_id)
            print(f"Peer {peer_conn.peer_id} is interested")
            
        elif msg_type == NOT_INTERESTED:
            peer_conn.is_interested_in_user = False
            self.logger.log_not_interested(peer_conn.peer_id)
            print(f"Peer {peer_conn.peer_id} is not interested")
            
        elif msg_type == HAVE:
            piece_index = struct.unpack(">I", msg_payload)[0]
            if peer_conn.bitfield:
                peer_conn.bitfield[piece_index] = True
            self.logger.log_have_received(peer_conn.peer_id, piece_index)
            print(f"Peer {peer_conn.peer_id} has piece {piece_index}")
            
            # Check if we're now interested.
            if not peer_conn.interested_in_peer and not self.bitfield[piece_index]:
                interested_msg = actual_message(INTERESTED)
                peer_conn.conn.sendall(interested_msg.encode())
                peer_conn.interested_in_peer = True
                print(f"Now interested in peer {peer_conn.peer_id}")
            
        elif msg_type == REQUEST:
            piece_index = struct.unpack(">I", msg_payload)[0]
            print(f"Received REQUEST for piece {piece_index} from peer {peer_conn.peer_id}")
            
            # Send piece if not choked.
            if not peer_conn.is_choked_by_user and self.bitfield[piece_index]:
                self._send_piece(peer_conn, piece_index)
            else:
                print(f"Cannot send piece {piece_index}: choked={peer_conn.is_choked_by_user}, have={self.bitfield[piece_index]}")
            
        elif msg_type == PIECE:
            piece_index = struct.unpack(">I", msg_payload[:4])[0]
            piece_data = msg_payload[4:]
            print(f"Received PIECE {piece_index} from peer {peer_conn.peer_id} ({len(piece_data)} bytes)")
            
            # Save the piece.
            try:
                self.file_manager.write_piece(piece_index, piece_data)
                self.bitfield[piece_index] = True
                
                # Update the download stats.
                peer_conn.bytes_downloaded += len(piece_data)
                if piece_index in peer_conn.requested_pieces:
                    peer_conn.requested_pieces.remove(piece_index)
                
                num_pieces = self.bitfield.count()
                self.logger.log_piece_downloaded(peer_conn.peer_id, piece_index, num_pieces)
                print(f"Saved piece {piece_index}. Now have {num_pieces}/{self.config.num_pieces} pieces")
                
                # Broadcast HAVE to all other peers.
                self._broadcast_have(piece_index)
                
                # Check if we're done.
                if self.bitfield.all():
                    self.logger.log_download_complete()
                    print(f"Peer {self.peer_id} has downloaded the complete file")
                    self._check_all_done()
                else:
                    # Check if still interested in this peer.
                    if not self._has_interesting_pieces(peer_conn.bitfield):
                        not_interested_msg = actual_message(NOT_INTERESTED)
                        peer_conn.conn.sendall(not_interested_msg.encode())
                        peer_conn.interested_in_peer = False
                        print(f"No longer interested in peer {peer_conn.peer_id}")
                
                # Request next piece if not choked.
                if not peer_conn.is_choking_user:
                    self._send_request(peer_conn)
                    
            except Exception as e:
                print(f"Error saving piece {piece_index}: {e}")
    
    # Send a request for a piece to peer.
    def _send_request(self, peer_conn):
        # Find a piece we need that peer has and we haven't requested yet.
        available_pieces = []
        for i in range(len(self.bitfield)):
            if (peer_conn.bitfield[i] and 
                not self.bitfield[i] and 
                i not in peer_conn.requested_pieces):
                available_pieces.append(i)
        
        if available_pieces:
            # Random selection
            piece_index = random.choice(available_pieces)
            peer_conn.requested_pieces.add(piece_index)
            
            payload = struct.pack(">I", piece_index)
            request_msg = actual_message(REQUEST, payload)
            peer_conn.conn.sendall(request_msg.encode())
            print(f"Sent REQUEST for piece {piece_index} to peer {peer_conn.peer_id}")
    
    # Send a piece to peer.
    def _send_piece(self, peer_conn, piece_index):
        try:
            piece_data = self.file_manager.read_piece(piece_index)
            payload = struct.pack(">I", piece_index) + piece_data
            piece_msg = actual_message(PIECE, payload)
            peer_conn.conn.sendall(piece_msg.encode())
            print(f"Sent PIECE {piece_index} to peer {peer_conn.peer_id} ({len(piece_data)} bytes)")
        except Exception as e:
            print(f"Error sending piece {piece_index}: {e}")
    
    # Broadcast HAVE message to all peers.
    def _broadcast_have(self, piece_index):
        payload = struct.pack(">I", piece_index)
        have_msg = actual_message(HAVE, payload)
        
        with self.peers_lock:
            for peer_id, peer_conn in self.peers.items():
                try:
                    peer_conn.conn.sendall(have_msg.encode())
                except Exception as e:
                    print(f"Error sending HAVE to peer {peer_id}: {e}")
    
    # Start periodic unchoking threads.
    def start_unchoking_intervals(self):
        # Preferred neighbors selection
        def preferred_neighbor_timer():
            while self.running:
                time.sleep(self.unchoking_interval)
                self._select_preferred_neighbors()
        
        # Optimistic unchoking
        def optimistic_unchoking_timer():
            while self.running:
                time.sleep(self.optimistic_unchoking_interval)
                self._select_optimistic_unchoke()
        
        threading.Thread(target=preferred_neighbor_timer, daemon=True).start()
        threading.Thread(target=optimistic_unchoking_timer, daemon=True).start()
        print(f"Started unchoking intervals: preferred={self.unchoking_interval}s, optimistic={self.optimistic_unchoking_interval}s")
    
    # Select k preferred neighbors based on download rate or randomly.
    def _select_preferred_neighbors(self):
        with self.peers_lock:
            interested_peers = [
                (peer_id, peer_conn) 
                for peer_id, peer_conn in self.peers.items() 
                if peer_conn.is_interested_in_user
            ]
        
        if not interested_peers:
            return
        
        # If we have complete file, select randomly
        if self.bitfield.all():
            selected = random.sample(interested_peers, min(self.num_preferred_neighbors, len(interested_peers)))
            new_preferred = set(peer_id for peer_id, _ in selected)
        else:
            # Select based on download rate
            interested_peers.sort(key=lambda x: x[1].get_download_rate(), reverse=True)
            selected = interested_peers[:self.num_preferred_neighbors]
            new_preferred = set(peer_id for peer_id, _ in selected)
        
        # Update preferred neighbors
        old_preferred = self.preferred_neighbors
        self.preferred_neighbors = new_preferred
        
        if new_preferred != self.preferred_neighbors:
            self.logger.log_preferred_neighbors(list(new_preferred))
            print(f"Preferred neighbors: {new_preferred}")
        
        # Unchoke new preferred neighbors
        for peer_id in new_preferred:
            if peer_id in self.peers:
                peer_conn = self.peers[peer_id]
                if peer_conn.is_choked_by_user:
                    unchoke_msg = actual_message(UNCHOKE)
                    peer_conn.conn.sendall(unchoke_msg.encode())
                    peer_conn.is_choked_by_user = False
                    print(f"Unchoked preferred neighbor {peer_id}")
        
        # Choke peers no longer preferred (except optimistic)
        for peer_id in old_preferred - new_preferred:
            if peer_id != self.optimistically_unchoked and peer_id in self.peers:
                peer_conn = self.peers[peer_id]
                if not peer_conn.is_choked_by_user:
                    choke_msg = actual_message(CHOKE)
                    peer_conn.conn.sendall(choke_msg.encode())
                    peer_conn.is_choked_by_user = True
                    print(f"Choked peer {peer_id}")
        
        # Reset download rates
        for peer_id, peer_conn in self.peers.items():
            peer_conn.reset_download_rate()
    
    # Select one optimistically unchoked neighbor randomly.
    def _select_optimistic_unchoke(self):
        with self.peers_lock:
            # Get choked peers that are interested
            candidates = [
                peer_id 
                for peer_id, peer_conn in self.peers.items() 
                if peer_conn.is_choked_by_user and peer_conn.is_interested_in_user
            ]
        
        if not candidates:
            return
        
        # Select randomly
        old_optimistic = self.optimistically_unchoked
        new_optimistic = random.choice(candidates)
        self.optimistically_unchoked = new_optimistic
        
        self.logger.log_optimistic_unchoke(new_optimistic)
        print(f"Optimistically unchoked neighbor: {new_optimistic}")
        
        # Unchoke the new one
        if new_optimistic in self.peers:
            peer_conn = self.peers[new_optimistic]
            unchoke_msg = actual_message(UNCHOKE)
            peer_conn.conn.sendall(unchoke_msg.encode())
            peer_conn.is_choked_by_user = False
            print(f"Unchoked optimistic neighbor {new_optimistic}")
        
        # Choke the old one if not preferred
        if old_optimistic and old_optimistic != new_optimistic and old_optimistic not in self.preferred_neighbors:
            if old_optimistic in self.peers:
                peer_conn = self.peers[old_optimistic]
                if not peer_conn.is_choked_by_user:
                    choke_msg = actual_message(CHOKE)
                    peer_conn.conn.sendall(choke_msg.encode())
                    peer_conn.is_choked_by_user = True
                    print(f"Choked old optimistic neighbor {old_optimistic}")
    
    # Check if this peer should terminate.
    def should_terminate(self):
        return self.all_done
    
    # Check if all peers have complete file.
    def _check_all_done(self):
        with self.peers_lock:
            if not self.bitfield.all():
                return False
            
            for peer_conn in self.peers.values():
                if not (peer_conn.bitfield and peer_conn.bitfield.all()):
                    return False
        
        self.all_done = True
        print(f"All peers have complete file")
    
    # Clean shutdown of peer.
    def shutdown(self):
        print(f"Peer {self.peer_id} shutting down")
        self.running = False
        
        # Close all peer connections
        with self.peers_lock:
            for peer_conn in self.peers.values():
                try:
                    peer_conn.conn.close()
                except:
                    pass
        
        # Close server socket
        try:
            self.server_socket.close()
        except:
            pass
        
        print(f"Peer {self.peer_id} shutdown complete")
