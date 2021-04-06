# boot.py - - runs on boot-up
import network
import upip
import config

DEPENDENCIES = []
INSTALL_PACKAGES = False


def install_packages():
    print("Installing dependencies:", DEPENDENCIES)
    upip.install(DEPENDENCIES)


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())

    if INSTALL_PACKAGES:
        install_packages()


# do_connect()
