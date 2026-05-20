import sys
import hashlib
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
import psycopg2
import re
from psycopg2 import sql

DB_CONFIG = {
    'dbname': 'postgres',              # имя вашей базы данных (обычно postgres)
    'user': 'postgres',
    'password': 'a4815162342A',
    'host': 'localhost',
    'port': 5432,
    'client_encoding': 'utf8'          # исправляет UnicodeDecodeError
}

current_user_id = None

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """Создаёт таблицу users, если её ещё нет."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            login VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password):
    """Возвращает SHA-256 хеш пароля."""
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(login_or_email, password):
    """
    Проверяет логин/пароль.
    Если введён email (содержит '@'), ищет по email.
    Иначе ищет по логину. Регистр не учитывается.
    """
    global current_user_id
    conn = get_db_connection()
    cur = conn.cursor()
    pwd_hash = hash_password(password)

    if '@' in login_or_email:
        # поиск по email (без учёта регистра)
        cur.execute(
            "SELECT id FROM users WHERE LOWER(email) = LOWER(%s) AND password_hash = %s",
            (login_or_email, pwd_hash)
        )
    else:
        # поиск по логину (без учёта регистра)
        cur.execute(
            "SELECT id FROM users WHERE LOWER(login) = LOWER(%s) AND password_hash = %s",
            (login_or_email, pwd_hash)
        )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        current_user_id = row[0]
        return True
    return False

def do_registration():
    username = ui_register.line_User.text().strip()
    password = ui_register.line_Password.text().strip()
    email = ui_register.line_Email.text().strip()
    if not username or not password:
        QMessageBox.warning(register_window, "Ошибка", "Логин и пароль обязательны.")
        return
    if not email:
        QMessageBox.warning(register_window, "Ошибка", "Введите Email")
        return
    success, message = register_user(username, password, email)
    if success:
        QMessageBox.information(register_window, "Успех", message)
        register_window.hide()
        login_window.show()
        ui_register.line_User.clear()
        ui_register.line_Password.clear()
        ui_register.line_Email.clear()
    else:
        QMessageBox.critical(register_window, "Ошибка", message)

def register_user(username, password, email):
    """
    Регистрирует пользователя.
    Проверяет уникальность логина и email (без учёта регистра).
    Проверяет формат email, если он указан.
    Возвращает (True/False, сообщение).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Проверка уникальности логина (без учёта регистра)
    cur.execute("SELECT id FROM users WHERE LOWER(login) = LOWER(%s)", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False, "Пользователь с таким логином уже существует."

    email = email.strip() if email else ''
    if email:
        # Проверка формата email
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            cur.close()
            conn.close()
            return False, "Некорректный формат email."

        # Проверка уникальности email (без учёта регистра)
        cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Пользователь с таким email уже существует."

    pwd_hash = hash_password(password)
    try:
        cur.execute(
            "INSERT INTO users (login, password_hash, email) VALUES (%s, %s, %s)",
            (username, pwd_hash, email)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Ошибка регистрации: {e}"

    cur.close()
    conn.close()
    return True, "Регистрация прошла успешно!"

class Ui_Register(object):
    def setupUi(self, Register):
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
        MainWindow.resize(365, 317)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Income = QtWidgets.QLineEdit(self.centralwidget)
        self.Income.setGeometry(QtCore.QRect(160, 50, 161, 31))
        self.Income.setText("")
        self.Income.setObjectName("Income")
        self.Lable_sum = QtWidgets.QLabel(self.centralwidget)
        self.Lable_sum.setGeometry(QtCore.QRect(30, 60, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_sum.setFont(font)
        self.Lable_sum.setObjectName("Lable_sum")
        self.Lable_3 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_3.setGeometry(QtCore.QRect(30, 100, 121, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_3.setFont(font)
        self.Lable_3.setObjectName("Lable_3")
        self.pushButton_Save = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Save.setGeometry(QtCore.QRect(100, 130, 111, 31))
        self.pushButton_Save.setObjectName("pushButton_Save")
        self.Lable_1 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_1.setGeometry(QtCore.QRect(30, 190, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_1.setFont(font)
        self.Lable_1.setObjectName("Lable_1")
        self.Lable_2 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_2.setGeometry(QtCore.QRect(30, 230, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_2.setFont(font)
        self.Lable_2.setObjectName("Lable_2")
        self.label_Sum = QtWidgets.QLabel(self.centralwidget)
        self.label_Sum.setGeometry(QtCore.QRect(160, 190, 141, 21))
        self.label_Sum.setText("")
        self.label_Sum.setObjectName("label_Sum")
        self.label_SumTax = QtWidgets.QLabel(self.centralwidget)
        self.label_SumTax.setGeometry(QtCore.QRect(160, 230, 141, 21))
        self.label_SumTax.setText("")
        self.label_SumTax.setObjectName("label_SumTax")
        self.label_TaxProc = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxProc.setGeometry(QtCore.QRect(100, 100, 141, 21))
        self.label_TaxProc.setText("")
        self.label_TaxProc.setObjectName("label_TaxProc")
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
        self.Lable_3.setText(_translate("MainWindow", "Налог:"))
        self.pushButton_Save.setText(_translate("MainWindow", "Сохранить"))
        self.Lable_1.setText(_translate("MainWindow", "Сумма дохода:"))
        self.Lable_2.setText(_translate("MainWindow", "Сумма налога:"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    init_db()

    login_window = QtWidgets.QMainWindow()
    register_window = QtWidgets.QMainWindow()
    MainWindow_window = QtWidgets.QMainWindow()

    ui_login = Ui_Login()
    ui_login.setupUi(login_window)

    ui_register = Ui_Register()
    ui_register.setupUi(register_window)

    ui_MainWindow = Ui_MainWindow()
    ui_MainWindow.setupUi(MainWindow_window)

    MainWindow_window.hide()
    register_window.hide()
    login_window.show()

    def try_login():
        username = ui_login.line_User.text().strip()
        password = ui_login.line_Password.text().strip()
        if not username or not password:
            QMessageBox.warning(login_window, "Ошибка", "Введите логин/email и пароль.")
            return
        if login_user(username, password):
            MainWindow_window.show()
            login_window.hide()
        else:
            QMessageBox.critical(login_window, "Ошибка", "Неверный логин/email или пароль.")

    def go_to_register():
        login_window.hide()
        register_window.show()

    def do_registration():
        username = ui_register.line_User.text().strip()
        password = ui_register.line_Password.text().strip()
        email = ui_register.line_Email.text().strip()
        if not username or not password:
            QMessageBox.warning(register_window, "Ошибка", "Логин и пароль обязательны.")
            return
        success, message = register_user(username, password, email)
        if success:
            QMessageBox.information(register_window, "Успех", message)
            register_window.hide()
            login_window.show()
            ui_register.line_User.clear()
            ui_register.line_Password.clear()
            ui_register.line_Email.clear()
        else:
            QMessageBox.critical(register_window, "Ошибка", message)

    def back_to_login():
        register_window.hide()
        login_window.show()

    ui_login.pushButton_Login.clicked.connect(try_login)
    ui_login.pushButton_Cancel.clicked.connect(go_to_register)
    ui_register.pushButton_Cancel.clicked.connect(do_registration)

    MainWindow_window.closeEvent = lambda event: QtWidgets.qApp.quit()

    sys.exit(app.exec_())
