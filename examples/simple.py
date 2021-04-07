import uasyncio as asyncio
from uibbq import iBBQ


def handle_data(d):
    print("Result:", d)


async def run():
    ibbq = iBBQ(handle_data)
    await ibbq.connect()
    print("Battery:", await ibbq.battery_level())
    await asyncio.sleep(10)
    print("Disconnecting")
    await ibbq.disconnect()


asyncio.run(run())