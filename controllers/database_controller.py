from PyQt5 import QtWidgets, uic, QtCore
import os
from config import UI_DIR
from models.db import list_visits_between, get_visit_by_id, init_db

class DatabaseController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('База данных обращений')
        self.resize(900, 500)
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        lay = QtWidgets.QVBoxLayout(central)
        top = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText('Поиск по ФИО или коду...')
        self.date_from = QtWidgets.QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.date_to = QtWidgets.QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QtCore.QDate.currentDate())
        self.btn_filter = QtWidgets.QPushButton('Применить')
        top.addWidget(self.search_edit)
        top.addWidget(self.date_from)
        top.addWidget(self.date_to)
        top.addWidget(self.btn_filter)
        lay.addLayout(top)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['id','Дата','Пациент','Кейс'])
        self.table.hideColumn(0)
        self.table.doubleClicked.connect(self.on_double)
        lay.addWidget(self.table)
        self.btn_filter.clicked.connect(self.on_filter)
        # initialize DB
        try:
            init_db()
        except Exception:
            pass
        self.on_filter()

    def on_filter(self):
        try:
            start = self.date_from.date().toString('yyyy-MM-dd') + ' 00:00:00'
            end = self.date_to.date().toString('yyyy-MM-dd') + ' 23:59:59'
            rows = list_visits_between(start, end)
            q = self.search_edit.text().lower()
            filtered = []
            for r in rows:
                if not q or q in (r.get('patient_fio') or '').lower() or q in str(r.get('full_epicrisis','')).lower():
                    filtered.append(r)
            self.table.setRowCount(len(filtered))
            for i, r in enumerate(filtered):
                id_item = QtWidgets.QTableWidgetItem(str(r.get('id')))
                date_item = QtWidgets.QTableWidgetItem(r.get('visit_datetime'))
                fio_item = QtWidgets.QTableWidgetItem(r.get('patient_fio') or '')
                case_item = QtWidgets.QTableWidgetItem(str(r.get('full_epicrisis') or ''))
                self.table.setItem(i,0,id_item)
                self.table.setItem(i,1,date_item)
                self.table.setItem(i,2,fio_item)
                self.table.setItem(i,3,case_item)
            try:
                self.table.hideColumn(0)
            except Exception:
                pass
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить данные: {e}')

    def on_double(self, index):
        try:
            row = index.row()
            id_item = self.table.item(row,0)
            if not id_item:
                return
            vid = int(id_item.text())
            visit = get_visit_by_id(vid)
            if not visit:
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Кейс не найден')
                return
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle('Кейс')
            txt = QtWidgets.QTextEdit(dlg)
            txt.setPlainText(str(visit.get('full_epicrisis') or ''))
            txt.setReadOnly(True)
            lay = QtWidgets.QVBoxLayout(dlg)
            lay.addWidget(txt)
            dlg.resize(800,600)
            dlg.exec_()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть кейс: {e}')
