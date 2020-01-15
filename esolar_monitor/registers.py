import struct
from enum import Enum
from typing import Union, List, Callable


class ModbusRegisterType(Enum):
    InputRegister = 0
    HoldingRegister = 1
    Coil = 2


class DataType(Enum):
    Uint16 = 0
    Int16 = 1
    UInt32s = 2


def uint32s_to_int(x: bytes) -> int:
    high: int
    low: int
    (high, low) = struct.unpack("<HH", x)
    return (high << 16) | low


class ESolarRegister:
    def __init__(self, name: str, *, esolar_data_item: int, esolar_address: int, data_type: DataType, scale: Union[int, float] = 1,
                 modbus_address: int,
                 modbus_type: ModbusRegisterType,
                 esolar_to_modbus: Callable[[int], Union[int, bool]] = lambda x: x,
                 modbus_to_esolar: Callable[[int], int] = lambda x: x) -> None:
        self.name = name
        self.data_item = esolar_data_item
        self.esolar_address = esolar_address
        self.data_type = data_type
        self.scale = scale
        self.modbus_address = modbus_address
        self.modbus_type = modbus_type
        self.esolar_to_modbus = esolar_to_modbus
        self.modbus_to_esolar = modbus_to_esolar

    @property
    def data_format(self) -> str:
        if self.data_type == DataType.Int16:
            return "<h"
        if self.data_type == DataType.Uint16:
            return "<H"
        if self.data_type == DataType.UInt32s:
            return "4s"

        raise Exception("invalid data type")

    @property
    def data_size(self) -> int:
        return struct.calcsize(self.data_format)

    @property
    def data_size_words(self) -> int:
        return self.data_size // 2

    def process_raw(self, value: Union[int, bytes]) -> int:
        if self.data_type == DataType.Int16 and isinstance(value, int):
            return value
        if self.data_type == DataType.Uint16 and isinstance(value, int):
            return value
        if self.data_type == DataType.UInt32s and isinstance(value, bytes):
            return uint32s_to_int(value)
        raise Exception

    def to_modbus(self, value: int) -> int:
        return self.esolar_to_modbus(value)

    def to_modbus_regs(self, value: int) -> List[int]:
        modbus_value = self.to_modbus(value)

        if self.data_type in (DataType.Int16, DataType.Uint16):
            return [modbus_value]
        if self.data_type == DataType.UInt32s:
            return [(value & 0x0000ffff) >> 0,
                    (value & 0xffff0000) >> 16]

        raise Exception("invalid data type")

    def from_modbus_regs(self, regs: List[int]) -> Union[int, List[int]]:
        if self.data_type in (DataType.Int16, DataType.Uint16):
            return regs[0]
        if self.data_type == DataType.UInt32s:
            return [(regs[0]) << 0 |
                    (regs[1]) << 16]

        raise Exception("invalid data type")

    def to_esolar_word(self, value: int) -> int:
        esolar_value = self.modbus_to_esolar(value)

        if self.data_type in (DataType.Int16, DataType.Uint16):
            return esolar_value

        raise Exception("invalid data type")


u16 = DataType.Uint16
s16 = DataType.Int16
u32 = DataType.UInt32s

regs = [
    ESolarRegister("        wChgMode", esolar_data_item=0, esolar_address=0x00, data_type=u16, modbus_address=1, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("         wPvVolt", esolar_data_item=0, esolar_address=0x01, data_type=u16, modbus_address=2, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("        mBatVolt", esolar_data_item=0, esolar_address=0x02, data_type=u16, modbus_address=3, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("        wChgCurr", esolar_data_item=0, esolar_address=0x03, data_type=u16, modbus_address=4, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("        wOutVolt", esolar_data_item=0, esolar_address=0x04, data_type=u16, modbus_address=5, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("       wLoadVolt", esolar_data_item=0, esolar_address=0x05, data_type=u16, modbus_address=6, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("       wLoadCurr", esolar_data_item=0, esolar_address=0x06, data_type=u16, modbus_address=7, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("       wChgPower", esolar_data_item=0, esolar_address=0x07, data_type=u16, modbus_address=8, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("      wLoadPower", esolar_data_item=0, esolar_address=0x08, data_type=u16, modbus_address=9, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("        wBatTemp", esolar_data_item=0, esolar_address=0x09, data_type=s16, modbus_address=10, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("      wInnerTemp", esolar_data_item=0, esolar_address=0x0A, data_type=s16, modbus_address=11, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("         wBatCap", esolar_data_item=0, esolar_address=0x0B, data_type=s16, modbus_address=12, modbus_type=ModbusRegisterType.InputRegister),

    ESolarRegister("      dwTotalEng", esolar_data_item=2, esolar_address=0x0E, data_type=u32, modbus_address=13, modbus_type=ModbusRegisterType.InputRegister),
    ESolarRegister("  dbLoadTotalEng", esolar_data_item=2, esolar_address=0x14, data_type=u32, modbus_address=15, modbus_type=ModbusRegisterType.InputRegister),

    ESolarRegister("       wBulkVolt", esolar_data_item=1, esolar_address=0x03, data_type=u16, modbus_address=1, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("      wFloatVolt", esolar_data_item=1, esolar_address=0x04, data_type=u16, modbus_address=2, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("     wMaxChgCurr", esolar_data_item=1, esolar_address=0x05, data_type=u16, modbus_address=3, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("  wMaxDisChgCurr", esolar_data_item=1, esolar_address=0x06, data_type=u16, modbus_address=4, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("wEqualizeChgVolt", esolar_data_item=1, esolar_address=0x07, data_type=u16, modbus_address=5, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("wEqualizeChgTime", esolar_data_item=1, esolar_address=0x08, data_type=u16, modbus_address=6, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("     bLoadUseSel", esolar_data_item=1, esolar_address=0x09, data_type=u16, modbus_address=7, modbus_type=ModbusRegisterType.HoldingRegister),

    ESolarRegister("        wLoadOvp", esolar_data_item=7, esolar_address=0x01, data_type=u16, modbus_address=8, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("        wLoadUvp", esolar_data_item=7, esolar_address=0x02, data_type=u16, modbus_address=9, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("         wBatOvp", esolar_data_item=7, esolar_address=0x03, data_type=u16, modbus_address=10, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("         wBatOvB", esolar_data_item=7, esolar_address=0x04, data_type=u16, modbus_address=11, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("         wBatUvp", esolar_data_item=7, esolar_address=0x05, data_type=u16, modbus_address=12, modbus_type=ModbusRegisterType.HoldingRegister),
    ESolarRegister("         wBatUvB", esolar_data_item=7, esolar_address=0x06, data_type=u16, modbus_address=13, modbus_type=ModbusRegisterType.HoldingRegister),

    ESolarRegister("     loadEnabled", esolar_data_item=4, esolar_address=0x01, data_type=u16, modbus_address=1, modbus_type=ModbusRegisterType.Coil,
                   esolar_to_modbus=lambda x: x == 5117,
                   modbus_to_esolar=lambda x: 5117 if x else 5118),
]


def get_register(data_item: int, data_offset: int) -> ESolarRegister:
    return [x for x in regs if x.data_item == data_item and x.esolar_address == data_offset][0]
