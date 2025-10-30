import sys
from PyQt5 import QtWidgets
from controllers.mainwindow_controller import MainWindowController
from controllers.reports_controller import ReportsController
from controllers.settings_controller import SettingsController
from controllers.database_controller import DatabaseController
from controllers.login_controller import LoginDialog
from controllers.history_controller import HistoryController
from models.db import init_db


def main():
    # initialize DB automatically
    try:
        init_db()
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)

    login = LoginDialog()
    if login.exec_() != QtWidgets.QDialog.Accepted:
        sys.exit(0)

    main_win = MainWindowController()
    reports_win = ReportsController()
    settings_win = SettingsController()
    db_win = DatabaseController()
    history_win = HistoryController()

    # connect settings_updated signal so main window updates comboboxes automatically
    try:
        settings_win.settings_updated.connect(main_win.apply_settings_to_ui)
    except Exception:
        pass

    try:
        if hasattr(main_win, 'reports'):
            main_win.reports.triggered.connect(reports_win.show)
        if hasattr(main_win, 'opendatabase'):
            main_win.opendatabase.triggered.connect(db_win.show)
        if hasattr(main_win, 'action_3'):
            main_win.action_3.triggered.connect(settings_win.show)
        if hasattr(main_win, 'action_4'):
            main_win.action_4.triggered.connect(settings_win.show)
        if hasattr(main_win, 'history'):
            main_win.history.triggered.connect(history_win.show)
    except Exception:
        pass

    main_win.show()
    try:
        if hasattr(main_win, 'load_today_visits'):
            main_win.load_today_visits()
    except Exception:
        pass

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
