from PyQt5 import QtWidgets, QtCore
import csv
try:
    import openpyxl
    from openpyxl import Workbook
except Exception:
    openpyxl = None
from models.db import list_visits_between

class HistoryController(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('История обращений (период)')
        self.resize(900, 500)
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        lay = QtWidgets.QVBoxLayout(central)
        top = QtWidgets.QHBoxLayout()
        self.date_from = QtWidgets.QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QtCore.QDate.currentDate())
        self.date_to = QtWidgets.QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QtCore.QDate.currentDate())
        self.btn_apply = QtWidgets.QPushButton('Показать')
        self.btn_export = QtWidgets.QPushButton('Экспорт в Excel')
        top.addWidget(self.date_from)
        top.addWidget(self.date_to)
        top.addWidget(self.btn_apply)
        top.addWidget(self.btn_export)
        lay.addLayout(top)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['id','ДатаВремя','ФИО','МКБ'])
        self.table.hideColumn(0)
        lay.addWidget(self.table)
        self.btn_apply.clicked.connect(self.on_apply)
        self.btn_export.clicked.connect(self.on_export)
        self.on_apply()

    def on_apply(self):
        start = self.date_from.date().toString('yyyy-MM-dd') + ' 00:00:00'
        end = self.date_to.date().toString('yyyy-MM-dd') + ' 23:59:59'
        rows = list_visits_between(start, end)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QtWidgets.QTableWidgetItem(str(r.get('id')))
            dt_item = QtWidgets.QTableWidgetItem(r.get('visit_datetime') or '')
            fio_item = QtWidgets.QTableWidgetItem(r.get('patient_fio') or '')
            mkb_item = QtWidgets.QTableWidgetItem(r.get('mkb_code') or '')
            self.table.setItem(i,0,id_item)
            self.table.setItem(i,1,dt_item)
            self.table.setItem(i,2,fio_item)
            self.table.setItem(i,3,mkb_item)
        try:
            self.table.hideColumn(0)
        except Exception:
            pass

    def on_export(self):
        n = self.table.rowCount()
        if n == 0:
            QtWidgets.QMessageBox.information(self, 'Экспорт', 'Нет данных для экспорта')
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Сохранить в Excel', '', 'Excel Files (*.xlsx);;CSV Files (*.csv)')
        if not path:
            return
        if path.lower().endswith('.xlsx') and openpyxl:
            wb = Workbook()
            ws = wb.active
            ws.append(['id','ДатаВремя','ФИО','МКБ'])
            for i in range(n):
                row = [self.table.item(i,0).text() if self.table.item(i,0) else '',
                       self.table.item(i,1).text() if self.table.item(i,1) else '',
                       self.table.item(i,2).text() if self.table.item(i,2) else '',
                       self.table.item(i,3).text() if self.table.item(i,3) else '']
                ws.append(row)
            wb.save(path)
            QtWidgets.QMessageBox.information(self, 'Экспорт', f'Экспорт выполнен: {path}')
        else:
            if not path.lower().endswith('.csv'):
                path = path + '.csv'
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id','ДатаВремя','ФИО','МКБ'])
                for i in range(n):
                    row = [self.table.item(i,0).text() if self.table.item(i,0) else '',
                           self.table.item(i,1).text() if self.table.item(i,1) else '',
                           self.table.item(i,2).text() if self.table.item(i,2) else '',
                           self.table.item(i,3).text() if self.table.item(i,3) else '']
                    writer.writerow(row)
            QtWidgets.QMessageBox.information(self, 'Экспорт', f'Экспорт выполнен: {path}')
