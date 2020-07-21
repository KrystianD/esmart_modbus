import struct
from dataclasses import dataclass

from esmart_device.protocol import PROTOCOL_STARTING_MARK


@dataclass
class ResponseHeader:
    FMT = "<BBBBBB"

    cmd: int
    data_item: int
    length: int

    @staticmethod
    def parse(data: bytes) -> 'ResponseHeader':
        (mark, device_type, device_addr, cmd, data_item, length) = struct.unpack(ResponseHeader.FMT, data)
        assert mark == PROTOCOL_STARTING_MARK
        return ResponseHeader(cmd, data_item, length)

    @staticmethod
    def packet_size() -> int:
        return struct.calcsize(ResponseHeader.FMT)
