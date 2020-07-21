from dataclasses import dataclass


@dataclass
class ESolarState:
    charging_mode: int = 0
    pv_voltage: float = 0
    bat_voltage: float = 0
    bat_current: float = 0
    bat_power: int = 0
    bat_charge: int = 0
    load_voltage: float = 0
    load_current: float = 0
    load_power: int = 0
    load_consumption: int = 0
    bat_temp: int = 0
    inner_temp: int = 0
    bat_capacity: int = 0

    load_enabled: bool = False


@dataclass
class ESolarConfig:
    bat_type: int = 0
    bat_sys_type: int = 0
    bulk_volt: float = 0
    float_volt: float = 0
    max_charging_current: float = 0
    max_discharging_current: float = 0
    equalize_charging_voltage: float = 0
    equalize_charging_time: int = 0
    load_use_sel: int = 0
