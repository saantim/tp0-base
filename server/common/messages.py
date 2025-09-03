from . import utils

class MessageParser:
    BET_MSG_TYPE = 1
    ACK_MSG_TYPE = 2
    HEADER_SIZE = 1

    def __init__(self, data: bytes):
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
        if self.read_uint8() == BET_MSG_TYPE:
            return BetParser(self.data, self.offset).parse_bet()
        raise ValueError("Invalid message type")

    @classmethod
    def expected_bytes(self, header: bytes) -> int:
        if header[0] == self.BET_MSG_TYPE:
            return BetParser.PAYLOAD_SIZE
        return 0

class BetParser(MessageParser):
    NAME_LENGTH = 32
    BIRTH_DAY_LENGTH = 10
    PAYLOAD_SIZE = 83

    def __init__(self, data: bytes, offset: int = 0):
        super().__init__(data)
        self.offset = offset

    def parse_bet(self) -> utils.Bet:
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


class AckMsg:

    def __init__(self, success: bool):
        self.success = success

    def to_bytes(self) -> bytes:
        return bytes([ACK_MSG_TYPE, int(self.success)])