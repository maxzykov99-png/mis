from PyQt5 import uic, QtWidgets
import os
from config import UI_DIR
from models.db import list_visits_between
import datetime

class ReportsController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(UI_DIR, "reports.ui")
        uic.loadUi(ui_path, self)

        if hasattr(self, "createreport"):
            self.createreport.clicked.connect(self.on_create_report)

    def on_create_report(self):
        try:
            start = self.datereport_s.date().toString("yyyy-MM-dd")
            end = self.datereport_po.date().toString("yyyy-MM-dd")
        except Exception:
            start = getattr(self, "datereport_s", None).text() if hasattr(self, "datereport_s") else datetime.date.today().isoformat()
            end = getattr(self, "datereport_po", None).text() if hasattr(self, "datereport_po") else datetime.date.today().isoformat()

        rows = list_visits_between(start, end)
        self.show_results_table(rows)

    def show_results_table(self, rows):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Результаты отчёта")
        table = QtWidgets.QTableWidget(dialog)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Дата", "Пациент", "Организация", "Прочее"])
        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(r.get("visit_date", "")))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(r.get("patient_fio", "")))
            table.setItem(i, 2, QtWidgets.QTableWidgetItem(r.get("organisation", "")))
            table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(r.get("extra", ""))))
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(table)
        dialog.resize(800, 400)
        dialog.exec_()
