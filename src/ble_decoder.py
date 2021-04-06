class BLEAdvReader:

    # ============================================================================
    # ===( Constants )============================================================
    # ============================================================================

    DATA_TYPE_FLAGS = 0x01
    DATA_TYPE_INCOMP_16BITS_UUIDS = 0x02
    DATA_TYPE_COMP_16BITS_UUIDS = 0x03
    DATA_TYPE_INCOMP_32BITS_UUIDS = 0x04
    DATA_TYPE_COMP_32BITS_UUIDS = 0x05
    DATA_TYPE_INCOMP_128BITS_UUIDS = 0x06
    DATA_TYPE_COMP_128BITS_UUIDS = 0x07
    DATA_TYPE_SHORT_NAME = 0x08
    DATA_TYPE_COMPLETE_NAME = 0x09
    DATA_TYPE_TX_POWER_LEVEL = 0x0A
    DATA_TYPE_DEVICE_CLASS = 0x0B
    DATA_TYPE_SMP_PAIR_HASH_C = 0x0C
    DATA_TYPE_SMP_PAIR_HASH_C192 = 0x0D
    DATA_TYPE_SMP_PAIR_RAND_R = 0x0E
    DATA_TYPE_SMP_PAIR_RAND_R192 = 0x0F
    DATA_TYPE_DEVICE_ID = 0x10
    DATA_TYPE_SECU_MNGR_TK_VAL = 0x11
    DATA_TYPE_SECU_MNGR_OOB_FLAGS = 0x12
    DATA_TYPE_SLAVE_CONN_INT_RNG = 0x13
    DATA_TYPE_16BITS_SVC_SOL_UUIDS = 0x14
    DATA_TYPE_128BITS_SVC_SOL_UUIDS = 0x15
    DATA_TYPE_SVC_DATA = 0x16
    DATA_TYPE_SVC_DATA_16BITS_UUID = 0x17
    DATA_TYPE_PUB_TARGET_ADDR = 0x18
    DATA_TYPE_RAND_TARGET_ADDR = 0x19
    DATA_TYPE_APPEARANCE = 0x1A
    DATA_TYPE_ADV_INT = 0x1B
    DATA_TYPE_LE_BLT_DEVICE_ADDR = 0x1C
    DATA_TYPE_LE_ROLE = 0x1D
    DATA_TYPE_SMP_PAIR_HASH_C256 = 0x1E
    DATA_TYPE_SMP_PAIR_RAND_R256 = 0x1F
    DATA_TYPE_32BITS_SVC_SOL_UUIDS = 0x20
    DATA_TYPE_SVC_DATA_32BITS_UUID = 0x21
    DATA_TYPE_SVC_DATA_128BITS_UUID = 0x22
    DATA_TYPE_LE_SECU_CONN_RAND_VAL = 0x23
    DATA_TYPE_URI = 0x24
    DATA_TYPE_INDOOR_POS = 0x25
    DATA_TYPE_TRANS_DISCOV_DATA = 0x26
    DATA_TYPE_LE_SUPPORT_FEAT = 0x27
    DATA_TYPE_CHAN_MAP_UPD_INDIC = 0x28
    DATA_TYPE_PB_ADV = 0x29
    DATA_TYPE_MESH_MSG = 0x2A
    DATA_TYPE_MESH_BEACON = 0x2B
    DATA_TYPE_3D_INFO_DATA = 0x3D
    DATA_TYPE_MANUFACTURER_DATA = 0xFF

    class InvalidAdvData(Exception):
        pass

    def __init__(self, advertisingData):
        self._advData = dict()
        self._advObj = []
        self._advDataProcess(advertisingData)
        self._advDataElementsProcess()
        # self._advKnownElementsProcess()

    def _advDataProcess(self, advData):
        if advData:
            advDataLen = len(advData)
            idx = 0
            while idx < advDataLen:
                dataLen = advData[idx]
                idx += 1
                if dataLen > 0:
                    idxEnd = idx + dataLen
                    if idxEnd < advDataLen:
                        dataType = advData[idx]
                        data = advData[idx + 1 : idxEnd]
                        self._advData[dataType] = data
                    else:
                        raise self.InvalidAdvData("Data element invalid size")
                    idx = idxEnd

    def _advDataElementsProcess(self):
        if not self._advData:
            raise self.InvalidAdvData("No advertising data element")
        for dataType in self._advData:
            data = self._advData[dataType]
            advObj = None
            if dataType == self.DATA_TYPE_FLAGS:
                try:
                    advObj = self.Flags(ord(data))
                except:
                    raise self.InvalidAdvData("Invalid flags data element")
            # elif dataType == self.DATA_TYPE_COMP_16BITS_UUIDS:
            #     try:
            #         advObj = self.AdoptedService16bits(unpack("<H", data)[0])
            #     except:
            #         raise self.InvalidAdvData(
            #             "Invalid adopted service 16bits data element"
            #         )
            # elif dataType == self.DATA_TYPE_COMP_32BITS_UUIDS:
            #     try:
            #         advObj = self.AdoptedService32bits(unpack("<I", data)[0])
            #     except:
            #         raise self.InvalidAdvData(
            #             "Invalid adopted service 32bits data element"
            #         )
            # elif dataType == self.DATA_TYPE_COMP_128BITS_UUIDS:
            #     try:
            #         advObj = self.AdoptedService128bits(data)
            #     except:
            #         raise self.InvalidAdvData(
            #             "Invalid adopted service 128bits data element"
            #         )
            # elif dataType == self.DATA_TYPE_SHORT_NAME:
            #     try:
            #         advObj = self.ShortName(data.decode())
            #     except:
            #         raise self.InvalidAdvData("Invalid short name data element")
            elif dataType == self.DATA_TYPE_COMPLETE_NAME:
                try:
                    advObj = self.CompleteName(data.decode())
                except:
                    raise self.InvalidAdvData("Invalid complete name data element")
            # elif dataType == self.DATA_TYPE_TX_POWER_LEVEL:
            #     try:
            #         advObj = self.TXPowerLevel(unpack("<b", data)[0])
            #     except:
            #         raise self.InvalidAdvData("Invalid TX power level data element")
            # elif dataType == self.DATA_TYPE_SVC_DATA:
            #     try:
            #         advObj = self.ServiceData(unpack("<H", data[0:2])[0], data[2:])
            #     except:
            #         raise self.InvalidAdvData("Invalid service data element")
            # elif dataType == self.DATA_TYPE_MANUFACTURER_DATA:
            #     try:
            #         advObj = self.ManufacturerData(unpack("<H", data[0:2])[0], data[2:])
            #     except:
            #         raise self.InvalidAdvData("Invalid manufacturer data element")
            if advObj:
                self._advObj.append(advObj)

    def GetDataByDataType(self, dataType) :
        return self._advData.get(dataType)

    def GetAllElements(self) :
        return self._advObj
        
    class CompleteName :

        def __init__(self, completeName='') :
            self._completeName = completeName

        def __str__(self) :
            return self._completeName

    class Flags :

        FLAG_LE_LIMITED_DISC_MODE       = 0x01
        FLAG_LE_GENERAL_DISC_MODE       = 0x02
        FLAG_BR_EDR_NOT_SUPPORTED       = 0x04
        FLAG_LE_BR_EDR_CONTROLLER       = 0x08
        FLAG_LE_BR_EDR_HOST             = 0x10
        FLAGS_LE_ONLY_LIMITED_DISC_MODE = 0x01 | 0x04
        FLAGS_LE_ONLY_GENERAL_DISC_MODE = 0x02 | 0x04

        def __init__(self, flags=0x00) :
            self._flags = flags

        def __str__(self) :
            return '{0:08b}'.format(self._flags)

        @property
        def LE_LIMITED_DISC_MODE(self) :
            return bool(self._flags & self.FLAG_LE_LIMITED_DISC_MODE)

        @property
        def LE_GENERAL_DISC_MODE(self) :
            return bool(self._flags & self.FLAG_LE_GENERAL_DISC_MODE)

        @property
        def BR_EDR_NOT_SUPPORTED(self) :
            return bool(self._flags & self.FLAG_BR_EDR_NOT_SUPPORTED)

        @property
        def LE_BR_EDR_CONTROLLER(self) :
            return bool(self._flags & self.FLAG_LE_BR_EDR_CONTROLLER)

        @property
        def LE_BR_EDR_HOST(self) :
            return bool(self._flags & self.FLAG_LE_BR_EDR_HOST)

        @property
        def LE_ONLY_LIMITED_DISC_MODE(self) :
            return bool(self._flags & self.FLAGS_LE_ONLY_LIMITED_DISC_MODE)

        @property
        def LE_ONLY_GENERAL_DISC_MODE(self) :
            return bool(self._flags & self.FLAGS_LE_ONLY_GENERAL_DISC_MODE)
