SET = True

# *********************************************************************
def ChangeRsButtonsIdle(ui):
    '''
    # активация кнопок после выбора порта и скорости
    :param ui:
    :param xls_filename:
    :return:
    '''
    # изменяем назначение кнопки прошить
    ui.pushButton_open_COM.setDisabled(SET)        #де-активируем кнопку открытие порта
    ui.pushButton_close_COM.setEnabled(SET)        #активируем кнопку закрытие порта
    ui.comboBox_COM.setDisabled(SET)               #де-активируем выбор порта
    ui.comboBox_Baudrate.setDisabled(SET)          #де-активируем выбор скорости

#*********************************************************************
def ChangeActiveButtonsRsClose(ui):
    '''
    де-активация всех кнопок
    :param ui:
    :return:
    '''
    ui.pushButton_open_COM.setDisabled(SET)           #де-активируем кнопку открытие порта
    ui.pushButton_close_COM.setDisabled(SET)          #де-активируем кнопку закрытие порта
    ui.comboBox_COM.setDisabled(SET)                  #де-активируем выбор порта
    ui.comboBox_Baudrate.setDisabled(SET)             #де-активируем выбор скорости

#*********************************************************************
def ChangeActiveButtonsRsSelected(ui):
    '''
    де-активация кнопок после выбора порта
    :param ui:
    :return:
    '''
    ui.pushButton_open_COM.setEnabled(SET)            #активируем кнопку открытие порта
    ui.pushButton_close_COM.setDisabled(SET)          #де-активируем кнопку закрытие порта
    ui.comboBox_COM.setEnabled(SET)                   #активируем выбор порта
    ui.comboBox_Baudrate.setEnabled(SET)              #активируем выбор скорости

#*********************************************************************
def ChangeButtonsRsSend(ui):
    '''
    # изменить значение кнопок для передачи
    :param ui:
    :return:
    '''
    #настраиваем видимость кнопок
    ui.pushButton_open_COM.setDisabled(SET)      #де-активируем кнопку открытие порта
    ui.pushButton_close_COM.setDisabled(SET)     #де-активируем кнопку закрытие порта
    ui.comboBox_COM.setDisabled(SET)             #де-активируем выбор порта
    ui.comboBox_Baudrate.setDisabled(SET)        #де-активируем выбор скорости

# *********************************************************************
def ChangeButtonsTCPServerConnected(ui):
    '''
    активируем и деактивируем кнопки для открытого TCP сервера
    :param ui:
    :return:
    '''
    ui.pushButton_open_TCP_Server.setDisabled(SET)
    ui.pushButton_close_TCP_Server.setEnabled(SET)
    ui.lineEdit_TCP_Server_IP_port.setDisabled(SET)
    ui.comboBox_IP_Address_TCP_Server.setDisabled(SET)

# *********************************************************************
def ChangeButtonsTCPServerDisconnected(ui):
    '''
    активируем и деактивируем кнопки для закрытого UDP сервера
    :param ui:
    :return:
    '''
    ui.pushButton_open_TCP_Server.setEnabled(SET)
    ui.pushButton_close_TCP_Server.setDisabled(SET)
    ui.lineEdit_TCP_Server_IP_port.setEnabled(SET)
    ui.comboBox_IP_Address_TCP_Server.setEnabled(SET)

# *********************************************************************
def ChangeButtonsTCPClientConnected(ui):
    '''
    активируем и деактивируем кнопки при подключении клиентом по TCP к серверу
    :param ui:
    :return:
    '''
    ui.pushButton_open_TCP_Client.setDisabled(SET)
    ui.pushButton_close_TCP_Client.setEnabled(SET)
    ui.lineEdit_TCP_IP_Addr.setDisabled(SET)
    ui.lineEdit_TCP_Client_IP_Port.setDisabled(SET)

#*********************************************************************
def ChangeButtonsTCPClientDisconnected(ui):
    '''
    активируем и деактивируем кнопки при отключении клиента по TCP от сервера
    :param ui:
    :return:
    '''
    ui.pushButton_open_TCP_Client.setEnabled(SET)
    ui.pushButton_close_TCP_Client.setDisabled(SET)
    ui.lineEdit_TCP_IP_Addr.setEnabled(SET)
    ui.lineEdit_TCP_Client_IP_Port.setEnabled(SET)

# *********************************************************************
def ChangeTCPButtonsIdle(ui, xls_filename):
    '''
    # активация кнопок после нажатия кнопки отправить
    :param ui:
    :param xls_filename:
    :return:
    '''
    # изменяем назначение кнопки прошить
    ui.pushButton_Send.setText("Отправить данные")
    ui.pushButton_Choice_File.setEnabled(SET)      #активируем кнопку выбор файла
    ui.pushButton_close_TCP_Client.setEnabled(SET)        #де-активируем кнопку открытие порта
    ui.checkBoxXlsSave.setEnabled(SET)
    if xls_filename and xls_filename[0] != '':
        ui.pushButton_Send.setEnabled(SET)
        ui.pushButton_Send_One_Pack.setEnabled(SET)

#*********************************************************************
def ChangeButtonsTCPSend(ui):
    '''
    # изменить значение кнопок для передачи
    :param ui:
    :return:
    '''
    # изменяем назначение кнопки прошить
    ui.pushButton_Send.setText("Прервать отправку")
    #настраиваем видимость кнопок
    ui.pushButton_Choice_File.setDisabled(SET)   #де-активируем кнопку выбор файла
    ui.pushButton_close_TCP_Client.setDisabled(SET)      #де-активируем кнопку открытие порта
    ui.pushButton_open_TCP_Client.setDisabled(SET)     #де-активируем кнопку закрытие порта
    ui.checkBoxXlsSave.setDisabled(SET)

#*********************************************************************
def EnableAllButtonsRS(ui):
    '''
    деактивируем все кнопки в RS
    :param ui:
    :return:
    '''
    ui.pushButton_open_COM.setEnabled(SET)
    ui.pushButton_close_COM.setDisabled(SET)

#*********************************************************************
def EnableAllButtonsMode(ui):
    '''
    деактивируем все кнопки в RS
    :param ui:
    :return:
    '''
    ui.pushButton_Mode_TX.setEnabled(SET)
    ui.pushButton_Mode_RX.setEnabled(SET)
    ui.pushButton_Mode_RTLS.setEnabled(SET)
    ui.pushButton_Mode_Work.setEnabled(SET)

#*********************************************************************
def DisableAllButtonsRS(ui):
    '''
    деактивируем все кнопки в RS
    :param ui:
    :return:
    '''
    ui.pushButton_open_COM.setDisabled(SET)
    ui.pushButton_close_COM.setDisabled(SET)

#*********************************************************************
def DisableAllButtonsMode(ui):
    '''
    деактивируем все кнопки в RS
    :param ui:
    :return:
    '''
    ui.pushButton_Mode_TX.setDisabled(SET)
    ui.pushButton_Mode_RX.setDisabled(SET)
    ui.pushButton_Mode_RTLS.setDisabled(SET)
    ui.pushButton_Mode_Work.setDisabled(SET)

#*********************************************************************
def DisableAllButtonsTCP(ui):
    '''
    деактивируем все кнопки в UDP
    :param ui:
    :return:
    '''
    ui.pushButton_open_TCP_Client.setDisabled(SET)
    ui.pushButton_close_TCP_Client.setDisabled(SET)

#*********************************************************************
def EnableAllButtonsTCP(ui):
    '''
    деактивируем все кнопки в UDP
    :param ui:
    :return:
    '''
    ui.pushButton_open_TCP_Client.setEnabled(SET)
    ui.pushButton_close_TCP_Client.setDisabled(SET)

#*********************************************************************
def ClearLabelStatus(ui):
    '''
    возврят к исходному значению всех надписей статусов выполнения
    :param ui:
    :return:
    '''
    ui.label_ModeWork.setText('Статус выполнения:')
    ui.label_ModeTx.setText('Статус выполнения:')
    ui.label_ModeRx.setText('Статус выполнения:')
    ui.label_ModeRTLS.setText('Статус выполнения:')

