import sys
from PyQt5 import QtWidgets, QtCore, QtGui

class Ui_Register(object):
    def setupUi(self, Register):
        # ... весь ваш код без изменений ...
        Register.setObjectName("Register")
        Register.resize(300, 300)
        self.centralwidget = QtWidgets.QWidget(Register)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(0, -20, 300, 300))
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.Lable_User = QtWidgets.QLabel(self.groupBox)
        self.Lable_User.setGeometry(QtCore.QRect(30, 20, 101, 51))
        self.Lable_User.setObjectName("Lable_User")
        self.label_Password = QtWidgets.QLabel(self.groupBox)
        self.label_Password.setGeometry(QtCore.QRect(30, 60, 101, 51))
        self.label_Password.setObjectName("label_Password")
        self.line_User = QtWidgets.QLineEdit(self.groupBox)
        self.line_User.setGeometry(QtCore.QRect(90, 40, 171, 20))
        self.line_User.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.line_User.setObjectName("line_User")
        self.line_Password = QtWidgets.QLineEdit(self.groupBox)
        self.line_Password.setGeometry(QtCore.QRect(82, 80, 181, 20))
        self.line_Password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.line_Password.setObjectName("line_Password")
        self.pushButton_Cancel = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_Cancel.setGeometry(QtCore.QRect(90, 190, 101, 71))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_Cancel.setFont(font)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        self.line_Email = QtWidgets.QLineEdit(self.groupBox)
        self.line_Email.setGeometry(QtCore.QRect(82, 120, 181, 20))
        self.line_Email.setText("")
        self.line_Email.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.line_Email.setObjectName("line_Email")
        self.label_Email = QtWidgets.QLabel(self.groupBox)
        self.label_Email.setGeometry(QtCore.QRect(30, 100, 101, 51))
        self.label_Email.setObjectName("label_Email")
        Register.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(Register)
        self.statusbar.setObjectName("statusbar")
        Register.setStatusBar(self.statusbar)

        self.retranslateUi(Register)
        QtCore.QMetaObject.connectSlotsByName(Register)


    def retranslateUi(self, Register):
        _translate = QtCore.QCoreApplication.translate
        Register.setWindowTitle(_translate("Register", "MainWindow"))
        self.Lable_User.setText(_translate("Register", "User Name:"))
        self.label_Password.setText(_translate("Register", "Password:"))
        self.pushButton_Cancel.setText(_translate("Register", "Registration"))
        self.label_Email.setText(_translate("Register", "Email"))

class Ui_Login(object):
    def setupUi(self, Login):
        Login.setObjectName("Login")
        Login.resize(300, 301)
        self.centralwidget = QtWidgets.QWidget(Login)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(0, 0, 300, 300))
        self.groupBox.setStyleSheet("")
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.Lable_User = QtWidgets.QLabel(self.groupBox)
        self.Lable_User.setGeometry(QtCore.QRect(30, 20, 101, 51))
        self.Lable_User.setObjectName("Lable_User")
        self.label_Password = QtWidgets.QLabel(self.groupBox)
        self.label_Password.setGeometry(QtCore.QRect(30, 60, 101, 51))
        self.label_Password.setObjectName("label_Password")
        self.line_User = QtWidgets.QLineEdit(self.groupBox)
        self.line_User.setGeometry(QtCore.QRect(90, 40, 171, 20))
        self.line_User.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.line_User.setObjectName("line_User")
        self.line_Password = QtWidgets.QLineEdit(self.groupBox)
        self.line_Password.setGeometry(QtCore.QRect(82, 80, 181, 20))
        self.line_Password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.line_Password.setObjectName("line_Password")
        self.pushButton_Login = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_Login.setGeometry(QtCore.QRect(20, 150, 101, 71))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_Login.setFont(font)
        self.pushButton_Login.setObjectName("pushButton_Login")
        self.pushButton_Cancel = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_Cancel.setGeometry(QtCore.QRect(160, 150, 101, 71))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_Cancel.setFont(font)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        Login.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(Login)
        self.statusbar.setObjectName("statusbar")
        Login.setStatusBar(self.statusbar)

        self.retranslateUi(Login)
        QtCore.QMetaObject.connectSlotsByName(Login)

    def retranslateUi(self, Login):
        _translate = QtCore.QCoreApplication.translate
        Login.setWindowTitle(_translate("Login", "MainWindow"))
        self.Lable_User.setText(_translate("Login", "User Name:"))
        self.label_Password.setText(_translate("Login", "Password:"))
        self.pushButton_Login.setText(_translate("Login", "Login"))
        self.pushButton_Cancel.setText(_translate("Login", "Registration"))

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(829, 317)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.AmountTax = QtWidgets.QLineEdit(self.centralwidget)
        self.AmountTax.setGeometry(QtCore.QRect(160, 50, 161, 31))
        self.AmountTax.setText("")
        self.AmountTax.setObjectName("AmountTax")
        self.TableTax = QtWidgets.QTableView(self.centralwidget)
        self.TableTax.setGeometry(QtCore.QRect(380, 70, 381, 151))
        self.TableTax.setObjectName("TableTax")
        self.Lable_sum = QtWidgets.QLabel(self.centralwidget)
        self.Lable_sum.setGeometry(QtCore.QRect(30, 60, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_sum.setFont(font)
        self.Lable_sum.setObjectName("Lable_sum")
        self.Lable_Tax = QtWidgets.QLabel(self.centralwidget)
        self.Lable_Tax.setGeometry(QtCore.QRect(30, 100, 121, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_Tax.setFont(font)
        self.Lable_Tax.setObjectName("Lable_Tax")
        self.Tax = QtWidgets.QLineEdit(self.centralwidget)
        self.Tax.setGeometry(QtCore.QRect(100, 90, 161, 31))
        self.Tax.setText("")
        self.Tax.setObjectName("Tax")
        self.Lable_Table = QtWidgets.QLabel(self.centralwidget)
        self.Lable_Table.setGeometry(QtCore.QRect(380, 40, 161, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_Table.setFont(font)
        self.Lable_Table.setObjectName("Lable_Table")
        self.pushButton_Save = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Save.setGeometry(QtCore.QRect(100, 130, 111, 31))
        self.pushButton_Save.setObjectName("pushButton_Save")
        self.Lable_sumAmount = QtWidgets.QLabel(self.centralwidget)
        self.Lable_sumAmount.setGeometry(QtCore.QRect(30, 190, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_sumAmount.setFont(font)
        self.Lable_sumAmount.setObjectName("Lable_sumAmount")
        self.Lable_sumTax = QtWidgets.QLabel(self.centralwidget)
        self.Lable_sumTax.setGeometry(QtCore.QRect(30, 230, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_sumTax.setFont(font)
        self.Lable_sumTax.setObjectName("Lable_sumTax")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(160, 190, 141, 21))
        self.label.setText("")
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(160, 230, 141, 21))
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.Lable_sum.setText(_translate("MainWindow", "Введите сумму:"))
        self.Lable_Tax.setText(_translate("MainWindow", "Налог:"))
        self.Lable_Table.setText(_translate("MainWindow", "Таблица налогов:"))
        self.pushButton_Save.setText(_translate("MainWindow", "Сохранить"))
        self.Lable_sumAmount.setText(_translate("MainWindow", "Сумма дохода:"))
        self.Lable_sumTax.setText(_translate("MainWindow", "Сумма налога:"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # 1. Создаём оба окна как QMainWindow
    login_window = QtWidgets.QMainWindow()
    register_window = QtWidgets.QMainWindow()

    # 2. Настраиваем интерфейсы
    ui_login = Ui_Login()
    ui_login.setupUi(login_window)

    ui_register = Ui_Register()
    ui_register.setupUi(register_window)

    # 3. Прячем окно регистрации, показываем только окно входа
    register_window.hide()
    login_window.show()

    # 4. Переход: при нажатии «Registration» в окне входа
    def go_to_register():
        login_window.hide()          # или login_window.showMinimized() если нужно свернуть в панель
        register_window.show()

    ui_login.pushButton_Cancel.clicked.connect(go_to_register)

    # 5. (Опционально) Обратный переход: при закрытии окна регистрации – показать вход
    #    Можно повесить на кнопку «Registration» в форме регистрации (после успешной регистрации)
    def back_to_login():
        register_window.hide()
        login_window.show()

    ui_register.pushButton_Cancel.clicked.connect(back_to_login)   # теперь эта кнопка возвращает назад

    # Если нужно, чтобы при закрытии регистрации (крестик) тоже возвращало:
    # register_window.closeEvent = lambda event: (back_to_login(), event.ignore())
    # Но лучше переопределить в подклассе.

    sys.exit(app.exec_())
