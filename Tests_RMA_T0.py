import unittest
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

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
