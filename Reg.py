import sys
import hashlib
import re
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
import psycopg2
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
    """Создаёт таблицы users, income и user_totals, если их ещё нет."""
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            amount NUMERIC(12,2) NOT NULL,
            tax NUMERIC(12,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_totals (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            total_income NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_tax NUMERIC(12,2) NOT NULL DEFAULT 0
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
        cur.execute(
            "SELECT id FROM users WHERE LOWER(email) = LOWER(%s) AND password_hash = %s",
            (login_or_email, pwd_hash)
        )
    else:
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
        cur.execute(
            "INSERT INTO users (login, password_hash, email) VALUES (%s, %s, %s) RETURNING id",
            (username, pwd_hash, email)
        )
        user_id = cur.fetchone()[0]
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
        return income * 0.13
    else:
        return 5_000_000 * 0.13 + (income - 5_000_000) * 0.15

def get_totals():
    """Возвращает (суммарный_доход, суммарный_налог) из таблицы user_totals."""
    global current_user_id
    if current_user_id is None:
        return 0.0, 0.0
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT total_income, total_tax FROM user_totals WHERE user_id = %s",
        (current_user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return float(row[0]), float(row[1])
    return 0.0, 0.0

def save_income(amount):
    """
    Добавляет доход, вычисляя налог нарастающим итогом.
    Обновляет таблицу user_totals.
    """
    global current_user_id
    if current_user_id is None:
        return False, "Пользователь не авторизован."
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Текущие итоги
        cur.execute("SELECT total_income, total_tax FROM user_totals WHERE user_id = %s FOR UPDATE",
                    (current_user_id,))
        row = cur.fetchone()
        if not row:
            # Если по какой-то причине записи нет – создаём
            cur.execute("INSERT INTO user_totals (user_id) VALUES (%s)", (current_user_id,))
            total_income, total_tax = 0.0, 0.0
        else:
            total_income, total_tax = float(row[0]), float(row[1])

        new_total_income = total_income + amount
        new_total_tax = calculate_tax(new_total_income)
        tax_due = new_total_tax - total_tax   # добавочный налог

        # Сохраняем запись о доходе
        cur.execute(
            "INSERT INTO income (user_id, amount, tax) VALUES (%s, %s, %s)",
            (current_user_id, amount, tax_due)
        )
        # Обновляем итоги
        cur.execute(
            "UPDATE user_totals SET total_income = %s, total_tax = %s WHERE user_id = %s",
            (new_total_income, new_total_tax, current_user_id)
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

# ==================== UI-классы ====================
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
        MainWindow.resize(400, 460)                # увеличен размер окна
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Поле ввода суммы
        self.Income = QtWidgets.QLineEdit(self.centralwidget)
        self.Income.setGeometry(QtCore.QRect(160, 50, 161, 31))
        self.Income.setText("")
        self.Income.setObjectName("Income")

        # "Введите сумму:"
        self.Lable_sum = QtWidgets.QLabel(self.centralwidget)
        self.Lable_sum.setGeometry(QtCore.QRect(30, 60, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_sum.setFont(font)
        self.Lable_sum.setObjectName("Lable_sum")

        # "Налог:"
        self.Lable_3 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_3.setGeometry(QtCore.QRect(30, 100, 121, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_3.setFont(font)
        self.Lable_3.setObjectName("Lable_3")

        # label_TaxProc - ставка
        self.label_TaxProc = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxProc.setGeometry(QtCore.QRect(100, 100, 200, 21))
        self.label_TaxProc.setText("")
        self.label_TaxProc.setObjectName("label_TaxProc")

        # "Добавится налога:"
        self.label_NewTaxTitle = QtWidgets.QLabel(self.centralwidget)
        self.label_NewTaxTitle.setGeometry(QtCore.QRect(30, 130, 151, 16))
        font_small = QtGui.QFont()
        font_small.setPointSize(10)
        font_small.setBold(True)
        font_small.setWeight(75)
        self.label_NewTaxTitle.setFont(font_small)
        self.label_NewTaxTitle.setObjectName("label_NewTaxTitle")

        self.label_NewTaxValue = QtWidgets.QLabel(self.centralwidget)
        self.label_NewTaxValue.setGeometry(QtCore.QRect(160, 130, 161, 21))
        self.label_NewTaxValue.setText("")
        self.label_NewTaxValue.setObjectName("label_NewTaxValue")

        # "Налог, руб. (итог):"
        self.label_TaxRubTitle = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxRubTitle.setGeometry(QtCore.QRect(30, 160, 151, 16))
        self.label_TaxRubTitle.setFont(font_small)
        self.label_TaxRubTitle.setObjectName("label_TaxRubTitle")

        self.label_TaxRubValue = QtWidgets.QLabel(self.centralwidget)
        self.label_TaxRubValue.setGeometry(QtCore.QRect(160, 160, 161, 21))
        self.label_TaxRubValue.setText("")
        self.label_TaxRubValue.setObjectName("label_TaxRubValue")

        # "Доход после налога:"
        self.label_NetIncomeTitle = QtWidgets.QLabel(self.centralwidget)
        self.label_NetIncomeTitle.setGeometry(QtCore.QRect(30, 190, 151, 16))
        self.label_NetIncomeTitle.setFont(font_small)
        self.label_NetIncomeTitle.setObjectName("label_NetIncomeTitle")

        self.label_NetIncomeValue = QtWidgets.QLabel(self.centralwidget)
        self.label_NetIncomeValue.setGeometry(QtCore.QRect(160, 190, 161, 21))
        self.label_NetIncomeValue.setText("")
        self.label_NetIncomeValue.setObjectName("label_NetIncomeValue")

        # Кнопка "Сохранить"
        self.pushButton_Save = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Save.setGeometry(QtCore.QRect(120, 230, 111, 31))
        self.pushButton_Save.setObjectName("pushButton_Save")

        # Итоговые накопления
        self.Lable_1 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_1.setGeometry(QtCore.QRect(30, 280, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_1.setFont(font)
        self.Lable_1.setObjectName("Lable_1")

        self.label_Sum = QtWidgets.QLabel(self.centralwidget)
        self.label_Sum.setGeometry(QtCore.QRect(160, 280, 161, 21))
        self.label_Sum.setText("0.00")
        self.label_Sum.setObjectName("label_Sum")

        self.Lable_2 = QtWidgets.QLabel(self.centralwidget)
        self.Lable_2.setGeometry(QtCore.QRect(30, 320, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Lable_2.setFont(font)
        self.Lable_2.setObjectName("Lable_2")

        self.label_SumTax = QtWidgets.QLabel(self.centralwidget)
        self.label_SumTax.setGeometry(QtCore.QRect(160, 320, 161, 21))
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
        self.label_NewTaxTitle.setText(_translate("MainWindow", "Добавится налога:"))
        self.label_TaxRubTitle.setText(_translate("MainWindow", "Налог, руб. (итог):"))
        self.label_NetIncomeTitle.setText(_translate("MainWindow", "Доход после налога:"))

# ==================== Точка входа ====================
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

    # ---------- Логика главного окна ----------
    def update_tax_display():
        text = ui_MainWindow.Income.text().strip()
        if not text:
            ui_MainWindow.label_TaxProc.setText("")
            ui_MainWindow.label_NewTaxValue.setText("")
            ui_MainWindow.label_TaxRubValue.setText("")
            ui_MainWindow.label_NetIncomeValue.setText("")
            return
        try:
            amount = float(text)
            if amount <= 0:
                ui_MainWindow.label_TaxProc.setText("")
                ui_MainWindow.label_NewTaxValue.setText("")
                ui_MainWindow.label_TaxRubValue.setText("")
                ui_MainWindow.label_NetIncomeValue.setText("")
                return
            cur_income, cur_tax = get_totals()
            new_total_income = cur_income + amount
            new_total_tax = calculate_tax(new_total_income)
            added_tax = new_total_tax - cur_tax
            net_after = new_total_income - new_total_tax

            if new_total_income <= 5_000_000:
                rate = "13%"
            else:
                rate = "13% на первые 5 млн + 15% свыше"

            ui_MainWindow.label_TaxProc.setText(rate)
            ui_MainWindow.label_NewTaxValue.setText(f"{added_tax:,.2f}")
            ui_MainWindow.label_TaxRubValue.setText(f"{new_total_tax:,.2f}")
            ui_MainWindow.label_NetIncomeValue.setText(f"{net_after:,.2f}")
        except ValueError:
            ui_MainWindow.label_TaxProc.setText("")
            ui_MainWindow.label_NewTaxValue.setText("")
            ui_MainWindow.label_TaxRubValue.setText("")
            ui_MainWindow.label_NetIncomeValue.setText("")

    def save_and_update():
        text = ui_MainWindow.Income.text().strip()
        if not text:
            QMessageBox.warning(MainWindow_window, "Ошибка", "Введите сумму дохода.")
            return
        try:
            amount = float(text)
            if amount <= 0:
                QMessageBox.warning(MainWindow_window, "Ошибка", "Сумма должна быть положительной.")
                return
        except ValueError:
            QMessageBox.warning(MainWindow_window, "Ошибка", "Некорректная сумма.")
            return

        success, msg = save_income(amount)
        if success:
            total_income, total_tax = get_totals()
            ui_MainWindow.label_Sum.setText(f"{total_income:,.2f}")
            ui_MainWindow.label_SumTax.setText(f"{total_tax:,.2f}")
            ui_MainWindow.Income.clear()
            ui_MainWindow.label_TaxProc.clear()
            ui_MainWindow.label_NewTaxValue.clear()
            ui_MainWindow.label_TaxRubValue.clear()
            ui_MainWindow.label_NetIncomeValue.clear()
            QMessageBox.information(MainWindow_window, "Успех", msg)
        else:
            QMessageBox.critical(MainWindow_window, "Ошибка", msg)

    def load_totals():
        total_income, total_tax = get_totals()
        ui_MainWindow.label_Sum.setText(f"{total_income:,.2f}")
        ui_MainWindow.label_SumTax.setText(f"{total_tax:,.2f}")

    ui_MainWindow.Income.textChanged.connect(update_tax_display)
    ui_MainWindow.pushButton_Save.clicked.connect(save_and_update)

    # ---------- Логика логина/регистрации ----------
    def try_login():
        username = ui_login.line_User.text().strip()
        password = ui_login.line_Password.text().strip()
        if not username or not password:
            QMessageBox.warning(login_window, "Ошибка", "Введите логин/email и пароль.")
            return
        if login_user(username, password):
            load_totals()
            ui_MainWindow.Income.clear()
            ui_MainWindow.label_TaxProc.clear()
            ui_MainWindow.label_NewTaxValue.clear()
            ui_MainWindow.label_TaxRubValue.clear()
            ui_MainWindow.label_NetIncomeValue.clear()
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