import ubluetooth as bluetooth
from micropython import const
from bleAdvReader import BLEAdvReader
import struct
from ubinascii import hexlify

# Advertising payloads are repeated packets of the following form:
#   1 byte data length (N + 1)
#   1 byte type (see constants below)
#   N bytes type-specific data

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)


def decode_field(payload, adv_type):
    i = 0
    result = []
    while i + 1 < len(payload):
        if payload[i + 1] == adv_type:
            result.append(payload[i + 2 : i + payload[i] + 1])
        i += 1 + payload[i]
    return result


def decode_name(payload):
    n = decode_field(payload, _ADV_TYPE_NAME)
    return str(n[0], "utf-8") if n else ""


def decode_services(payload):
    services = []
    for u in decode_field(payload, _ADV_TYPE_UUID16_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<h", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID32_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<d", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID128_COMPLETE):
        services.append(bluetooth.UUID(u))
    return services


def decode_mac_address(addr):
    return hexlify(addr).decode().upper()


class BTScan:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            # A central has connected to this peripheral.
            conn_handle, addr_type, addr = data
            print("_IRQ_CENTRAL_CONNECT")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            # A central has disconnected from this peripheral.
            conn_handle, addr_type, addr = data
            print("_IRQ_CENTRAL_DISCONNECT")
        elif event == _IRQ_GATTS_WRITE:
            # A client has written to this characteristic or descriptor.
            conn_handle, attr_handle = data
            print("_IRQ_GATTS_WRITE")
        elif event == _IRQ_GATTS_READ_REQUEST:
            # A client has issued a read. Note: this is only supported on STM32.
            # Return a non-zero integer to deny the read (see below), or zero (or None)
            # to accept the read.
            conn_handle, attr_handle = data
            print("_IRQ_GATTS_READ_REQUEST")
        elif event == _IRQ_SCAN_RESULT:
            # A single scan result.
            addr_type, addr, adv_type, rssi, adv_data = data
            addr = bytes(addr)
            adv_data = bytes(adv_data)
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND):
                print("_IRQ_SCAN_RESULT")
                mac = decode_mac_address(addr)
                if mac == "F83331B90F4B":

                    # print(decode_services(adv_data))
                    # self._name = decode_name(adv_data) or "?"
                    print(hexlify(adv_data))
                    advReader = BLEAdvReader(hexlify(adv_data))
                    for advElement in advReader.GetAllElements():
                        print(advElement)
                    self._addr_type = addr_type
                    self._addr = addr

                    self._ble.gap_scan(None)
                # print(addr_type, bytes(addr), adv_type, rssi, bytes(adv_data))
                # print(decode_name(adv_data) or "?", decode_services(adv_data))
        elif event == _IRQ_SCAN_DONE:
            # Scan duration finished or manually stopped.
            print("_IRQ_SCAN_DONE")
            if self._addr:
                print("Connecting")
                self.connect()
            pass
        elif event == _IRQ_PERIPHERAL_CONNECT:
            # A successful gap_connect().
            conn_handle, addr_type, addr = data
            print("_IRQ_PERIPHERAL_CONNECT")
            print(conn_handle, addr_type, addr)
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Connected peripheral has disconnected.
            conn_handle, addr_type, addr = data
            print("_IRQ_PERIPHERAL_DISCONNECT")
        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Called for each service found by gattc_discover_services().
            conn_handle, start_handle, end_handle, uuid = data
            print("_IRQ_GATTC_SERVICE_RESULT")
        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
            print("_IRQ_GATTC_SERVICE_DONE")
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Called for each characteristic found by gattc_discover_services().
            conn_handle, def_handle, value_handle, properties, uuid = data
            print("_IRQ_GATTC_CHARACTERISTIC_RESULT")
        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
            print("_IRQ_GATTC_CHARACTERISTIC_DONE")
        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            # Called for each descriptor found by gattc_discover_descriptors().
            conn_handle, dsc_handle, uuid = data
            print("_IRQ_GATTC_DESCRIPTOR_RESULT")
        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
            print("_IRQ_GATTC_DESCRIPTOR_DONE")
        elif event == _IRQ_GATTC_READ_RESULT:
            # A gattc_read() has completed.
            conn_handle, value_handle, char_data = data
            print("_IRQ_GATTC_READ_RESULT")
        elif event == _IRQ_GATTC_READ_DONE:
            # A gattc_read() has completed.
            # Note: The value_handle will be zero on btstack (but present on NimBLE).
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            print("_IRQ_GATTC_READ_DONE")
        elif event == _IRQ_GATTC_WRITE_DONE:
            # A gattc_write() has completed.
            # Note: The value_handle will be zero on btstack (but present on NimBLE).
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            print("_IRQ_GATTC_WRITE_DONE")
        elif event == _IRQ_GATTC_NOTIFY:
            # A server has sent a notify request.
            conn_handle, value_handle, notify_data = data
            print("_IRQ_GATTC_NOTIFY")
        elif event == _IRQ_GATTC_INDICATE:
            # A server has sent an indicate request.
            conn_handle, value_handle, notify_data = data
            print("_IRQ_GATTC_INDICATE")
        elif event == _IRQ_GATTS_INDICATE_DONE:
            # A client has acknowledged the indication.
            # Note: Status will be zero on successful acknowledgment, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            print("_IRQ_GATTS_INDICATE_DONE")
        elif event == _IRQ_MTU_EXCHANGED:
            # ATT MTU exchange complete (either initiated by us or the remote device).
            conn_handle, mtu = data
            print("_IRQ_MTU_EXCHANGED")
        elif event == _IRQ_L2CAP_ACCEPT:
            # A new channel has been accepted.
            # Return a non-zero integer to reject the connection, or zero (or None) to accept.
            conn_handle, cid, psm, our_mtu, peer_mtu = data
            print("_IRQ_L2CAP_ACCEPT")
        elif event == _IRQ_L2CAP_CONNECT:
            # A new channel is now connected (either as a result of connecting or accepting).
            conn_handle, cid, psm, our_mtu, peer_mtu = data
            print("_IRQ_L2CAP_CONNECT")
        elif event == _IRQ_L2CAP_DISCONNECT:
            # Existing channel has disconnected (status is zero), or a connection attempt failed (non-zero status).
            conn_handle, cid, psm, status = data
            print("_IRQ_L2CAP_DISCONNECT")
        elif event == _IRQ_L2CAP_RECV:
            # New data is available on the channel. Use l2cap_recvinto to read.
            conn_handle, cid = data
            print("_IRQ_L2CAP_RECV_IRQ_L2CAP_RECV")
        elif event == _IRQ_L2CAP_SEND_READY:
            # A previous l2cap_send that returned False has now completed and the channel is ready to send again.
            # If status is non-zero, then the transmit buffer overflowed and the application should re-send the data.
            conn_handle, cid, status = data
            print("_IRQ_L2CAP_SEND_READY")
        elif event == _IRQ_CONNECTION_UPDATE:
            # The remote device has updated connection parameters.
            conn_handle, conn_interval, conn_latency, supervision_timeout, status = data
            print("_IRQ_CONNECTION_UPDATE")
            print(conn_handle, conn_interval, conn_latency, supervision_timeout, status)
        elif event == _IRQ_ENCRYPTION_UPDATE:
            # The encryption state has changed (likely as a result of pairing or bonding).
            conn_handle, encrypted, authenticated, bonded, key_size = data
            print("_IRQ_ENCRYPTION_UPDATE")
        elif event == _IRQ_GET_SECRET:
            # Return a stored secret.
            # If key is None, return the index'th value of this sec_type.
            # Otherwise return the corresponding value for this sec_type and key.
            sec_type, index, key = data
            print("_IRQ_GET_SECRET")
            return value
        elif event == _IRQ_SET_SECRET:
            # Save a secret to the store for this sec_type and key.
            sec_type, key, value = data
            print("_IRQ_SET_SECRET")
            return True
        # elif event == _IRQ_PASSKEY_ACTION:
        #     # Respond to a passkey request during pairing.
        #     # See gap_passkey() for details.
        #     # action will be an action that is compatible with the configured "io" config.
        #     # passkey will be non-zero if action is "numeric comparison".
        #     conn_handle, action, passkey = data

    # Connect to the specified device (otherwise use cached address from a scan).
    def connect(self, addr_type=None, addr=None, callback=None):
        self._addr_type = addr_type or self._addr_type
        self._addr = addr or self._addr
        self._conn_callback = callback
        if self._addr_type is None or self._addr is None:
            return False
        self._ble.gap_connect(self._addr_type, self._addr)
        return True

    def scan(self):
        self._ble.gap_scan(5000, 30000, 30000)


bt = BTScan()
bt.scan()
