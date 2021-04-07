"""Micropython iBBQ Interface"""

__version__ = "1.0"

from struct import unpack_from
import uasyncio as asyncio
import bluetooth
import aioble


class iBBQ:
    _DEVICE_NAME = "iBBQ"

    _PRIMARY_SERVICE = bluetooth.UUID(0xFFF0)
    _ACCOUNT_AND_VERIFY_CHARACTERISTIC = bluetooth.UUID(0xFFF2)
    _SETTINGS_RESULT_CHARACTERISTIC = bluetooth.UUID(0xFFF1)
    _SETTINGS_WRITE_CHARACTERISTIC = bluetooth.UUID(0xFFF5)
    _REAL_TIME_DATA_CHARACTERISTIC = bluetooth.UUID(0xFFF4)
    _HISTORIC_DATA_CHARACTERISTIC = bluetooth.UUID(0xFFF3)

    _CREDENTIALS_MSG = b"\x21\x07\x06\x05\x04\x03\x02\x01\xb8\x22\x00\x00\x00\x00\x00"
    _REALTIME_DATA_ENABLE_MSG = b"\x0B\x01\x00\x00\x00\x00"
    _UNITS_FAHRENHEIT_MSG = b"\x02\x01\x00\x00\x00\x00"
    _UNITS_CELSIUS_MSG = b"\x02\x00\x00\x00\x00\x00"
    _REQUEST_BATTERY_LEVEL_MSG = b"\x08\x24\x00\x00\x00\x00"

    def __init__(self, data_handler):
        self._device = None
        self._connection = None
        self._real_time_data = None
        self._settings_data = None
        self._data_handler = data_handler

    def reset(self):
        self._device = None
        self._connection = None
        self._real_time_data = None
        self._data_handler = None
        self._settings_data = None

    async def set_display_to_celcius(self):
        await self._write(
            iBBQ._PRIMARY_SERVICE,
            iBBQ._SETTINGS_WRITE_CHARACTERISTIC,
            iBBQ._UNITS_CELSIUS_MSG,
        )

    async def set_display_to_farenheit(self):
        await self._write(
            iBBQ._PRIMARY_SERVICE,
            iBBQ._SETTINGS_WRITE_CHARACTERISTIC,
            iBBQ._UNITS_FAHRENHEIT_MSG,
        )

    async def find_ibbq(self):
        # Scan for 5 seconds, in active mode, with very low interval/window (to
        # maximise detection rate).
        async with aioble.scan(
            5000, interval_us=30000, window_us=30000, active=True
        ) as scanner:
            async for result in scanner:
                # See if it matches our name
                if result.name() == iBBQ._DEVICE_NAME:
                    self._device = result.device
                    return True
        return False

    async def _write(self, service, characteristic, message):
        if not self._connection.is_connected():
            raise "Cannot write, device disconnected"
        try:
            _service = await self._connection.service(service)
            _characteristic = await _service.characteristic(characteristic)
            await _characteristic.write(message)
            return _characteristic
        except asyncio.TimeoutError:
            raise "Timeout during write"

    async def _subscribe(self, service, characteristic):
        if not self._connection.is_connected():
            raise "Cannot write, device disconnected"
        try:
            _service = await self._connection.service(service)
            _characteristic = await _service.characteristic(characteristic)
            await _characteristic.subscribe()
            return _characteristic
        except asyncio.TimeoutError:
            raise "Timeout during subscribe"

    async def connect(self):
        await self.find_ibbq()
        if not self._device:
            print("iBBQ not found")
            return

        print("Connecting to", self._device)
        self._connection = await self._device.connect()
        print("Connected to", self._device)

        try:
            # login
            await self._write(
                iBBQ._PRIMARY_SERVICE,
                iBBQ._ACCOUNT_AND_VERIFY_CHARACTERISTIC,
                iBBQ._CREDENTIALS_MSG,
            )
            # subscribe to settings
            self._settings_data = await self._subscribe(
                iBBQ._PRIMARY_SERVICE, iBBQ._SETTINGS_RESULT_CHARACTERISTIC
            )
            # subscribe to real time data
            self._real_time_data = await self._subscribe(
                iBBQ._PRIMARY_SERVICE, iBBQ._REAL_TIME_DATA_CHARACTERISTIC
            )
            # enable real time data
            await self._write(
                iBBQ._PRIMARY_SERVICE,
                iBBQ._SETTINGS_WRITE_CHARACTERISTIC,
                iBBQ._REALTIME_DATA_ENABLE_MSG,
            )
            # enable real time data
            await self._write(
                iBBQ._PRIMARY_SERVICE,
                iBBQ._SETTINGS_WRITE_CHARACTERISTIC,
                iBBQ._REALTIME_DATA_ENABLE_MSG,
            )
            asyncio.create_task(self._read_data())
        except Exception as e:
            self.disconnect()
            raise e

    async def battery_level(self):
        """Get current battery level in volts as ``(current_voltage, max_voltage)``.
        Results are approximate and may differ from the
        actual battery voltage by 0.1v or so.
        """
        try:
            await self._write(
                iBBQ._PRIMARY_SERVICE,
                iBBQ._SETTINGS_WRITE_CHARACTERISTIC,
                iBBQ._REQUEST_BATTERY_LEVEL_MSG,
            )
            data = await self._settings_data.notified(1000)
            if len(data) > 5:
                header, current_voltage, max_voltage = unpack_from("<BHH", data)
                if header == 0x24:
                    # From https://github.com/adafruit/Adafruit_CircuitPython_BLE_iBBQ
                    # Calibration was determined empirically, by comparing
                    # the returned values with actual measurements of battery voltage,
                    # on one sample each of two different products.
                    return (
                        current_voltage / 2000 - 0.3,
                        (6550 if max_voltage == 0 else max_voltage) / 2000,
                    )
            return None
        except Exception as e:
            print("Error retrieving battery level")
            print(e)
            return None

    async def _read_data(self):
        while self._connection.is_connected():
            try:
                data = await self._real_time_data.notified(1000)
                if data:
                    probe_data = []
                    for r in range(len(data) - 1):
                        if r % 2 == 0:
                            temperature = unpack_from("<H", data[r : r + 2])[0] / 10

                            probe_data.append(
                                None if temperature == 6552.6 else int(temperature)
                            )
                    self._data_handler(probe_data)
            except Exception as e:
                pass

            await asyncio.sleep(0.1)

    async def disconnect(self):
        await self._connection.disconnect()
