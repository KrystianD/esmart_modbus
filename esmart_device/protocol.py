import struct

from esmart_device.crc import calculate_crc

PROTOCOL_STARTING_MARK = 0xaa

ESMART_DEVICE_TYPE = 1

CMD_ACK = 0x00
CMD_GET = 0x01
CMD_SET = 0x02
CMD_SET_NO_RESP = 0x03
CMD_NACK = 0x04
CMD_EXEC = 0x05
CMD_ERR = 0x7f


def build_request(device_addr: int, command_id: int, data_item: int, payload: bytes) -> bytes:
    data = struct.pack("BBBBBB", PROTOCOL_STARTING_MARK, ESMART_DEVICE_TYPE, device_addr, command_id, data_item, len(payload)) + payload
    data += struct.pack("B", calculate_crc(data))
    return data


def build_get_request(*, device_addr: int, data_item: int, data_offset: int, data_length: int) -> bytes:
    return build_request(device_addr, CMD_GET, data_item, struct.pack("BBB", data_offset, 0, data_length))


def build_set_request_word(*, device_addr: int, data_item: int, data_offset: int, value: int) -> bytes:
    return build_request(device_addr, CMD_SET, data_item, struct.pack("BB", data_offset, 0) + struct.pack("<H", value))
