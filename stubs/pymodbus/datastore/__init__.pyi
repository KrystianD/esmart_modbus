from pymodbus.datastore.store import BaseModbusDataBlock


class ModbusSlaveContext:
    def __init__(self, di: BaseModbusDataBlock, co: BaseModbusDataBlock, hr: BaseModbusDataBlock, ir: BaseModbusDataBlock, zero_mode: bool): ...


class ModbusServerContext:
    def __init__(self, slaves: ModbusSlaveContext, single: bool): ...
