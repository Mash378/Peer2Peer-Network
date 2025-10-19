import struct

CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7

class handshake_message:
    header = b'P2PFILESHARINGPROJ'
    zero_bits = b'\x00' * 10

    def __init__(self, peer_id: int ):
        self.Peer_ID = peer_id

    def encode(self):
        return self.header + self.zero_bits + struct.pack('>I', self.Peer_ID)
    @classmethod
    def decode(cls, data: bytes):
        if len(data) != 32:
            raise ValueError("Incorrect handshake message")
        
        header = data[:18]
        zeros = data[18:28]
        peer_id = struct.unpack('>I', data[28:])[0]

        if header != cls.header:
            raise ValueError("Invalid handshake header")
        if zeros != cls.zero_bits:
            raise ValueError("Invalid zero bits section")

        return (cls(peer_id))
    
    def __repr__(self):
        return f"HandshakeMessage peer_id={self.Peer_ID}"


class actual_message:
    def __init__(self, message_type: int, message_payload):
        self.message_length = len(message_payload) + 1
        self.message_type = message_type
        self.message_payload = message_payload
    
    def encode(self):
        return struct.pack(">I", self.message_length) + struct.pack("B", self.message_type) + struct.pack(self.message_payload)
    @classmethod
    def decode(cls, data: bytes):
        if len(data) < 5:
            raise ValueError("Incomplete message header")
        
        message_length = struct.unpack(">I", data[:4])[0]
        message_type = data[4]
        message_payload = data[5:5 + (message_length - 1)]

        if len(message_payload) != (message_length - 1):
            raise ValueError("Incomplete payload")

        return cls(message_type, message_payload)
    
    def __repr__(self):
        return f"ActualMessage type={self.message_type} length={self.message_length}"