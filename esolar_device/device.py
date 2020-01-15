import serial
import logging
from typing import Union, Sequence

from esolar_device.crc import verify_crc
from esolar_device.exceptions import CommandNotAcknowledgedException, ChecksumException, InvalidCommandException, ReadTimeoutException
from esolar_device.protocol import build_set_request_word, build_get_request, CMD_NACK, CMD_ERR
from esolar_device.types import ResponseHeader


def read_all(ser: serial.Serial, len_to_read: int) -> bytes:
    buffer = b""
    while len(buffer) < len_to_read:
        cur_read = ser.read(len_to_read - len(buffer))
        if len(cur_read) == 0:
            raise ReadTimeoutException()
        buffer += cur_read
    return buffer


def bytes_to_str(data: Union[bytes, Sequence[int]]) -> str:
    return ','.join(f'{x:02x}' for x in data)


class ESolarSerialDevice:
    def __init__(self, path: str, *, device_addr: int) -> None:
        self.ser = serial.Serial(path, 9600, timeout=0.1)
        self.device_addr = device_addr

    def close(self) -> None:
        self.ser.close()

    def set_word(self, *, data_item: int, data_offset: int, value: int) -> bytes:
        req_data = build_set_request_word(device_addr=self.device_addr, data_item=data_item, data_offset=data_offset, value=value)
        return self._send_request_for_response(req_data)

    def get(self, *, data_item: int, data_offset: int, data_length: int) -> bytes:
        req_data = build_get_request(device_addr=self.device_addr, data_item=data_item, data_offset=data_offset, data_length=data_length)
        return self._send_request_for_response(req_data)[2:]

    def _send_request_for_response(self, request_data: bytes) -> bytes:
        self.ser.write(request_data)

        logging.debug(f"Sending request: {bytes_to_str(request_data)}")

        payload = self._read_response()

        return payload

    def _read_response(self) -> bytes:
        header_bytes = read_all(self.ser, ResponseHeader.packet_size())

        header = ResponseHeader.parse(header_bytes)

        if header.cmd == CMD_NACK:
            raise CommandNotAcknowledgedException()
        if header.cmd == CMD_ERR:
            raise InvalidCommandException()

        payload_with_crc = read_all(self.ser, header.length + 1)
        payload = payload_with_crc[:-1]
        crc = payload_with_crc[-1]

        logging.debug(f"Got response: {bytes_to_str(header_bytes)} / {bytes_to_str(payload)} / {bytes_to_str([crc])}")

        if not verify_crc(header_bytes, payload, crc):
            raise ChecksumException()

        return payload
