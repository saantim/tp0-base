"""
Message parsing and serialization module for the server.

This module handles the binary protocol for client-server communication.
"""

from . import utils

class MessageParser:
    """Base class for parsing binary messages with a type header.
    """
    BET_MSG_TYPE = 1
    ACK_MSG_TYPE = 2
    BET_BATCH_MSG_TYPE = 3
    HEADER_SIZE = 2

    def __init__(self, header: bytes, data: bytes):
        self.header = header
        self.data = data
        self.offset = 0

    def read_uint8(self) -> int:
        value = self.data[self.offset]
        self.offset += 1
        return value

    def read_uint32(self) -> int:
        value = int.from_bytes(self.data[self.offset:self.offset+4], 'big')
        self.offset += 4
        return value

    def read_string(self, length: int) -> str:
        string_bytes = self.data[self.offset:self.offset+length]
        self.offset += length
        return string_bytes.decode('utf-8').rstrip('\x00')

    def parse(self):
        msg_type = self.header[0]
        if msg_type == MessageParser.BET_MSG_TYPE:
            return [BetParser(self.header, self.data, self.offset).parse()]
        if msg_type == MessageParser.BET_BATCH_MSG_TYPE:
            return BetBatchParser(self.header, self.data, self.offset).parse()

        raise ValueError("Invalid message type")

    @classmethod
    def expected_bytes(cls, header: bytes) -> int:
        msg_type = header[0]
        if msg_type == MessageParser.BET_MSG_TYPE:
            return BetParser.PAYLOAD_SIZE
        if msg_type == MessageParser.BET_BATCH_MSG_TYPE:
            required_bytes = BetParser.PAYLOAD_SIZE * header[1]
            return required_bytes
        return 0

class BetParser(MessageParser):
    """Parser for bet messages.
    """
    NAME_LENGTH = 32
    BIRTH_DAY_LENGTH = 10
    PAYLOAD_SIZE = 83

    def __init__(self, header: bytes, data: bytes, offset: int = 0):
        super().__init__(header, data)
        self.offset = offset

    def parse(self) -> utils.Bet:
        agency=self.read_uint8()
        bet_id=self.read_uint32()
        first_name=self.read_string(self.NAME_LENGTH)
        last_name=self.read_string(self.NAME_LENGTH)
        birth_day=self.read_string(self.BIRTH_DAY_LENGTH)
        bet_num=self.read_uint32()

        return utils.Bet(
            str(agency),
            first_name,
            last_name,
            str(bet_id),
            birth_day,
            str(bet_num)
        )

class BetBatchParser(MessageParser):
    """Parser for bet batch messages."""

    def __init__(self, header: bytes, data: bytes, offset: int = 0):
        super().__init__(header, data)
        self.offset = offset
        self.batch_size = header[1]

    def parse(self) -> list[utils.Bet]:
        bets = []
        for _ in range(self.batch_size):
            bet_parser = BetParser(self.header, self.data, self.offset)
            bets.append(bet_parser.parse())
            self.offset = bet_parser.offset
        return bets

class AckMsg:
    """ACK message.
    
    Attributes:
        success (bool)
    """

    def __init__(self, success: bool):
        self.success = success

    def to_bytes(self) -> bytes:
        return bytes([MessageParser.ACK_MSG_TYPE, 0, int(self.success)])