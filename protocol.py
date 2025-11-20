import struct

CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7

VALID_MESSAGE_TYPES = {
    CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED,
    HAVE, BITFIELD, REQUEST, PIECE
}

class handshake_message:
    header = b'P2PFILESHARINGPROJ'
    zero_bits = b'\x00' * 10

    def __init__(self, peer_id: int):
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


        return cls(peer_id)

    def __repr__(self):
        return f"HandshakeMessage peer_id={self.Peer_ID}"


class actual_message:
    def __init__(self, message_type: int, message_payload: bytes = b''):
        if message_type not in VALID_MESSAGE_TYPES:
            raise ValueError(f"Invalid message type: {message_type}")

        self.message_type = message_type
        self.message_payload = message_payload
        self.message_length = len(message_payload) + 1  # includes type byte

    def encode(self):
        return (
            struct.pack(">I", self.message_length) +
            struct.pack("B", self.message_type) +
            self.message_payload
        )

    @classmethod
    def decode(cls, data: bytes):
        if len(data) < 5:
            raise ValueError("Incomplete message header")

        message_length = struct.unpack(">I", data[:4])[0]
        message_type = data[4]

        if message_type not in VALID_MESSAGE_TYPES:
            raise ValueError(f"Invalid message type: {message_type}")

        expected_total = 4 + message_length
        if len(data) != expected_total:
            raise ValueError("Message length mismatch")

        payload_len = message_length - 1
        payload = data[5:5 + payload_len]

        if len(payload) != payload_len:
            raise ValueError("Incomplete payload")

        # Messages with no payload must have length 1
        if message_type in (CHOKE, UNCHOKE, INTERESTED, NOT_INTERESTED):
            if message_length != 1:
                raise ValueError("Invalid length for no-payload message")

        return cls(message_type, payload)

    def __repr__(self):
        return f"ActualMessage type={self.message_type} length={self.message_length}"
