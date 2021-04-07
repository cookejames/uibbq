# Micropython iBBQ
Micropython support for BLE iBBQ thermometers such as those made by Inkbird.

## Dependencies
This driver depends on `uasyncio` and [aioble](https://github.com/jimmo/micropython-lib/tree/lib-aioble/aioble). 

Note that aioble requires a build of MicroPython created after Feb 18 2021 which are the unstable 1.14 releases or 1.15.

## Features
* Read temperature levels from all probes
* Read battery level
* Set the display to either celcius or farenheit (temperature readings are in celcius)
* Asynchronous api

## Usage
Connect and read the temperature
```python
def handle_data(d):
    print("Result:", d)

async def run():
    ibbq = iBBQ(handle_data)
    await ibbq.connect()
    await ibbq.disconnect()

asyncio.run(run())
```

Read the battery level
```python
async def run():
    ibbq = iBBQ(handle_data)
    await ibbq.connect()
    print("Battery:", await ibbq.battery_level())
    await ibbq.disconnect()

asyncio.run(run())
```

Set the units on the display
```python
async def run():
    ibbq = iBBQ(handle_data)
    await ibbq.connect()
    await ibbq.set_display_to_celcius()
    await ibbq.set_display_to_farenheit()
    await ibbq.disconnect()

asyncio.run(run())
```

## Credits

[Adafruit circuitpython iBBQ](https://github.com/adafruit/Adafruit_CircuitPython_BLE_iBBQ) and 
[Go iBBQ](https://github.com/sworisbreathing/go-ibbq) were very useful for decoding the iBBQ protocol.
The Adafruit library in particular has an empirically worked formula for calculating the battery voltage.