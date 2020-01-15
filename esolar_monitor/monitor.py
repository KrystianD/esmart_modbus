import datetime
import logging
import queue
import struct
import time
import traceback
import itertools
from typing import Optional, Any, Tuple, cast, Dict, List

from esolar_device.device import ESolarSerialDevice
from esolar_device.exceptions import ReadTimeoutException
from esolar_monitor.registers import regs, ESolarRegister, get_register
from esolar_monitor.types import ESolarState, ESolarConfig

TCommandEntry = Tuple[ESolarRegister, Any]


class ESolarMonitor:
    def __init__(self, path: str):
        self._dev: Optional[ESolarSerialDevice] = None
        self._path = path
        self._state: Optional[ESolarState] = None
        self._config: Optional[ESolarConfig] = None
        self._state_last_update: Optional[datetime.datetime] = None

        self._commands_queue: queue.Queue[TCommandEntry] = queue.Queue()

        self._values: List[Tuple[ESolarRegister, Any]] = []

        self._pending_updates: Dict[ESolarRegister, Any] = {}

    def _get_unpack(self, *, data_item: int, data_offset: int, data_format: str) -> Tuple[Any, ...]:
        if self._dev is None:
            raise Exception("device not initialized")
        data = self._dev.get(data_item=data_item, data_offset=data_offset, data_length=struct.calcsize(data_format))
        time.sleep(0.5)
        return struct.unpack(data_format, data)

    def _execute_commands(self) -> None:
        while True:
            try:
                cmd = self._commands_queue.get_nowait()
                self._execute_command_retry(cmd)
            except queue.Empty:
                break

    def _execute_command_retry(self, cmd: TCommandEntry) -> None:
        logging.info(f"Executing command: {cmd}")
        reg, value = cmd

        if self._dev is None:
            raise Exception("device not initialized")

        for i in range(5):
            try:
                self._dev.set_word(data_item=reg.data_item, data_offset=reg.esolar_address, value=cast(int, value))
                time.sleep(0.2)
                break
            except ReadTimeoutException:
                logging.info(f"Command timed out: {cmd}, retrying")
                time.sleep(0.2)

    def run(self) -> None:
        while True:
            try:
                logging.info("Creating new serial port connection")
                self._dev = ESolarSerialDevice(self._path, device_addr=2)
                while True:
                    try:
                        new_values = []
                        for data_item, regs_for_item_it in itertools.groupby(regs, lambda x: x.data_item):
                            regs_for_item = list(regs_for_item_it)
                            addr_min = min(x.esolar_address for x in regs_for_item)
                            addr_max = max(x.esolar_address + (x.data_size // 2) for x in regs_for_item)

                            d = self._dev.get(data_item=data_item, data_offset=addr_min, data_length=(addr_max - addr_min) * 2)
                            time.sleep(0.2)

                            self._execute_commands()

                            for reg in regs_for_item:
                                reg_data = reg.process_raw(struct.unpack_from(reg.data_format, d, (reg.esolar_address - addr_min) * 2)[0])

                                new_values.append((reg, reg_data))

                        self._values = new_values
                        self._state_last_update = datetime.datetime.utcnow()

                        for reg, val in new_values:
                            logging.debug(f"{reg.name} {reg.to_modbus(val)}")

                        self._pending_updates = {}

                    except KeyboardInterrupt:
                        break
                    except ReadTimeoutException:
                        logging.error("Read timeout exception")
                        time.sleep(1)
            except KeyboardInterrupt:
                break
            except:
                traceback.print_exc()
                time.sleep(1)
            finally:
                if self._dev is not None:
                    self._dev.close()

    def get_state(self) -> Optional[ESolarState]:
        if self._state is None or \
                self._state_last_update is None or \
                datetime.datetime.utcnow() - self._state_last_update > datetime.timedelta(seconds=10):
            return None
        else:
            return self._state

    def get_values(self) -> Optional[List[Tuple[ESolarRegister, Any]]]:
        if self._state_last_update is None or \
                datetime.datetime.utcnow() - self._state_last_update > datetime.timedelta(seconds=10):
            return None
        else:
            merged_values = self._values
            for i, (reg, _) in enumerate(merged_values):
                if reg in self._pending_updates:
                    merged_values[i] = (reg, self._pending_updates[reg])

            return merged_values

    def set_word(self, *, data_item: int, data_offset: int, value: int) -> None:
        reg = get_register(data_item, data_offset)

        self._commands_queue.put((reg, value))
        self._pending_updates[reg] = value
