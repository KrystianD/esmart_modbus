import struct
from enum import Enum
from typing import Union, List, Callable


class ModbusRegisterType(Enum):
    InputRegister = 0
    HoldingRegister = 1
    Coil = 2


class DataType(Enum):
    UInt16 = 0
    Int16 = 1
    UInt32s = 2


def uint32s_to_int(x: bytes) -> int:
    high: int
    low: int
    (high, low) = struct.unpack("<HH", x)
    return (high << 16) | low


class ESmartRegister:
    def __init__(self, name: str, *, esmart_data_item: int, esmart_address: int, data_type: DataType, scale: Union[int, float] = 1,
                 modbus_address: int,
                 modbus_type: ModbusRegisterType,
                 esmart_to_modbus: Callable[[int], Union[int, bool]] = lambda x: x,
                 modbus_to_esmart: Callable[[int], int] = lambda x: x) -> None:
        self.name = name
        self.data_item = esmart_data_item
        self.esmart_address = esmart_address
        self.data_type = data_type
        self.scale = scale
        self.modbus_address = modbus_address
        self.modbus_type = modbus_type
        self.emart_to_modbus = esmart_to_modbus
        self.modbus_to_esmart = modbus_to_esmart

    @property
    def data_format(self) -> str:
        if self.data_type == DataType.Int16:
            return "<h"
        if self.data_type == DataType.UInt16:
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
        if self.data_type == DataType.UInt16 and isinstance(value, int):
            return value
        if self.data_type == DataType.UInt32s and isinstance(value, bytes):
            return uint32s_to_int(value)
        raise Exception

    def to_modbus(self, value: int) -> int:
        return self.emart_to_modbus(value)

    def to_modbus_regs(self, value: int) -> List[int]:
        modbus_value = self.to_modbus(value)

        if self.data_type in (DataType.Int16, DataType.UInt16):
            return [modbus_value]
        if self.data_type == DataType.UInt32s:
            return [(value & 0x0000ffff) >> 0,
                    (value & 0xffff0000) >> 16]

        raise Exception("invalid data type")

    def from_modbus_regs(self, regs: List[int]) -> Union[int, List[int]]:
        if self.data_type in (DataType.Int16, DataType.UInt16):
            return regs[0]
        if self.data_type == DataType.UInt32s:
            return [(regs[0]) << 0 |
                    (regs[1]) << 16]

        raise Exception("invalid data type")

    def to_esmart_word(self, value: int) -> int:
        esmart_value = self.modbus_to_esmart(value)

        if self.data_type in (DataType.Int16, DataType.UInt16):
            return esmart_value

        raise Exception("invalid data type")


u16 = DataType.UInt16
s16 = DataType.Int16
u32 = DataType.UInt32s

esmart_registers = [
    ESmartRegister("        wChgMode", esmart_data_item=0, esmart_address=0x00, data_type=u16, modbus_address=1, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("         wPvVolt", esmart_data_item=0, esmart_address=0x01, data_type=u16, modbus_address=2, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("        mBatVolt", esmart_data_item=0, esmart_address=0x02, data_type=u16, modbus_address=3, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("        wChgCurr", esmart_data_item=0, esmart_address=0x03, data_type=u16, modbus_address=4, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("        wOutVolt", esmart_data_item=0, esmart_address=0x04, data_type=u16, modbus_address=5, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("       wLoadVolt", esmart_data_item=0, esmart_address=0x05, data_type=u16, modbus_address=6, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("       wLoadCurr", esmart_data_item=0, esmart_address=0x06, data_type=u16, modbus_address=7, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("       wChgPower", esmart_data_item=0, esmart_address=0x07, data_type=u16, modbus_address=8, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("      wLoadPower", esmart_data_item=0, esmart_address=0x08, data_type=u16, modbus_address=9, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("        wBatTemp", esmart_data_item=0, esmart_address=0x09, data_type=s16, modbus_address=10, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("      wInnerTemp", esmart_data_item=0, esmart_address=0x0A, data_type=s16, modbus_address=11, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("         wBatCap", esmart_data_item=0, esmart_address=0x0B, data_type=s16, modbus_address=12, modbus_type=ModbusRegisterType.InputRegister),

    ESmartRegister("      dwTotalEng", esmart_data_item=2, esmart_address=0x0E, data_type=u32, modbus_address=13, modbus_type=ModbusRegisterType.InputRegister),
    ESmartRegister("  dbLoadTotalEng", esmart_data_item=2, esmart_address=0x14, data_type=u32, modbus_address=15, modbus_type=ModbusRegisterType.InputRegister),

    ESmartRegister("       wBulkVolt", esmart_data_item=1, esmart_address=0x03, data_type=u16, modbus_address=1, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("      wFloatVolt", esmart_data_item=1, esmart_address=0x04, data_type=u16, modbus_address=2, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("     wMaxChgCurr", esmart_data_item=1, esmart_address=0x05, data_type=u16, modbus_address=3, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("  wMaxDisChgCurr", esmart_data_item=1, esmart_address=0x06, data_type=u16, modbus_address=4, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("wEqualizeChgVolt", esmart_data_item=1, esmart_address=0x07, data_type=u16, modbus_address=5, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("wEqualizeChgTime", esmart_data_item=1, esmart_address=0x08, data_type=u16, modbus_address=6, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("     bLoadUseSel", esmart_data_item=1, esmart_address=0x09, data_type=u16, modbus_address=7, modbus_type=ModbusRegisterType.HoldingRegister),

    ESmartRegister("        wLoadOvp", esmart_data_item=7, esmart_address=0x01, data_type=u16, modbus_address=8, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("        wLoadUvp", esmart_data_item=7, esmart_address=0x02, data_type=u16, modbus_address=9, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("         wBatOvp", esmart_data_item=7, esmart_address=0x03, data_type=u16, modbus_address=10, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("         wBatOvB", esmart_data_item=7, esmart_address=0x04, data_type=u16, modbus_address=11, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("         wBatUvp", esmart_data_item=7, esmart_address=0x05, data_type=u16, modbus_address=12, modbus_type=ModbusRegisterType.HoldingRegister),
    ESmartRegister("         wBatUvB", esmart_data_item=7, esmart_address=0x06, data_type=u16, modbus_address=13, modbus_type=ModbusRegisterType.HoldingRegister),

    ESmartRegister("  wBacklightTime", esmart_data_item=2, esmart_address=0x16, data_type=u16, modbus_address=14, modbus_type=ModbusRegisterType.HoldingRegister),

    ESmartRegister("     loadEnabled", esmart_data_item=4, esmart_address=0x01, data_type=u16, modbus_address=1, modbus_type=ModbusRegisterType.Coil,
                   esmart_to_modbus=lambda x: x == 5117,
                   modbus_to_esmart=lambda x: 5117 if x else 5118),
]


def get_register(data_item: int, data_offset: int) -> ESmartRegister:
    return [x for x in esmart_registers if x.data_item == data_item and x.esmart_address == data_offset][0]
