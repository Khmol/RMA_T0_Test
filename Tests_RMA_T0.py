import unittest
import datetime
import Config_RMA_T0_Test
from RMA_T0_Test import *
from PyQt5 import QtWidgets #QtCore, QtGui,

class TestUM(unittest.TestCase):

    def setUp(self):
        self.widg = QtWidgets.QApplication(sys.argv)
        self.app = RMA_T0_Test()

    def test_ParseID(self):
        data = '55AA1D00FCFFFF01002D0000010001010107011B0023001257345737383120D9D4'
        res = self.app.ParseID(data, DATA_START_INDEX, DATA_END_INDEX)
        self.assertEqual(res, '20313837573457120023001B')

    def test_Convert_HexStr_to_Str(self):
        data = '55AA6500FCFFFF010069000001000101010100524D412052544C532076332E3230202D205474616C2076322E3730202D2042634D2076312E3230202D2053543332463330332052463233335F414D502052463231322076312E303020342D36304D487A20646267E3EE'
        res = Convert_HexStr_to_Str(data, DATA_START_INDEX, DATA_END_INDEX)
        self.assertEqual(res, 'RMA RTLS v3.20 - Ttal v2.70 - BcM v1.20 - ST32F303 RF233_AMP RF212 v1.00 4-60MHz dbg')

    def test_SendNextCommandWriteAnswer(self):
        now = datetime.datetime.now()
        filename = '{}_{}_{} test.txt'.format(now.day, now.month, now.year)
        self.file = open(filename, 'at')
        # заполняем переменные нужными значениями и переопределяем методы
        self.app.rightAnswer = self.app.LoadTxPacketByMode('mode_6', '_answer_')
        self.app.measureCounter = 1
        self.app.FECCounter = 1
        self.app.DQFCounter = 1
        self.app.result = False
        self.app.now = datetime.datetime.now()

        def GetRsData():
            self.app.dataRx = []
            dataHex = '55AA6500FCFFFF010069000001000101010100524D412052544C532076332E3230202D205474616C2076322E3730202D2042634D2076312E3230202D2053543332463330332052463233335F414D502052463231322076312E303020342D36304D487A20646267E3EE'
            self.app.dataRx.append(['Rx:<<<', dataHex, dataHex])
            dataHex = '55AA1C00FCFFFF0100930000010001010102004E6F76202033203230323007CA'
            self.app.dataRx.append(['Rx:<<<', dataHex, dataHex])
            dataHex = '55AA1900FCFFFF0100A800000100010101030031363A30303A343326A6'
            self.app.dataRx.append(['Rx:<<<', dataHex, dataHex])
            dataHex = '55AA1D00FCFFFF0100C3000001000101010701250032000957345737383120E166'
            self.app.dataRx.append(['Rx:<<<', dataHex, dataHex])

        self.app.GetRsData = GetRsData
        self.app.SendNextCommandWriteAnswer('mode_6', self.file)
        self.app.lastLengthRxDataProcessed = 1
        self.app.SendNextCommandWriteAnswer('mode_6', self.file)
        self.app.lastLengthRxDataProcessed = 2
        self.app.SendNextCommandWriteAnswer('mode_6', self.file)
        self.app.lastLengthRxDataProcessed = 3
        self.app.SendNextCommandWriteAnswer('mode_6', self.file)
        self.file.close()

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
