from PyQt5 import QtWidgets, QtCore
from settings_store import verify_user, set_current_user, load_settings


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Вход в систему")
        self.resize(350, 150)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.username = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)

        form.addRow("Пользователь:", self.username)
        form.addRow("Пароль:", self.password)
        layout.addLayout(form)

        btns = QtWidgets.QHBoxLayout()
        self.btn_login = QtWidgets.QPushButton("Войти")
        self.btn_cancel = QtWidgets.QPushButton("Отмена")
        btns.addWidget(self.btn_login)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.btn_login.clicked.connect(self.on_login)
        self.btn_cancel.clicked.connect(self.reject)

        # Автозаполнение имени пользователя
        try:
            s = load_settings()
            users = s.get("users", {})
            if users:
                self.username.setText(list(users.keys())[0])
        except Exception:
            pass

    def on_login(self):
        user = self.username.text().strip()
        pwd = self.password.text()

        if not user or not pwd:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль")
            return

        ok = verify_user(user, pwd)
        if ok:
            set_current_user(user)
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Неверное имя пользователя или пароль")
