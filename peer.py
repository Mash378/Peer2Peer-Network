import socket
import threading
from bitarray import bitarray
from protocol import *

class Peer:
    def __init__(self, host, port, peer_id: int, bitfield: bitarray):
        self.host = host
        self.port = port
        self.peer_id = peer_id
        self.bitfield = bitfield
        self.peers = {}
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
            #Handshake Message
            user_msg = handshake_message(self.peer_id)
            conn.send(user_msg.encode())  #Send handshake message
            data = conn.recv(32)                         #Receive handshake message
            peer_msg = handshake_message.decode(data)

            #Bitfield Message
            user_bitfield_msg = actual_message(BITFIELD, self.bitfield)
            conn.send(user_bitfield_msg.encode())
            data = conn.recv()
            peer_bitfield_msg = actual_message.decode(data)

        except:
            print("Connection Error")
        finally:
            conn.close()        
                    

    