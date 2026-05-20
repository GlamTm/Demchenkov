import sys
import hashlib
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
import psycopg2
import re
from psycopg2 import sql

DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'a4815162342A',
    'host': 'localhost',
    'port': 5432,
    'client_encoding': 'utf8'
}

current_user_id = None

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS users
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    login
                    VARCHAR
                (
                    50
                ) UNIQUE NOT NULL,
                    password_hash VARCHAR
                (
                    64
                ) NOT NULL,
                    email VARCHAR
                (
                    100
                ),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS income
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    user_id
                    INTEGER
                    REFERENCES
                    users
                (
                    id
                ) ON DELETE CASCADE,
                    amount NUMERIC
                (
                    12,
                    2
                ) NOT NULL,
                    tax NUMERIC
                (
                    12,
                    2
                ) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS user_totals
                (
                    user_id
                    INTEGER
                    PRIMARY
                    KEY
                    REFERENCES
                    users
                (
                    id
                ) ON DELETE CASCADE,
                    total_income NUMERIC
                (
                    12,
                    2
                ) NOT NULL DEFAULT 0,
                    total_tax NUMERIC
                (
                    12,
                    2
                ) NOT NULL DEFAULT 0
                    );
                """)
    conn.commit()
    cur.close()
    conn.close()



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(login_or_email, password):

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE LOWER(login) = LOWER(%s)", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False, "Пользователь с таким логином уже существует."
    email = email.strip() if email else ''
    if email:
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            cur.close()
            conn.close()
            return False, "Некорректный формат email."
        cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "Пользователь с таким email уже существует."
    pwd_hash = hash_password(password)
    try:
        # Вставляем пользователя и получаем его id
        cur.execute(
            "INSERT INTO users (login, password_hash, email) VALUES (%s, %s, %s) RETURNING id",
            (username, pwd_hash, email)
        )
        user_id = cur.fetchone()[0]
        # Создаём запись в user_totals с нулями
        cur.execute("INSERT INTO user_totals (user_id) VALUES (%s)", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Ошибка регистрации: {e}"
    cur.close()
    conn.close()
    return True, "Регистрация прошла успешно!"

def calculate_tax(income):
    """Прогрессивный НДФЛ: 13% до 5 млн, 15% свыше."""
    if income <= 5_000_000:
        tax = income * 0.13
    else:
        tax = 5_000_000 * 0.13 + (income - 5_000_000) * 0.15
    return tax

def save_income(amount):
    """Сохраняет запись о доходе и налоге в БД для текущего пользователя."""
    global current_user_id
    if current_user_id is None:
        return False, "Пользователь не авторизован."
    tax = calculate_tax(amount)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO income (user_id, amount, tax) VALUES (%s, %s, %s)",
            (current_user_id, amount, tax)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"Ошибка сохранения: {e}"
    cur.close()
    conn.close()
    return True, "Доход сохранён."

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
        MainWindow.resize(400, 380)                     # увеличил высоту
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
        # Налог (процент) – существующий label
        self.label_TaxProc = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxProc.setGeometry(QtCore.QRect(100, 100, 141, 21))
        self.label_TaxProc.setText("")
        self.label_TaxProc.setObjectName("label_TaxProc")
        # Новые элементы: Сумма налога в рублях
        self.label_TaxRubTitle = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxRubTitle.setGeometry(QtCore.QRect(30, 125, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_TaxRubTitle.setFont(font)
        self.label_TaxRubTitle.setObjectName("label_TaxRubTitle")
        self.label_TaxRubValue = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxRubValue.setGeometry(QtCore.QRect(160, 125, 161, 21))
        self.label_TaxRubValue.setText("")
        self.label_TaxRubValue.setObjectName("label_TaxRubValue")
        # Новые элементы: Чистый доход после налога
        self.label_NetIncomeTitle = QtWidgets.QLabel(self.centralwidget)
        self.label_NetIncomeTitle.setGeometry(QtCore.QRect(30, 150, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_NetIncomeTitle.setFont(font)
        self.label_NetIncomeTitle.setObjectName("label_NetIncomeTitle")
        self.label_NetIncomeValue = QtWidgets.QLabel(self.centralwidget)
        self.label_NetIncomeValue.setGeometry(QtCore.QRect(160, 150, 161, 21))
        self.label_NetIncomeValue.setText("")
        self.label_NetIncomeValue.setObjectName("label_NetIncomeValue")
        # Кнопка "Сохранить" (сдвинута вниз)
        self.pushButton_Save = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Save.setGeometry(QtCore.QRect(100, 180, 111, 31))
        self.pushButton_Save.setObjectName("pushButton_Save")
        # Итоговые накопленные суммы
        self.Lable_1 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_1.setGeometry(QtCore.QRect(30, 230, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_1.setFont(font)
        self.Lable_1.setObjectName("Lable_1")
        self.Lable_2 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_2.setGeometry(QtCore.QRect(30, 270, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_2.setFont(font)
        self.Lable_2.setObjectName("Lable_2")
        self.label_Sum = QtWidgets.QLabel(self.centralwidget)
        self.label_Sum.setGeometry(QtCore.QRect(160, 230, 141, 21))
        self.label_Sum.setText("0.00")
        self.label_Sum.setObjectName("label_Sum")
        self.label_SumTax = QtWidgets.QLabel(self.centralwidget)
        self.label_SumTax.setGeometry(QtCore.QRect(160, 270, 141, 21))
        self.label_SumTax.setText("0.00")
        self.label_SumTax.setObjectName("label_SumTax")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Налоговый учёт"))
        self.Lable_sum.setText(_translate("MainWindow", "Введите сумму:"))
        self.Lable_3.setText(_translate("MainWindow", "Налог:"))
        self.pushButton_Save.setText(_translate("MainWindow", "Сохранить"))
        self.Lable_1.setText(_translate("MainWindow", "Сумма дохода:"))
        self.Lable_2.setText(_translate("MainWindow", "Сумма налога:"))
        self.label_TaxRubTitle.setText(_translate("MainWindow", "Налог, руб.:"))
        self.label_NetIncomeTitle.setText(_translate("MainWindow", "Доход :"))

def get_totals():
    """Возвращает (суммарный_доход, суммарный_налог) для текущего пользователя."""
    global current_user_id
    if current_user_id is None:
        return 0.0, 0.0
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(amount), 0), COALESCE(SUM(tax), 0) FROM income WHERE user_id = %s",
        (current_user_id,)
    )
    total_income, total_tax = cur.fetchone()
    cur.close()
    conn.close()
    return float(total_income), float(total_tax)


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

    # ---------------- Логика главного окна ----------------
    def update_tax_display():
        """Вычисляет налог для введённой суммы и показывает процент, сумму налога, чистый доход."""
        text = ui_MainWindow.Income.text().strip()
        if not text:
            ui_MainWindow.label_TaxProc.setText("")
            ui_MainWindow.label_TaxRubValue.setText("")
            ui_MainWindow.label_NetIncomeValue.setText("")
            return
        try:
            income = float(text)
            if income < 0:
                ui_MainWindow.label_TaxProc.setText("")
                ui_MainWindow.label_TaxRubValue.setText("")
                ui_MainWindow.label_NetIncomeValue.setText("")
                return
            tax = calculate_tax(income)
            net_income = income - tax
            if income <= 5_000_000:
                rate = "13%"
            else:
                rate = "13% на 5 млн + 15% сверх"
            ui_MainWindow.label_TaxProc.setText(rate)
            ui_MainWindow.label_TaxRubValue.setText(f"{tax:,.2f}")
            ui_MainWindow.label_NetIncomeValue.setText(f"{net_income:,.2f}")
        except ValueError:
            ui_MainWindow.label_TaxProc.setText("")
            ui_MainWindow.label_TaxRubValue.setText("")
            ui_MainWindow.label_NetIncomeValue.setText("")

    def save_and_update():
        """Сохраняет текущий доход и обновляет итоговые суммы."""
        text = ui_MainWindow.Income.text().strip()
        if not text:
            QMessageBox.warning(MainWindow_window, "Ошибка", "Введите сумму дохода.")
            return
        try:
            income = float(text)
            if income <= 0:
                QMessageBox.warning(MainWindow_window, "Ошибка", "Сумма должна быть положительной.")
                return
        except ValueError:
            QMessageBox.warning(MainWindow_window, "Ошибка", "Некорректная сумма.")
            return

        success, msg = save_income(income)
        if success:
            # Обновить итоговые метки
            total_income, total_tax = get_totals()
            ui_MainWindow.label_Sum.setText(f"{total_income:,.2f}")
            ui_MainWindow.label_SumTax.setText(f"{total_tax:,.2f}")
            ui_MainWindow.Income.clear()
            ui_MainWindow.label_TaxProc.clear()
            QMessageBox.information(MainWindow_window, "Успех", msg)
        else:
            QMessageBox.critical(MainWindow_window, "Ошибка", msg)
        ui_MainWindow.label_TaxRubValue.clear()
        ui_MainWindow.label_NetIncomeValue.clear()

    def load_totals():
        """Загружает накопленные суммы и отображает их."""
        total_income, total_tax = get_totals()
        ui_MainWindow.label_Sum.setText(f"{total_income:,.2f}")
        ui_MainWindow.label_SumTax.setText(f"{total_tax:,.2f}")

    # Сигналы главного окна
    ui_MainWindow.Income.textChanged.connect(update_tax_display)
    ui_MainWindow.pushButton_Save.clicked.connect(save_and_update)

    # ---------------- Обработчики логина/регистрации ----------------
    def try_login():
        username = ui_login.line_User.text().strip()
        password = ui_login.line_Password.text().strip()
        if not username or not password:
            QMessageBox.warning(login_window, "Ошибка", "Введите логин/email и пароль.")
            return
        if login_user(username, password):
            load_totals()            # загружаем итоги пользователя
            ui_MainWindow.Income.clear()
            ui_MainWindow.label_TaxProc.clear()
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

    def back_to_login():
        register_window.hide()
        login_window.show()

    ui_login.pushButton_Login.clicked.connect(try_login)
    ui_login.pushButton_Cancel.clicked.connect(go_to_register)
    ui_register.pushButton_Cancel.clicked.connect(do_registration)

    MainWindow_window.closeEvent = lambda event: QtWidgets.qApp.quit()

    sys.exit(app.exec_())