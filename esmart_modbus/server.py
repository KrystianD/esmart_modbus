import threading
import traceback
from typing import Dict, List, Tuple, Sequence, Any

from pymodbus.datastore.store import BaseModbusDataBlock
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from esmart_monitor.monitor import ESmartMonitor
from esmart_monitor.registers import ModbusRegisterType, ESmartRegister, regs, DataType


def create_registers(registers: Sequence[Tuple[ESmartRegister, Any]]) -> Dict[int, int]:
    modbus_values = {}

    for reg, value in registers:
        address = reg.modbus_address
        value_registers = reg.to_modbus_regs(value)

        for i, value_register in enumerate(value_registers):
            modbus_values[address + i] = value_register

    return modbus_values


class RegistersBlock(BaseModbusDataBlock):
    def __init__(self, monitor: ESmartMonitor, reg_type: ModbusRegisterType) -> None:
        super().__init__()
        self.monitor = monitor
        self.reg_type = reg_type

    def setValues(self, address: int, values: List[int]) -> None:
        assert self.reg_type in (ModbusRegisterType.Coil, ModbusRegisterType.HoldingRegister)

        modbus_reg: ESmartRegister = [x for x in regs if x.modbus_address == address and x.modbus_type == self.reg_type][0]

        assert modbus_reg.data_type in (DataType.UInt16,)

        value = values[0]
        self.monitor.set_word(data_item=modbus_reg.data_item, data_offset=modbus_reg.esmart_address, value=modbus_reg.to_esmart_word(value))

    def validate(self, address: int, count: int = 1) -> bool:
        try:
            values = self.monitor.get_values()

            if values is None:
                return False

            modbus_values = create_registers([(x[0], x[1]) for x in values if x[0].modbus_type == self.reg_type])
            return all(i in modbus_values for i in range(address, address + count))
        except:
            traceback.print_exc()
            raise

    def getValues(self, address: int, count: int = 1) -> List[int]:
        try:
            values = self.monitor.get_values()

            if values is None:
                raise Exception("invalid state")

            modbus_values = create_registers([(x[0], x[1]) for x in values if x[0].modbus_type == self.reg_type])
            return [modbus_values[i] for i in range(address, address + count)]
        except:
            traceback.print_exc()
            raise


def run_server(esmart_serial_port_path: str, modbus_host: str, modbus_port: int) -> None:
    mon = ESmartMonitor(esmart_serial_port_path)

    th = threading.Thread(target=mon.run)
    th.daemon = True
    th.start()

    ir_block = RegistersBlock(mon, ModbusRegisterType.InputRegister)
    co_block = RegistersBlock(mon, ModbusRegisterType.Coil)
    hr_block = RegistersBlock(mon, ModbusRegisterType.HoldingRegister)
    empty = BaseModbusDataBlock()
    store = ModbusSlaveContext(di=empty, co=co_block, hr=hr_block, ir=ir_block, zero_mode=True)
    context = ModbusServerContext(slaves=store, single=True)

    StartTcpServer(context, address=(modbus_host, modbus_port))
