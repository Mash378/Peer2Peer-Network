import socket
import threading
from bitarray import bitarray
from protocol import *
import random

class PeerConnection:
    def __init__(self, conn, peer_id:int, addr):
        self.conn = conn
        self.peer_id = peer_id
        self.addr = addr
        self.interested_in_peer = False
        self.is_interested_in_user = False
        self.is_choked_by_user = False
        self.is_choking_user = False
        self.bitfield = None 

class Peer:
    def __init__(self, host, port, peer_id: int, bitfield: bitarray, k: int, p: int, m: int):
        self.host = host
        self.port = port
        self.peer_id = peer_id
        self.bitfield = bitfield
        self.num_preferred_neighbors = k       # k value
        self.unchoking_interval = p
        self.optimistic_unchoking_interval = m

        self.peers = {}
        self.preferred_neighbors = set()       # Set of preferred neighbors/peer_ids
        self.optimistically_unchoked = None    # Optimistically unchoked neighbor

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #TCP
        print("Socket successfully created")
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  #Number of pending connection requests set to five
        print(f"Peer listening on {self.host}:{self.port}")

    def listen_for_connections(self):
        while True:
            conn, addr = self.server_socket.accept() #Accept and establish TCP connection
            print(f"Accepted connection from {addr}")
            # Start a new thread to handle communication with this peer
            threading.Thread(target=self.handler, args=(conn, addr)).start()
    
    def connect_to_peers(self, peer_host, peer_port):
        #User/client try to connect with other users
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((peer_host, peer_port))
        print(f"Connection sucessful with Peer {peer_host}:{peer_port}")
        threading.Thread(target=self.handler, args=(conn, (peer_host, peer_port))).start()

    def handler(self, conn, addr):
        try:
            #=== Handshake Message ===
            user_msg = handshake_message(self.peer_id)
            conn.sendall(user_msg.encode())  #Send handshake message
            data = conn.recv(32)                         #Receive handshake message
            peer_handshake_msg = handshake_message.decode(data)
            peer_id = peer_handshake_msg.Peer_ID

            peer_conn = PeerConnection(conn, peer_id, addr)     #Connection object
            self.peers[peer_id] = peer_conn
            #=== Bitfield Message ===
            #User sending bitfield message
            if self.bitfield.any():
                bitfield_bytes = self.bitfield.tobytes() #convert bitarray to bytes
                user_bitfield_msg = actual_message(BITFIELD, bitfield_bytes)
                conn.sendall(user_bitfield_msg.encode())
            #User receiving bitfield message    
            data = conn.recv(7)
            peer_bitfield_msg = actual_message.decode(data)

            if peer_bitfield_msg.message_payload:
                #Check for interesting pieces
                isInterested = False
                peer_bitfield = bitarray()
                peer_bitfield.frombytes(peer_bitfield_msg.message_payload)  
                peer_conn.bitfield = peer_bitfield
                for i in range(len(peer_bitfield)):
                    if peer_bitfield[i] and not self.bitfield[i]:
                        isInterested = True

                #=== Interest message ====
                if isInterested:
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
                not_interested_msg = actual_message(NOT_INTERESTED)
                conn.sendall(not_interested_msg.encode())
                print(f"NOT INTERESTED msg sent to peer {peer_id} (empty bitfield)")

            #To do: continuing receiving and handling messages from peer
            while True:
                try:
                    msg_length = conn.recv(4)
                    msg_length = struct.unpack(">I", msg_length)[0]
                    msg_type = conn.recv(1)
                    msg_type = struct.unpack("B", msg_type[0])
                    msg_payload = conn.recv(msg_length-1)
                    match msg_type:
                        case 0:
                            peer_conn.is_choked_by_user = True
                        case 1:
                            peer_conn.is_choked_by_user = False
                        case 2:
                            peer_conn.is_interested_in_user = True
                        case 3:
                            peer_conn.is_interested_in_user = False
                        case 4:
                            piece_index = struct.unpack(">I", msg_payload)[0]   #the piece peer contains
                            if peer_conn.bitfield:
                                peer_conn.bitfield[piece_index] = True                  #User now has the piece
                        case 6:
                            piece_index = struct.unpack(">I", msg_payload)[0]
                            if not peer_conn.is_choked_by_user:
                                content = ""                                     #TODO load content data from somewhere
                                payload = msg_payload[0:4] + content
                                user_piece_msg = actual_message(PIECE, payload)
                                conn.sendall(user_piece_msg.encode())

                except Exception as e:
                    print(f"Unexpected error with {addr}: {e}")

        except ConnectionError as e:
            print(f"Connection error with {addr}: {e}")
        except struct.error as e:
            print(f"Protocol error with {addr}: {e}")
        except ValueError as e:
            print(f"Message decoding error with {addr}: {e}")
        except Exception as e:
            print(f"Unexpected error with {addr}: {e}")
        finally:
            conn.close()        
                    

    