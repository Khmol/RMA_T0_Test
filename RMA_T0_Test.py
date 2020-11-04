#coding: utf8


import datetime
import socket
import socketserver
import sys
from configparser import ConfigParser         # импортируем парсер ini файлов
import serial
from BIN_ASCII import *
from BIN_ASCII import Convert_ArrBite_to_ArrCharHex, Convert_ArrBite_to_ArrChar
from CRC16 import *
from Config_RMA_T0_Test import *
from UI_RMA_T0_Test import *
from OperationUI import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import QBasicTimer, QTimer
from PyQt5.QtWidgets import QMessageBox
from pyexcel_xlsx import get_data
from pyexcel_xlsx import save_data

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        while True:
            dataTCP = self.request.recv(1024)
            adr, port = self.client_address
            if len(dataTCP) > 0:
                RMA_T0_Test.DataRxAppend(myapp, dataTCP, adr, port)
            if dataTCP == b'':
                break

class RMA_T0_Test(QtWidgets.QMainWindow):

    #инициализация окна
    # c:\Python36_32\Scripts\pyuic5 UI_RMA_T0_Test.ui -o UI_RMA_T0_Test.py
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # инициализация переменных
        self.xlsFilename = ''
        self.cntPosition = CNT_POSITION
        self.log = LOG
        self.txtFilename = DEFAULT_TXT_FILENAME
        self.maxRxLength = MAX_RX_LENGTH
        self.curTextSize = TEXT_SIZE
        self.addressRMS = DEFAULT_ADDRESS_RMS
        self.step = 0
        self.errorCounter = 0
        self.lastLengthRxData = 0
        self.lastLengthRxDataProcessed = 0
        self.sumMiddleDist = 0
        self.sumMiddleDQF = 0
        self.sumMiddleFEC = 0
        self.measureCounter = 0
        self.DQFCounter = 0
        self.FECCounter = 0
        self.result = False
        self.now = None
        self.minDistance = MIN_DISTANCE
        self.maxDistance = MAX_DISTANCE
        self.minDQF = MIN_DQF
        self.minFEC = MIN_FEC
        self.maxFEC = MAX_FEC
        self.numberDimension = NUMBER_DIMENSION
        # словарь для STATUS
        self.CUR_STATUS = {
            "IDLE": 1,
            "RS_RECIEVE": 2,
            "RS_1": 3,
            "RS_2": 4,
            "RS_3": 5,
            "RS_4": 6,
            "RS_RTLS": 7,
            "TCP_RECIEVE": 8,
            "TCP_1": 9,
            "TCP_2": 10,
            "TCP_3": 11,
            "TCP_4": 12,
            "TCP_RTLS": 13,
            "RS_FILE": 14,
            "TCP_FILE": 15,
        }
        self.STATUS_NEW = 1  # текущее состояние
        self.STATUS_OLD = 1  # прошлое состояние
        self.CUR_CONNECTION = {
            "IDLE": 1,
            "RS": 2,
            "TCP": 3,
            "UDP": 4,
        }
        self.CRCPresent = True
        self.cur_line = 1
        self.activeConnection = 1
        self.counter = 0
        self.needNumberPackets = 0
        self.sentOne = False
        self.dataTx = []
        self.dataRx = []
        self.rightAnswer = []
        self.sockUDP = None
        self.sockTCP = None
        self.udpServer = None
        self.tcpServer = None
        self.timerUi = None
        self.file = None
        self.curClientAddress = DEFAULT_IP_ADDRESS[0]
        self.curUDPServerPort = DEFAULT_UDP_PORT
        self.curTCPServerPort = DEFAULT_TCP_PORT
        self.curUDPClientPort = DEFAULT_UDP_PORT
        self.curTCPClientPort = DEFAULT_TCP_PORT
        self.connectedTCPClientPort = None
        self.connectedTCPClientAddress = None
        self.curTCPClientThread = None
        #инициализация интерфейса
        self.ui = Ui_UI_RMAT0_Test()
        self.ui.setupUi(self)
        #настройка действий по кнопкам
        self.ui.pushButton_open_COM.clicked.connect(self.OpenRsHandler)          #обрабатываем нажатие кнопки отсрыть порт
        self.ui.pushButton_close_COM.clicked.connect(self.CloseRsPushButtonHandler)        #обрабатываем нажатие кнопки закрыть порт
        self.ui.pushButton_open_TCP_Client.clicked.connect(self.TcpClientConnectHendler)
        self.ui.pushButton_close_TCP_Client.clicked.connect(self.TcpClientDisconnectHendler)
        self.ui.pushButtonClearText.clicked.connect(self.ClearTextHendler)
        self.ui.pushButton_Mode_TX.clicked.connect(self.ModeTxHendler)
        self.ui.pushButton_Mode_RX.clicked.connect(self.ModeRxHendler)
        self.ui.pushButton_Mode_RTLS.clicked.connect(self.ModeRTLSHendler)
        self.ui.pushButton_Mode_Work.clicked.connect(self.ModeWorkHendler)

        # вывод строки в statusbar
        self.ui.statusbar.showMessage('Версия 1.00')
        # инициализация RS
        self.InitRS()

        # добавляем нужные скорости в comboBox_Baudrate
        self.ui.comboBox_Baudrate.addItems(BAUDRATES)
        self.ui.comboBox_Baudrate.setCurrentIndex(5)
        # читаем настройки из ini файла
        self.ReadSettings()
        # установить размер текста в окне вывода данных
        font = QtGui.QFont()
        font.setPointSize(self.curTextSize)
        self.ui.plainTextEdit.setFont(font)
        # задаем начальные параметры lineEdit_UDP_Server_IP_port

        # добавляем нужные IP адреса для comboBox_IP_Address_UDP_Server
        self.curServerAddress = DEFAULT_IP_ADDRESS
        try:
            pcName = socket.getfqdn()
            indexPoint = pcName.index('.')
            self.curServerAddress.append(socket.gethostbyname(pcName[0:indexPoint]))
        except:
            pass

        # задаем начальные параметры lineEdit_TCP_Server_IP_port
        self.ui.lineEdit_TCP_IP_Addr.setInputMask('000.000.000.000')
        self.ui.lineEdit_TCP_IP_Addr.setText(self.curClientAddress)
        self.ui.lineEdit_TCP_Client_IP_Port.setText(str(self.curTCPClientPort))
        self.ui.lineEdit_TCP_Client_IP_Port.setInputMask('0000')

        # инициализация таймера
        self.StartUiUpdateTimer(self.UpdateTextTextEdit)
        self.StartBasicTimer()

    # *********************************************************************
    def SendStageData(self, mode, step, timer):
        '''
        отправка следующего пакета с названием как в mode
        :param mode: название пакета в ini файле 'mode_1'
        :param step: номер пакета для отправки
        :return:
        '''
        if self.dataTx == []:
            self.dataTx = self.LoadTxPacketByMode(mode, '_send_')
        if step > len(self.dataTx):
            self.dataTx.clear()
            return False
        for self.curTxPack in self.dataTx[step:]:
            self.TransmitData(self.curTxPack)
            self.mainTimer.start(timer, self)  # запускаем обработку таймера
            return True

    # *********************************************************************
    def ModeTxHendler(self):
        '''
        чтение пакетов для отправки из ini файла
        :return:
        '''
        self.rightAnswer = self.LoadTxPacketByMode('mode_1', '_answer_')
        ClearLabelStatus(self.ui)
        self.ClearTxCounters()
        self.ui.label_ModeTx.setText('Статус выполнения: Выполняется')
        if self.activeConnection == self.CUR_CONNECTION['TCP']:
            self.STATUS_NEW = self.CUR_STATUS['TCP_1']
        elif self.activeConnection == self.CUR_CONNECTION['RS']:
            self.STATUS_NEW = self.CUR_STATUS['RS_1']
        self.SendStageData('mode_1', 0, TX_TIMER)

    # *********************************************************************
    def ModeRxHendler(self):
        '''
        чтение пакетов для отправки из ini файла
        :return:
        '''
        self.rightAnswer = self.LoadTxPacketByMode('mode_2', '_answer_')
        ClearLabelStatus(self.ui)
        self.ClearTxCounters()
        self.ui.label_ModeRx.setText('Статус выполнения: Выполняется')
        if self.activeConnection == self.CUR_CONNECTION['TCP']:
            self.STATUS_NEW = self.CUR_STATUS['TCP_2']
        elif self.activeConnection == self.CUR_CONNECTION['RS']:
            self.STATUS_NEW = self.CUR_STATUS['RS_2']
        self.SendStageData('mode_2', 0, TX_TIMER)

    # *********************************************************************
    def ModeRTLSHendler(self):
        '''
        чтение пакетов для отправки из ini файла
        :return:
        '''
        self.rightAnswer = self.LoadTxPacketByMode('mode_3', '_answer_')
        ClearLabelStatus(self.ui)
        for index in range(1,len(CUR_RTLS_LABEL)):
            cmd = '{}.setText("{}{}")'.format(CUR_RTLS_LABEL[index], CUR_RTLS_LABEL_DEF_TEXT[index],
                                              CUR_RTLS_LABEL_DEF_TEXT_END[index])
            eval(cmd)
            cmd = '{}.setText("{}{}")'.format(CUR_RTLS_LABEL_MIDDLE[index], CUR_RTLS_LABEL_DEF_TEXT_MIDDLE[index],
                                              CUR_RTLS_LABEL_DEF_TEXT_END[index])
            eval(cmd)
        self.ui.label_ModeRTLS_Counter.setText('Количество измерений: 0')
        self.ClearTxCounters()
        self.ui.label_ModeRTLS.setText('Статус выполнения: Выполняется')
        if self.activeConnection == self.CUR_CONNECTION['TCP']:
            self.STATUS_NEW = self.CUR_STATUS['TCP_3']
        elif self.activeConnection == self.CUR_CONNECTION['RS']:
            self.STATUS_NEW = self.CUR_STATUS['RS_3']
        self.SendStageData('mode_3', 0, TX_TIMER)

    # *********************************************************************
    def ModeWorkHendler(self):
        '''
        чтение пакетов для отправки из ini файла
        :return:
        '''
        self.rightAnswer = self.LoadTxPacketByMode('mode_4', '_answer_')
        ClearLabelStatus(self.ui)
        self.ClearTxCounters()
        self.ui.label_ModeWork.setText('Статус выполнения: Выполняется')
        if self.activeConnection == self.CUR_CONNECTION['TCP']:
            self.STATUS_NEW = self.CUR_STATUS['TCP_4']
        elif self.activeConnection == self.CUR_CONNECTION['RS']:
            self.STATUS_NEW = self.CUR_STATUS['RS_4']
        self.SendStageData('mode_4', 0, TX_TIMER)

    # *********************************************************************
    def LoadTxPacketByMode(self, mode, type):
        '''
        чтение пакетов для отправки из ini файла
        :return: данные в str формате
        '''
        try:
            data = []
            # определяем парсер конфигурации из ini файла
            self.modeTxPackets = ConfigParser()
            # читаем конфигурацию
            self.modeTxPackets.read(PACKETS_FILENAME)
            # Читаем нужные значения
            pack = '{}_number_pack'.format(mode)
            self.needNumberPackets = int(self.modeTxPackets.get('main', pack))
            for i in range(self.needNumberPackets):
                data.append(self.modeTxPackets.get('main', '{}{}{}'.format(mode, type, (i+1))))
            return data
        except Exception as EXP:
            out_str = "Ошибка наполнения файла с описанием пакетов для передачи: ".format(str(EXP))
            QMessageBox(QMessageBox.Warning, 'Сообщение', out_str, QMessageBox.Ok).exec()

    # *********************************************************************
    def StartBasicTimer(self):
        #инициализация таймера приемника по RS
        self.mainTimer = QBasicTimer()
        self.mainTimer.stop()

    # *********************************************************************
    def StartUiUpdateTimer(self, func, interval=DEFAULT_UI_TIMER):
        def handler():
            func()
        self.timerUi = QtCore.QTimer()
        self.timerUi.timeout.connect(handler)
        self.timerUi.start(interval)

    # *********************************************************************
    def DataRxAppend(self, data, address, port):
        '''
        добавить данные к allDataRx
        :return:
        '''
        self.dataRx.append(['Rx:<<<',Convert_ArrBite_to_ArrCharHex(data).upper(),
                            Convert_ArrBite_to_ArrChar(data),
                            str(address), str(port)])

    # *********************************************************************
    def SetConnectedTcpClientPort(self, port):
        self.connectedTCPClientPort = port

    # *********************************************************************
    def SetConnectedTcpClientAddress(self, address):
        self.connectedTCPClientAddress = address

    # *********************************************************************
    def TcpClientConnectHendler(self):
        if self.activeConnection == self.CUR_CONNECTION["IDLE"] or \
                        self.activeConnection == self.CUR_CONNECTION["TCP"]:
            try:
                self.curClientAddress = self.ui.lineEdit_TCP_IP_Addr.text()
                self.curTCPClientPort = int(self.ui.lineEdit_TCP_Client_IP_Port.text())

            except:
                out_str = "Такого порта нет. Введите корректное значение."
                QMessageBox(QMessageBox.Warning, 'Сообщение', out_str, QMessageBox.Ok).exec()
                return
            # изменяем активность виджетов внешнего вида
            ChangeButtonsTCPClientConnected(self.ui)
            # тестовое подключение к sockTCP
            try:
                self.sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sockTCP.connect((self.curClientAddress, self.curTCPClientPort))
            except Exception as EXP:
                # изменяем активность виджетов внешнего вида
                ChangeButtonsTCPClientDisconnected(self.ui)
                out_str = "Невозможно подключиться по указанному адресу и порту: {}".format(str(EXP))
                QMessageBox(QMessageBox.Warning, 'Ошибка подключения.', out_str, QMessageBox.Ok).exec()
            finally:
                self.sockTCP.close()
            if self.activeConnection == self.CUR_CONNECTION["IDLE"]:
                self.STATUS_OLD = self.STATUS_NEW
                self.STATUS_NEW = self.CUR_STATUS["TCP_1"]
                # переходим в режим TCP если флаг установлен
                self.activeConnection = self.CUR_CONNECTION["TCP"]
            DisableAllButtonsRS(self.ui)
            EnableAllButtonsMode(self.ui)
            # запускаем обработку таймера
            # self.mainTimer.start(DEFAULT_TIMER, self)

    # *********************************************************************
    def TcpClientDisconnectHendler(self):
        # изменяем активность виджетов внешнего вида
        ChangeButtonsTCPClientDisconnected(self.ui)
        self.STATUS_OLD = self.STATUS_NEW
        self.STATUS_NEW = self.CUR_STATUS["IDLE"]
        self.activeConnection = self.CUR_CONNECTION["IDLE"]
        EnableAllButtonsRS(self.ui)
        DisableAllButtonsMode(self.ui)
        self.dataTx.clear()
        self.WriteSettings()

    # *********************************************************************
    def ClearTextHendler(self):
        self.ui.plainTextEdit.clear()

    #*********************************************************************
    def ReadSettings(self):
        '''
        чтение настроек из ini файла
        :return:
        '''
        #читаем переменные из файла настроек при первом входе
        try:
            # определяем парсер конфигурации из ini файла
            self.config = ConfigParser()
            # читаем конфигурацию
            self.config.read(DEFAULT_SETTINGS_FILENAME)
            # Читаем нужные значения
            self.txtFilename = self.config.get('main', 'txt_filename')
            self.cntPosition = int(self.config.get('main', 'cnt_position'))
            self.curClientAddress = self.config.get('main', 'last_client_address')
            self.curTCPClientPort = int(self.config.get('main', 'last_tcp_client_port'))
            self.addressRMS = int(self.config.get('main', 'rms_address'), 16)
            self.curTextSize = int(self.config.get('main', 'text_size'))
            self.minDistance = int(self.config.get('main', 'min_distance'))
            self.maxDistance = int(self.config.get('main', 'max_distance'))
            self.minDQF = int(self.config.get('main', 'min_dqf'))
            self.minFEC = int(self.config.get('main', 'min_fec'))
            self.maxFEC = int(self.config.get('main', 'max_fec'))
            self.numberDimension = int(self.config.get('main', 'number_dimension'))
        except:
            # add a new section and some values
            try:
                self.config.add_section('main')
                # записываем настройки в ini
                self.WriteSettings()
            except:
                # записываем настройки в ini
                self.WriteSettings()

    # *********************************************************************
    def WriteSettings(self):
        '''
        # запись текущих настороек в ini
        :return:
        '''
        # изменяем запись в файле ini
        self.config.set('main', 'cnt_position', str(self.cntPosition))
        self.config.set('main', 'txt_filename', DEFAULT_TXT_FILENAME)
        self.config.set('main', 'last_client_address', self.curClientAddress)
        self.config.set('main', 'last_tcp_client_port', str(self.curTCPClientPort))
        self.config.set('main', 'text_size', str(self.curTextSize))
        self.config.set('main', 'rms_address', hex(self.addressRMS))
        self.config.set('main', 'min_distance', str(self.minDistance))
        self.config.set('main', 'max_distance', str(self.maxDistance))
        self.config.set('main', 'min_dqf', str(self.minDQF))
        self.config.set('main', 'min_fec', str(self.minFEC))
        self.config.set('main', 'max_fec', str(self.maxFEC))
        self.config.set('main', 'number_dimension', str(self.numberDimension))

        # записываем изменения в файл
        with open(DEFAULT_SETTINGS_FILENAME, 'w') as configfile:
            self.config.write(configfile)

    # *********************************************************************
    def InitRS(self):
        '''
        первоначальная инициализация RS
        :return:
        '''
        list_com_ports = '' #перечень доступных портов
        #проверка какие порты свободны
        try:
            portList = self.ScanRsPorts()
            for s in portList:
                list_com_ports += s + ' '
        except Exception as EXP:
            QMessageBox(QMessageBox.Critical, 'Ошибка', str(EXP), QMessageBox.Ok).exec()

        finally:
            #настройка списка для выбора порта
            #добавляем свободные порты в comboBox_COM
            self.ui.comboBox_COM.clear()
            self.ui.comboBox_COM.addItems(list_com_ports.split())
            self.ui.comboBox_COM.setCurrentIndex(0)

    #*********************************************************************
    def OpenRsHandler(self):
        '''
        обработчик открытия порта
        :return:
        '''
        if self.ui.comboBox_COM.currentText() != '':
            # проверяем текущее соединение
            if self.activeConnection == self.CUR_CONNECTION["IDLE"]:
                DisableAllButtonsTCP(self.ui)
                self.SerialConfig()    #инициализируем порт
                # переходим в режим RS_RECIEVE если флаг установлен
                self.STATUS_NEW = self.CUR_STATUS["RS_RECIEVE"]
                self.activeConnection = self.CUR_CONNECTION["RS"]  # Текущее соединение по RS
                ChangeRsButtonsIdle(self.ui)  #активируем кнопки
                EnableAllButtonsMode(self.ui)
            else:
                out_str = "Соединение уже установлено. Для выполения подключения нужно закрыть текущее соединение."
                QMessageBox(QMessageBox.Warning, 'Сообщение', out_str, QMessageBox.Ok).exec()
        else:
            out_str = "Порт не выбран."
            QMessageBox(QMessageBox.Warning, 'Сообщение', out_str, QMessageBox.Ok).exec()

    #*********************************************************************
    def ReturnUiIdle(self):
        if self.activeConnection == self.CUR_CONNECTION["RS"]:
            ChangeRsButtonsIdle(self.ui, self.xlsFilename)
        elif self.activeConnection == self.CUR_CONNECTION["UDP"]:
            ChangeUDPButtonsIdle(self.ui, self.xlsFilename)
        elif self.activeConnection == self.CUR_CONNECTION["TCP"]:
            ChangeTCPButtonsIdle(self.ui, self.xlsFilename)

    #*********************************************************************
    def CloseRsPushButtonHandler(self):
        '''
        обработчик кнопки закрытия порта
        :return:
        '''
        # записываем принятые данные в XLS
        # self.SaveDataToXls()
        # закрываем порт
        self.ser.close()
        # активного соединения нет
        self.activeConnection = self.CUR_CONNECTION["IDLE"]
        # переходим в режим IDLE
        self.STATUS_OLD = self.STATUS_NEW
        self.STATUS_NEW = self.CUR_STATUS["IDLE"]
        self.lastLengthRxData = 0

        self.dataTx.clear()
        # выключаем все кнопки и элементы выбора
        #ChangeActiveButtonsRsClose(self.ui)
        EnableAllButtonsTCP(self.ui)
        DisableAllButtonsMode(self.ui)
        ChangeActiveButtonsRsSelected(self.ui)  #изменяем кнопки для выбора порта и скорости        self.WriteSettings()
        self.WriteSettings()

    #*********************************************************************
    def ScanRsPorts(self):
        """scan for available ports. return a list of tuples (num, name)"""
        available = []
        for i in range(NUMBER_SCAN_PORTS):
            try:
                s = serial.Serial(i)
                available.append((s.portstr))
                s.close()   # explicit close 'cause of delayed GC in java
            except serial.SerialException:
                pass
        return available

    #*********************************************************************
    def SerialConfig(self):
        '''
        настройка порта со значением выбранным в comboBox_COM
        :return:
        '''
        baudrate = int(self.ui.comboBox_Baudrate.currentText())
        try:
            #проверяем есть ли порт
            if self.ser.isOpen() == False:#
                self.ser = serial.Serial(self.ui.comboBox_COM.currentText(),
                    baudrate=baudrate,#9600,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0,
                    bytesize=serial.EIGHTBITS,
                    xonxoff=0)
        except:
            try:
                self.ser = serial.Serial(self.ui.comboBox_COM.currentText(),
                        baudrate=baudrate,#9600,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=0,
                        bytesize=serial.EIGHTBITS,
                        xonxoff=0)
                if baudrate == 115200:
                    self.TIME_TO_RX = 40#было 40
                elif baudrate == 57600:
                    self.TIME_TO_RX = 60#было 60
                elif baudrate == 38400:
                    self.TIME_TO_RX = 80#было 80
                elif baudrate == 19200:
                    self.TIME_TO_RX = 100#
                elif baudrate == 9600:
                    self.TIME_TO_RX = 150#
                elif baudrate == 1200:
                    self.TIME_TO_RX = 1200#
                elif baudrate == 230400:
                    self.TIME_TO_RX = 40#
                elif baudrate == 460800:
                    self.TIME_TO_RX = 40#
                elif baudrate == 921600:
                    pass
                self.TIME_TO_RX_DATA = 10#
            except:
                out_str = "Порт будет закрыт, повторите прошивку заново."
                QMessageBox(QMessageBox.Warning, 'Ошибка №2 работы с портом ',out_str , QMessageBox.Ok).exec()
                #Закрытие порта и выключение записи - переход в исходное состояние
                self.STATUS_OLD = self.STATUS_NEW
                self.STATUS_NEW = self.ID2["IDLE"]
                self.CloseRsPushButtonHandler()
                return

    #*********************************************************************
    def RecieveRsData (self):
        '''
        проверка наличия данных в буфере RS и получение данных из порта
        :return:
        '''
        RX_Data = ''  #данных нет
        while self.ser.inWaiting() > 0:
            RX_Data = self.ser.read(MAX_WAIT_BYTES)
        if LOG == True:
            self.string_Data = '<< ' + str(len(RX_Data)) + ' байт '
            for i in range(len(RX_Data)):
                self.string_Data = self.string_Data + ' ' + str(hex(RX_Data[i]))
            print (self.string_Data)
            # записываем в лог файл принятые данные
            self.logfile.write(self.string_Data + '\n')
        return RX_Data

    #*********************************************************************
    def SetCounter(self, data):
        '''
        автоматическое заполнение позиции счетчика пакетов
        :param data:
        :return:
        '''
        if len(data) > self.cntPosition:
            data[self.cntPosition] = self.counter
            self.counter += 1
            if self.counter == 256:
                self.counter = 0
            return True
        else:
            out_str = 'Длина данных меньше положенной в строке {0:d}'.format(self.cur_line + 1)
            QMessageBox(QMessageBox.Warning, 'Ошибка длины данных ', out_str, QMessageBox.Ok).exec()
            return False

    #*********************************************************************
    def TransmitData (self, string_data):
        '''
        выполнить передачу данных
        :param string_data: данные для передачи
        :return:
        '''
        #установка начальног значения CRC16
        try:
            crc = INITIAL_MODBUS
            if self.activeConnection == self.CUR_CONNECTION["RS"]:
                #проверка открыт ли порт
                self.ser.isOpen()
            if len(string_data) > CNT_POSITION * 2:# умножаем на 2 потому как 2 символа на один HEX
                try:
                    bin_data = Convert_HexStr_to_Bytearray(string_data)
                except ValueError as EXP:
                    out_str = 'Ошибка преобразовани данных: {}'.format (str(EXP))
                    QMessageBox(QMessageBox.Warning, 'Ошибка преобразовани данных ',
                                                  out_str, QMessageBox.Ok).exec()
                    return False
                if not self.SetCounter(bin_data):
                    return False
                # удаляем CRC16 который присутствует в исходном пакете (в ini файле)
                if self.CRCPresent == True:
                    del bin_data[-2:]
                # производим рассчет CRC16 для bin_data
                for ch in bin_data[2:]:
                    crc = calcByte(ch, crc)
                bin_data += crc.to_bytes(2, byteorder='little')
                # записываем данные в ЛОГ файл и консоль
                self.dataRx.append(['Tx:>>>', Convert_ArrBite_to_ArrCharHex(bin_data).upper(),
                                    Convert_ArrBite_to_ArrChar(bin_data)])
                if self.activeConnection == self.CUR_CONNECTION["RS"]:
                    # передаем данные в порт RS
                    self.ser.write(bin_data)
                elif self.activeConnection == self.CUR_CONNECTION["TCP"]:
                    # передаем данные в sockTCP
                    try:
                        self.sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.sockTCP.settimeout(0.3)
                        self.sockTCP.connect((self.curClientAddress, self.curTCPClientPort))
                        self.sockTCP.sendall(bin_data)
                        result = self.sockTCP.recv(1024)
                        self.DataRxAppend(result, self.curClientAddress, self.curTCPClientPort)
                    except Exception as EXP:
                        self.dataRx.append(['Ошибка приема ответа: {}'.format(str(EXP)), '', ''])
                    finally:
                        self.sockTCP.close()
                return True
        except Exception as EXP:
            QMessageBox(QMessageBox.Critical, 'Ошибка', str(EXP), QMessageBox.Ok).exec()

    #*********************************************************************
    def SaveDataToXls(self):
        '''
        запись принятых данных в xls
        :return:
        '''
        if len(self.dataRx) > 0:
            try:
                data_rx = get_data(self.xlsFilename[0])
                data_rx.update({"RX_Data": self.dataRx})
                if len(self.dataRx) < self.maxRxLength:
                    save_data(self.xlsFilename[0], data_rx)
                else:
                    self.SavedataToTxt(self.dataRx, self.txtFilename)
                return True
            except Exception as EXP:
                # останавливаем отправку данных
                ChangeRsButtonsIdle(self.ui, self.xlsFilename)
                self.STATUS_OLD = self.STATUS_NEW
                self.STATUS_NEW = self.CUR_STATUS["IDLE"]
                self.lastLengthRxData = 0
                QMessageBox(QMessageBox.Critical, 'Ошибка записи файла данных: ',
                            'Ошибка работы с файлом для записи: ' + str(EXP),
                                               QtWidgets.QMessageBox.Ok).exec()
        return False

    #*********************************************************************
    def SavedataToTxt(self, data,fileName):
        '''
        запись списка данных в текстовый файл
        :param data:
        :return:
        '''
        writeData = ''
        for d in data:
            writeData += str(d)[1:-1] + '\n'
        with open(fileName, 'w', encoding='utf-8') as f:
            f.write(writeData)
        QMessageBox(QMessageBox.Warning, 'Превышение длины данных',
                                       'Превышена длина данных для записи в xls. Данные были записаны в файл ' + self.txtFilename,
                                       QtWidgets.QMessageBox.Ok).exec()

    #*********************************************************************
    def LogData(self):
        if LOG == True:
            # записываем в лог файл пепелаееые алееые
            self.logfile.write(self.string_data + '\n')
            # выводим переданные данные в консоль
            print(self.string_data)

    #*********************************************************************
    def ShowDialog_Open_File(self):
        '''
        Обработка кнопки открытия файла
        :return:
        '''
        try:
            self.xlsFilename = QtWidgets.QFileDialog.getOpenFileName(
                   self, 'Open File', self.xlsFilename[0] , 'XLS файл (*.xls)',
                   None, QtWidgets.QFileDialog.DontUseNativeDialog)
        except:
            self.xlsFilename = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Open File', '', 'XLS файл (*.xls)',
                None, QtWidgets.QFileDialog.DontUseNativeDialog)
        if self.xlsFilename[0] != '':
            self.ui.pushButton_Send.setEnabled(SET)  # активируем кнопку "Отправить данные"
            self.WriteSettings() # записать название файла в ini файл настроек
            # отображаем имя открытого файла
            ShowFileName(self.xlsFilename, self.ui)
        else:
            # читаем название файла из настроек
            self.ReadSettings()

    #*********************************************************************
    def ReadXlsData(self, file_name):
        '''
        Чтение данных для отправки из XLS файла
        :return: данные
        '''
        try:
            data_rx = None
            if file_name != None:
                data_rx = get_data(file_name[0])
            return data_rx

        except Exception as EXP:
            QMessageBox(QMessageBox.Critical, 'Ошибка обработки файла данных для передачи', str(EXP),
                                       QMessageBox.Ok).exec()

    #*********************************************************************
    def ParseData(self, data):
        '''
        парсинг пакетов позиционирования на основе стартовый байт RS_START
        :param data: данные для парсинга
        :return: returnData - список пакетов
        '''
        returnData = []
        if data != '':
            try:
                indexStart = 0
                indexStop = 0
                lenData = len(data)
                if lenData > 0:
                    for i in range(lenData - 1):
                       if data[i] == RS_START[0] and data[i+1] == RS_START[1]:
                           indexStop = i
                           if indexStop > indexStart:
                               returnData.append(data[indexStart:indexStop])
                               indexStart = i
                    if indexStart == indexStop:
                        returnData.append(data[indexStart:])
            except Exception as EXP:
                out_str = str(EXP)
                QMessageBox(QMessageBox.Warning, 'Ошибка.', out_str, QMessageBox.Ok).exec()
        return returnData

    #*********************************************************************
    def GetRsData(self):
        currentData = self.ParseData(self.RecieveRsData())
        if currentData != []:
            lenCurData = len(currentData)
            if lenCurData > 0:
                for d in currentData:
                    self.dataRx.append(['Rx:<<<',Convert_ArrBite_to_ArrCharHex(d).upper(), Convert_ArrBite_to_ArrChar(d)])

    #*********************************************************************
    def CheckCommand(self, rx_data, right_data, first_position = CNT_POSITION*2, sec_position = -8):
        if rx_data[:first_position] == right_data[:first_position] and \
                        rx_data[first_position+2:sec_position] == right_data[first_position+2:sec_position]:
            return True
        else:
            return False

    #*********************************************************************
    def timerEvent(self, e):
        '''
        обработчик таймера
        :param e:
        :return:
        '''
        self.mainTimer.stop() #выключаем таймер
        try:
            if self.STATUS_NEW == self.CUR_STATUS['RS_1'] or self.STATUS_NEW == self.CUR_STATUS['TCP_1']:
                if not self.SendNextCommand('mode_1', self.ui.label_ModeTx):
                    if self.activeConnection == self.CUR_CONNECTION['TCP']:
                        self.STATUS_NEW = self.CUR_STATUS['TCP_RECIEVE']
                    elif self.activeConnection == self.CUR_CONNECTION['RS']:
                        self.STATUS_NEW = self.CUR_STATUS['RS_RECIEVE']
            elif self.STATUS_NEW == self.CUR_STATUS['RS_2'] or self.STATUS_NEW == self.CUR_STATUS['TCP_2']:
                if not self.SendNextCommand('mode_2', self.ui.label_ModeRx):
                    if self.activeConnection == self.CUR_CONNECTION['TCP']:
                        self.STATUS_NEW = self.CUR_STATUS['TCP_RECIEVE']
                    elif self.activeConnection == self.CUR_CONNECTION['RS']:
                        self.STATUS_NEW = self.CUR_STATUS['RS_RECIEVE']
            elif self.STATUS_NEW == self.CUR_STATUS['RS_3'] or self.STATUS_NEW == self.CUR_STATUS['TCP_3']:
                if not self.SendNextCommand('mode_3', self.ui.label_ModeRTLS):
                    if self.STATUS_NEW == self.CUR_STATUS['RS_3']:
                        self.STATUS_NEW = self.CUR_STATUS['RS_RTLS']
                        self.rightAnswer = self.LoadTxPacketByMode('mode_5', '_answer_')
                        self.SendNextCommandDisplayAnswer('mode_5', CUR_RTLS_LABEL, CUR_RTLS_LABEL_DEF_TEXT,
                                                          CUR_RTLS_LABEL_MIDDLE, CUR_RTLS_LABEL_DEF_TEXT_MIDDLE,
                                                          CUR_RTLS_LABEL_DEF_TEXT_END)
                    elif self.STATUS_NEW == self.CUR_STATUS['TCP_3']:
                        self.STATUS_NEW = self.CUR_STATUS['TCP_RTLS']
                        self.rightAnswer = self.LoadTxPacketByMode('mode_5', '_answer_')
                        self.SendNextCommandDisplayAnswer('mode_5', CUR_RTLS_LABEL, CUR_RTLS_LABEL_DEF_TEXT,
                                                          CUR_RTLS_LABEL_MIDDLE, CUR_RTLS_LABEL_DEF_TEXT_MIDDLE,
                                                          CUR_RTLS_LABEL_DEF_TEXT_END)
            elif self.STATUS_NEW == self.CUR_STATUS['RS_4'] or self.STATUS_NEW == self.CUR_STATUS['TCP_4']:
                if not self.SendNextCommand('mode_4', self.ui.label_ModeWork):
                    if self.activeConnection == self.CUR_CONNECTION['TCP']:
                        self.STATUS_NEW = self.CUR_STATUS['TCP_RECIEVE']
                    elif self.activeConnection == self.CUR_CONNECTION['RS']:
                        self.STATUS_NEW = self.CUR_STATUS['RS_RECIEVE']
            elif self.STATUS_NEW == self.CUR_STATUS['RS_RTLS'] or self.STATUS_NEW == self.CUR_STATUS['TCP_RTLS']:
                # проверяем количество уже проведенных измерений
                if self.ui.checkBoxAutoDistance.isChecked():
                    # нужно проверять измерения расстояния автоматически
                    if self.measureCounter >= self.numberDimension:
                        distance = self.sumMiddleDist / self.measureCounter
                        DQF = self.sumMiddleDQF / self.DQFCounter
                        FEC = self.sumMiddleFEC / self.FECCounter
                        if distance >= self.minDistance and distance <= self.maxDistance \
                                and DQF >= self.minDQF \
                                and FEC >= self.minFEC and FEC <= self.maxFEC:
                            QMessageBox(QMessageBox.Warning, 'Результат проверки.',
                                        'Расстояние измеряется правильно. РМА проверена', QMessageBox.Ok).exec()
                            self.result = True
                            self.ui.label_ModeRTLS.setText('Статус выполнения: Успешно')
                        else:
                            QMessageBox(QMessageBox.Warning, 'Результат проверки.',
                                        'Расстояние измеряется с ошибкой. Нужно дополнительно проверить данную РМА.', QMessageBox.Ok).exec()
                            self.result = False
                            self.ui.label_ModeRTLS.setText('Статус выполнения: Ошибка')
                        # больше не ждем приема ответа
                        self.ClearTxCounters()
                        # открываем файл для записи результатов измерения
                        self.now = datetime.datetime.now()
                        filename = '{}_{}_{}.txt'.format(self.now.day, self.now.month, self.now.year)
                        self.file = open(filename, 'at')
                        if self.STATUS_NEW == self.CUR_STATUS['RS_RTLS']:
                            self.STATUS_NEW = self.CUR_STATUS['RS_FILE']
                            self.rightAnswer = self.LoadTxPacketByMode('mode_6', '_answer_')
                            self.SendNextCommandWriteAnswer('mode_6', self.file)
                        elif self.STATUS_NEW == self.CUR_STATUS['TCP_RTLS']:
                            self.STATUS_NEW = self.CUR_STATUS['TCP_FILE']
                            self.rightAnswer = self.LoadTxPacketByMode('mode_6', '_answer_')
                            self.SendNextCommandWriteAnswer('mode_6', self.file)
                        return
                self.SendNextCommandDisplayAnswer('mode_5', CUR_RTLS_LABEL, CUR_RTLS_LABEL_DEF_TEXT,
                                                  CUR_RTLS_LABEL_MIDDLE, CUR_RTLS_LABEL_DEF_TEXT_MIDDLE,
                                                  CUR_RTLS_LABEL_DEF_TEXT_END)
            elif self.STATUS_NEW == self.CUR_STATUS['RS_FILE'] or self.STATUS_NEW == self.CUR_STATUS['TCP_FILE']:
                if not self.SendNextCommandWriteAnswer('mode_6', self.file):
                    if self.activeConnection == self.CUR_CONNECTION['TCP']:
                        self.STATUS_NEW = self.CUR_STATUS['TCP_RECIEVE']
                    elif self.activeConnection == self.CUR_CONNECTION['RS']:
                        self.STATUS_NEW = self.CUR_STATUS['RS_RECIEVE']
                    self.file.close()

        except Exception as EXP:
            out_str = str(EXP)
            QMessageBox(QMessageBox.Warning, 'Ошибка.', out_str , QMessageBox.Ok).exec()
            # Закрытие порта и выключение записи - переход в исходное состояние
            self.STATUS_OLD = self.STATUS_NEW
            self.STATUS_NEW = self.ID2["IDLE"]
            self.CloseRsPushButtonHandler()
            return

    #*********************************************************************
    def SendNextCommand(self, mode, label):
        '''
        отправить следующую команду из группы mode и проконтролировать правильность ответа на прошлую команду
        из этой группы
        :param mode:
        :return:
        '''
        rightAnswer = False
        # Получаем данные из RS
        self.GetRsData()
        # получен успешный ответ
        self.step += 1
        lenData = len(self.dataRx)
        if self.rightAnswer[self.step - 1] == '':
            # поскольку ответа не должно быть, отправляем следующую команду
            if not self.SendStageData( mode, self.step, TX_TIMER):
                # больше не ждем приема ответа
                label.setText('Статус выполнения: Успешно')
                self.ClearTxCounters()
                return False
        else:
            while self.lastLengthRxDataProcessed < lenData:
                data = self.dataRx[self.lastLengthRxDataProcessed]
                self.lastLengthRxDataProcessed += 1
                if data[0] == 'Rx:<<<':
                    if self.CheckCommand(data[1], self.rightAnswer[self.step - 1]):
                        # принятый ответ правильный, отправляем следующую команду
                        rightAnswer = True
                        self.errorCounter = 0
                        if not self.SendStageData(mode, self.step, TX_TIMER):
                            # больше не ждем приема ответа
                            label.setText('Статус выполнения: Успешно')
                            self.ClearTxCounters()
                            return False
        if not rightAnswer:
            self.step -= 1
            self.errorCounter += 1
            if self.errorCounter <= MAX_ERROR_COUNTER:
                self.SendStageData(mode, self.step, TX_TIMER)
                return True
            else:
                self.ClearTxCounters()
                label.setText('Статус выполнения: Ошибка')
                # правильного ответа не было
                QMessageBox(QMessageBox.Warning, 'Нет ответа',
                            'Необходимые данные ответа от РМА не получены', QMessageBox.Ok).exec()
                return False
        return True

    #*********************************************************************
    def SendNextCommandDisplayAnswer(self, mode, label_cur, label_cur_text, label_mid, label_mid_text, label_text_end):
        '''
        отправить следующую команду из группы mode и проконтролировать правильность ответа на прошлую команду
        из этой группы
        :param mode:
        :return:
        '''
        if self.step == 0:
            self.ui.label_ModeRTLS.setText('Статус выполнения: Выполняется')
            self.sumMiddleDist = 0.0
            self.sumMiddleDQF = 0.0
            self.sumMiddleFEC = 0.0
            self.measureCounter = 0
            self.DQFCounter = 0
            self.FECCounter = 0
            timer = TX_RTLS_TIMER * 10
            self.mainTimer.start(timer, self)  # запускаем обработку таймера
            self.step += 1
            return
        # Получаем данные из RS
        self.GetRsData()
        # получен успешный ответ
        lenData = len(self.dataRx)
        while self.lastLengthRxDataProcessed < lenData:
            data = self.dataRx[self.lastLengthRxDataProcessed]
            self.lastLengthRxDataProcessed += 1
            if data[0] == 'Rx:<<<':
                index = self.step - 1
                if self.CheckCommand(data[1], self.rightAnswer[index], CNT_POSITION*2, CNT_POSITION*2 + 8):
                    value = 0
                    if self.step == 4:
                        self.FECCounter += 1
                        # выводим данные от пакета 3
                        i = int(data[1][-6:-4] + data[1][-8:-6], 16)
                        value = toSigned16(i)/100
                        self.sumMiddleFEC = self.sumMiddleFEC + value
                        if self.measureCounter:
                            middleFEC = 0.0 + self.sumMiddleFEC / self.FECCounter
                        else:
                            middleFEC = 0.0
                        cmd = '{}.setText("{}{:.6}{}")'.format(label_mid[index], label_mid_text[index], middleFEC,
                                                               label_text_end[index])
                        eval(cmd)
                    elif self.step == 1:
                        # выводим данные от пакета 1
                        rmsNumber = data[1][-6:-4] + data[1][-8:-6]
                        value = rmsNumber
                        if int(rmsNumber, 16) != self.addressRMS:
                            # ведется обмен не с тем РМС, нужновыдать ошибку и прекратить обмен
                            QMessageBox(QMessageBox.Warning, 'Ошибка.',
                                        'Измеряется расстояние с ошибочным РМС, нужно его проверить.',
                                        QMessageBox.Ok).exec()
                            self.ui.label_ModeRTLS.setText('Статус выполнения: Ошибка')
                            self.STATUS_NEW = self.CUR_STATUS['RS_RECIEVE']
                            # больше не ждем приема ответа
                            self.ClearTxCounters()
                            return
                    elif self.step == 2:
                        self.measureCounter += 1
                        # выводим данные от пакета 1
                        value = int(data[1][-6:-4] + data[1][-8:-6], 16)
                        self.sumMiddleDist = self.sumMiddleDist + value
                        if self.measureCounter:
                            middleDist = 0.0 + self.sumMiddleDist / self.measureCounter
                        else:
                            middleDist = 0.0
                        cmd = '{}.setText("{}{:.6}{}")'.format(label_mid[index], label_mid_text[index], middleDist,
                                                               label_text_end[index])
                        eval(cmd)
                        # увеличиваем количество принятых измерений
                        self.ui.label_ModeRTLS_Counter.setText('Количество измерений: {}'.format(self.measureCounter))
                    elif self.step == 3:
                        self.DQFCounter += 1
                        # выводим данные от пакета 2
                        value = int(data[1][-6:-4], 16)
                        self.sumMiddleDQF = self.sumMiddleDQF + value
                        if self.measureCounter:
                            middleDQF = 0.0 + self.sumMiddleDQF / self.DQFCounter
                        else:
                            middleDQF = 0.0
                        cmd = '{}.setText("{}{:.6}{}")'.format(label_mid[index], label_mid_text[index], middleDQF,
                                                               label_text_end[index])
                        eval(cmd)
                    # принятый ответ правильный, отображаем его и отправляем следующую команду
                    cmd = '{}.setText("{}{}{}")'.format(label_cur[index], label_cur_text[index], value, label_text_end[index])
                    eval(cmd)
        timer = TX_RTLS_TIMER
        if not self.SendStageData(mode, self.step, timer):
            # больше не ждем приема ответа
            self.ClearTxCounters()
            self.SendStageData(mode, self.step, timer)
        self.step += 1

    #*********************************************************************
    def SendNextCommandWriteAnswer(self, mode, file):
        '''
        отправить следующую команду из группы mode и проконтролировать правильность ответа на прошлую команду
        из этой группы
        :param mode:
        :return:
        '''
        rightAnswer = False
        # Получаем данные из RS
        self.GetRsData()
        # получен успешный ответ
        self.step += 1
        lenData = len(self.dataRx)
        if self.rightAnswer[self.step - 1] == '':
            # поскольку ответа не должно быть, отправляем следующую команду
            if not self.SendStageData( mode, self.step, TX_TIMER):
                # больше не ждем приема ответа
                self.ClearTxCounters()
                return False
        else:
            while self.lastLengthRxDataProcessed < lenData:
                data = self.dataRx[self.lastLengthRxDataProcessed]
                self.lastLengthRxDataProcessed += 1
                if data[0] == 'Rx:<<<':
                    if self.CheckCommand(data[1], self.rightAnswer[self.step - 1], CNT_POSITION*2, CNT_POSITION*2):
                        # принятый ответ правильный, отправляем следующую команду
                        rightAnswer = True
                        self.errorCounter = 0
                        # записываем в файл вычитанное значение
                        if (data[1][ID_START_INDEX:ID_END_INDEX]) == ID_VERSION or \
                           (data[1][ID_START_INDEX:ID_END_INDEX]) == ID_DATA or \
                           (data[1][ID_START_INDEX:ID_END_INDEX]) == ID_TIME :
                            text = Convert_HexStr_to_Str(data[1], DATA_START_INDEX, DATA_END_INDEX) + '\n'
                            file.write(text)
                        if (data[1][ID_START_INDEX:ID_END_INDEX]) == ID_ID:
                            text = self.ParseID(data[1], DATA_START_INDEX, DATA_END_INDEX) + '\n'
                            file.write(text)
                        if not self.SendStageData(mode, self.step, TX_TIMER):
                            # записываем все ранее измеренные значения
                            if self.FECCounter:
                                middleFEC = 0.0 + self.sumMiddleFEC / self.FECCounter
                                file.write(str('     FEC: {:.6} границы от {} до {}\n'.format(middleFEC, self.minFEC, self.maxFEC)))
                            if self.DQFCounter:
                                middleDQF = 0.0 + self.sumMiddleDQF / self.DQFCounter
                                file.write(str('     DQF: {:.6} граница от {}\n'.format(middleDQF, self.minDQF)))
                            if self.measureCounter:
                                middleDist = 0.0 + self.sumMiddleDist / self.measureCounter
                                file.write(str('     Dist: {:.6} границы от {} до {}\n'.format(middleDist, self.minDistance, self.maxDistance)))
                                file.write(str('     Количество измерений: {}\n'.format(self.measureCounter)))
                                if self.result:
                                    file.write(str('     Результат проверки РМА в {}:{}: Успешно\n\n'.format(self.now.hour, self.now.minute)))
                                    self.result = False
                                else:
                                    file.write(str('     Результат проверки РМА в {}:{}: Ошибка\n\n'.format(self.now.hour, self.now.minute)))

                            # больше не ждем приема ответа
                            self.ClearTxCounters()
                            return False
        if not rightAnswer:
            self.step -= 1
            self.errorCounter += 1
            if self.errorCounter <= MAX_ERROR_COUNTER:
                self.SendStageData(mode, self.step, TX_TIMER)
                return True
            else:
                self.ClearTxCounters()
                # правильного ответа не было
                QMessageBox(QMessageBox.Warning, 'Нет ответа',
                            'Необходимые данные ответа от РМА не получены', QMessageBox.Ok).exec()
                return False
        return True

    #*********************************************************************
    def ParseID(self, data, startIndex, endIndex):
        retval = ''
        if endIndex > 0:
            i = endIndex - 2
        else:
            i = len(data) + endIndex - 2
        while (i >= startIndex):
            retval += data[i:i + 2]
            i -= 2
        return retval

    #*********************************************************************
    def ClearTxCounters(self):
        self.step = 0
        self.errorCounter = 0
        self.dataRx.clear()
        self.dataTx.clear()
        self.lastLengthRxDataProcessed = 0
        self.lastLengthRxData = 0

    #*********************************************************************
    def UpdateTextTextEdit(self):
        '''
        вывод принятых данных в TextEdit
        :return:
        '''
        try:
            if self.ui.checkBoxShowRxDataStr.isChecked() | self.ui.checkBoxShowRxDataHex.isChecked():
                lenData = len(self.dataRx)
                if self.lastLengthRxData != lenData:
                    while self.lastLengthRxData < lenData:
                        self.lastLengthRxData += 1
                        if self.ui.checkBoxShowRxDataStr.isChecked() and self.ui.checkBoxShowRxDataHex.isChecked():
                            self.ui.plainTextEdit.appendPlainText('{} Str: {}\nHex: {}'.format(
                                self.dataRx[self.lastLengthRxData - 1][0],
                                self.dataRx[self.lastLengthRxData - 1][2],
                                self.dataRx[self.lastLengthRxData - 1][1]))
                        elif self.ui.checkBoxShowRxDataStr.isChecked():
                            self.ui.plainTextEdit.appendPlainText('{} Str: {}'.format(
                                self.dataRx[self.lastLengthRxData - 1][0],
                                self.dataRx[self.lastLengthRxData - 1][2]))
                        elif self.ui.checkBoxShowRxDataHex.isChecked():
                            self.ui.plainTextEdit.appendPlainText('{} Hex: {}'.format(
                                self.dataRx[self.lastLengthRxData - 1][0],
                                self.dataRx[self.lastLengthRxData - 1][1]))
        except Exception as EXP:
            QMessageBox(QMessageBox.Critical, 'Ошибка', str(EXP), QMessageBox.Ok).exec()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = RMA_T0_Test()
    myapp.show()
    sys.exit(app.exec_())

