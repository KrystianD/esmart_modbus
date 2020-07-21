from typing import Union, List


def calculate_crc(data: Union[bytes, List[int]]) -> int:
    return -sum(data) & 0xff


def verify_crc(header_data: bytes, payload_data: bytes, packet_crc: int) -> bool:
    return packet_crc == calculate_crc([*header_data, *payload_data])
