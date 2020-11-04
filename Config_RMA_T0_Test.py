#coding: utf8

#class Config_Serial_Qt():
BAUDRATES = ['1200', '9600', '19200', '38400', '57600', '115200','230400','460800','921600']    #возможные значения скоростей для RS-232
DEFAULT_IP_ADDRESS = ['127.0.0.1']
MAX_WAIT_BYTES = 1000    #максимальное количество байт в буфере порта на прием
NUMBER_SCAN_PORTS = 40   #количество портов для сканирования 10
SET = 1
RESET = 0
CNT_POSITION = 9
MAX_NUMBER_CLEAR_RX = 100
MAX_ERROR_COUNTER = 10
DEFAULT_SETTINGS_FILENAME = 'settings.ini'
PACKETS_FILENAME = 'packets.ini'
DEFAULT_LOG_FILENAME = 'log.txt'
DEFAULT_TXT_FILENAME = 'receive.txt'
TX_DATA_PAGE = 'TX_Data'
DEFAULT_RX_DATA = ['Direction','Hex', 'String', 'Address', 'Port']
MAX_RX_LENGTH = 20000
DEFAULT_TIMER = 10
TX_TIMER = 200
TX_RTLS_TIMER = 500
DEFAULT_UI_TIMER = 201
LOG = False
RS_START = bytearray([0x55, 0xAA])  # стартовая последовательность для RS
DEFAULT_UDP_PORT = 7798
DEFAULT_TCP_PORT = 7700
XLS_DATA = {
            "DELAY": 0,
            "CNT": 1,
            "DATA": 2,
            "FORMAT": 3,
            "REPEAT": 4,
            "CRC": 5,
            }
TEXT_SIZE = 12
DEFAULT_ADDRESS_RMS = 0xF630
CUR_RTLS_LABEL = ['self.ui.label_NumberRMS','self.ui.label_ModeRTLS_Cur_Dist', 'self.ui.label_ModeRTLS_Cur_DQF','self.ui.label_ModeRTLS_Cur_FEC']
CUR_RTLS_LABEL_MIDDLE = ['','self.ui.label_ModeRTLS_Mid_Dist', 'self.ui.label_ModeRTLS_Mid_DQF','self.ui.label_ModeRTLS_Mid_FEC']
CUR_RTLS_LABEL_DEF_TEXT = ['Номер РМС: ', 'Измеренное расстояние: ', 'DQF РМС, текущее: ','Значение FEC, текущее: ']
CUR_RTLS_LABEL_DEF_TEXT_MIDDLE = ['','Среднее расстояние: ', 'DQF РМС, среднее: ','Значение FEC, среднее: ']
CUR_RTLS_LABEL_DEF_TEXT_END = ['', ' см', ' %', '']
MIN_DISTANCE = 400
MAX_DISTANCE = 800
MIN_DQF = 95
MIN_FEC = -1
MAX_FEC = 1
NUMBER_DIMENSION = 20
ID_START_INDEX = 28
ID_END_INDEX = 36
DATA_START_INDEX = 38
DATA_END_INDEX = -4
ID_VERSION = '01010101'
ID_DATA = '01010102'
ID_TIME = '01010103'
ID_ID = '01010107'


