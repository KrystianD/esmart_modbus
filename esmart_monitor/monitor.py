import datetime
import enum
import logging
import queue
import struct
import threading
import time
import traceback
import itertools
from threading import Event
from typing import Optional, Any, Tuple, cast, Dict, List

from esmart_device.device import ESmartSerialDevice
from esmart_device.exceptions import ReadTimeoutException
from esmart_device.registers import ESmartRegister, get_register, esmart_registers


class RequestFailedException(Exception):
    pass


ValueHoldTime = datetime.timedelta(seconds=2)
UpdateInterval = datetime.timedelta(seconds=1)
StaleValueTime = datetime.timedelta(seconds=10)


class Command:
    def __init__(self, register: ESmartRegister, value: Any):
        self.event = Event()
        self.register = register
        self.value = value
        self.success = False
        self.event = threading.Event()

    def __str__(self) -> str:
        return f"{self.register.name} -> {self.value}"


class ESmartMonitor:
    def __init__(self, path: str, device_addr: int):
        self._dev: Optional[ESmartSerialDevice] = None
        self._path = path
        self._device_addr = device_addr
        self._state_last_update: Optional[datetime.datetime] = None

        self._commands_queue: queue.Queue[Command] = queue.Queue()

        self._values: List[Tuple[ESmartRegister, Any]] = []

        self._pending_updates: Dict[ESmartRegister, Tuple[float, int]] = {}

        self._update_lock = threading.Lock()

    def _execute_commands(self) -> None:
        while True:
            try:
                cmd = self._commands_queue.get_nowait()
                self._execute_command_retry(cmd)
            except queue.Empty:
                break

    def _execute_command_retry(self, cmd: Command) -> None:
        if self._dev is None:
            raise Exception("device not initialized")

        logging.info(f"Executing command [{cmd}]")

        for i in range(5):
            try:
                self._dev.set_word(data_item=cmd.register.data_item, data_offset=cmd.register.esmart_address, value=cast(int, cmd.value))
                cmd.success = True
                cmd.event.set()
                logging.info(f"Command [{cmd}] completed")
                self._pending_updates[cmd.register] = (time.time() + ValueHoldTime.total_seconds(), cmd.value)
                time.sleep(0.2)
                return
            except ReadTimeoutException:
                logging.info(f"Command [{cmd}] timed out, retrying")
                time.sleep(0.2)

        cmd.event.set()
        logging.info(f"Command [{cmd}] failed")

    def run(self) -> None:
        while True:
            try:
                logging.info("Creating new serial port connection")
                self._dev = ESmartSerialDevice(self._path, device_addr=self._device_addr)
                while True:
                    try:
                        new_values = []
                        for data_item, regs_for_item_it in itertools.groupby(esmart_registers, lambda x: x.data_item):
                            regs_for_item: List[ESmartRegister] = list(regs_for_item_it)
                            addr_min = min(x.esmart_address for x in regs_for_item)
                            addr_max = max(x.esmart_address + (x.data_size // 2) for x in regs_for_item)

                            self._execute_commands()

                            d = self._dev.get(data_item=data_item, data_offset=addr_min, data_length=(addr_max - addr_min) * 2)
                            time.sleep(0.2)

                            for reg in regs_for_item:
                                reg_data = reg.process_raw(struct.unpack_from(reg.data_format, d, (reg.esmart_address - addr_min) * 2)[0])

                                new_values.append((reg, reg_data))

                        with self._update_lock:
                            self._values = new_values
                            self._state_last_update = datetime.datetime.utcnow()

                        for reg, val in new_values:
                            logging.debug(f"{reg.name} {reg.to_modbus(val)}")

                    except KeyboardInterrupt:
                        break
                    except ReadTimeoutException:
                        logging.error("Read timeout exception")
                        time.sleep(UpdateInterval.total_seconds())
            except KeyboardInterrupt:
                break
            except:
                traceback.print_exc()
                time.sleep(UpdateInterval.total_seconds())
            finally:
                if self._dev is not None:
                    self._dev.close()

    def get_values(self) -> Optional[List[Tuple[ESmartRegister, Any]]]:
        with self._update_lock:
            if self._state_last_update is None or \
                    datetime.datetime.utcnow() - self._state_last_update > StaleValueTime:
                return None
            else:
                merged_values = self._values
                for i, (reg, _) in enumerate(list(merged_values)):
                    if reg in self._pending_updates:
                        v = self._pending_updates[reg]
                        if time.time() < v[0]:
                            merged_values[i] = (reg, v[1])

                return merged_values

    def set_word(self, *, data_item: int, data_offset: int, value: int) -> None:
        reg = get_register(data_item, data_offset)

        cmd = Command(reg, value)
        with self._update_lock:
            self._commands_queue.put(cmd)
        cmd.event.wait()
        if not cmd.success:
            raise RequestFailedException()
