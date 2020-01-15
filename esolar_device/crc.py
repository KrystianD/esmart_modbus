from typing import Union, List


def calculate_crc(data: Union[bytes, List[int]]) -> int:
    chk = 0
    for c in data:
        chk += c
    chk = chk & 0xff
    if chk == 0:
        return 0
    chk = 255 - chk + 1
    return chk


def verify_crc(header_data: bytes, payload_data: bytes, packet_crc: int) -> bool:
    return packet_crc == calculate_crc([*header_data, *payload_data])
