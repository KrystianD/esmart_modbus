esmart_modbus
=======

[eSmart MPPT charger](http://www.solarcontroller-inverter.com/products/I-Panda-20A-60A-12V-24V-36V-48V-MPPT-Solar-Charge-Controller-Residential-Off-grid-Solar-System-Batte.html) exposes RS485 interface for data reading and control. However, it is not Modbus RTU compatible. This project wraps its custom protocol and exposes Modbus TCP server that allows this device to be used in Modbus-based systems. 

Usage
-----

```sh
python -m esolar_modbus --esmart-port /dev/ttyUSB0 --modbus-host localhost --modbus-port=5000
```
