from PyQt5 import uic, QtWidgets, QtCore, QtGui
import os, json, datetime
from config import UI_DIR
from models.db import save_patient, init_db, save_visit, list_patients_like, list_visits_for_date, get_visit_by_id
from settings_store import load_settings, get_current_user

class MainWindowController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(UI_DIR, "mainwindow.ui")
        try:
            uic.loadUi(ui_path, self)
        except Exception as e:
            print('Ошибка загрузки mainwindow.ui:', e)

        # Auto init DB if missing
        try:
            init_db()
        except Exception as e:
            print('init_db error', e)

        self.app_settings = load_settings()

        # Connect menu actions
        try:
            if hasattr(self, 'reports'):
                self.reports.triggered.connect(self.open_reports)
        except Exception:
            pass
        try:
            if hasattr(self, 'opendatabase'):
                self.opendatabase.triggered.connect(self.open_database)
        except Exception:
            pass

        # Buttons
        if hasattr(self, 'savesession'):
            self.savesession.clicked.connect(self.on_save_clicked)
        if hasattr(self, 'closecase'):
            self.closecase.clicked.connect(self.on_closecase)
        if hasattr(self, 'pushButton_epicrisis'):
            self.pushButton_epicrisis.clicked.connect(self.show_epikriz)
        if hasattr(self, 'epikrizbut'):
            self.epikrizbut.clicked.connect(self.show_epikriz)

        # Autocomplete for patientfio
        if hasattr(self, 'patientfio'):
            completer = QtWidgets.QCompleter([], self)
            completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self.patientfio.setCompleter(completer)
            self.patientfio.textEdited.connect(self.on_patientfio_edited)

        # Fill comboboxes from settings
        self.apply_settings_to_ui(self.app_settings)

        # patientlist table
        if hasattr(self, 'patientlist'):
            try:
                self.patientlist.setColumnCount(4)
                self.patientlist.setHorizontalHeaderLabels(['id','Время','Пациент','МКБ'])
                self.patientlist.hideColumn(0)
            except Exception:
                pass
            self.patientlist.doubleClicked.connect(self.on_patientlist_doubleclick)
            self.load_today_visits()

        # LCD show hours:minutes
        if hasattr(self, 'LCDtimedate'):
            self._timer_clock = QtCore.QTimer(self)
            self._timer_clock.timeout.connect(self.update_clock)
            self._timer_clock.start(1000)
            self.update_clock()


    def apply_theme(self, theme_name='light'):
        try:
            if theme_name == 'dark':
                # Simple built-in dark theme
                self.setStyleSheet("QWidget{background:#2b2b2b;color:#e6e6e6;} QLineEdit{background:#3c3c3c;} QTableWidget{background:#3c3c3c;}")
            else:
                self.setStyleSheet("")
        except Exception:
            pass

    
    def apply_settings_to_ui(self, settings):
        """Применяет настройки приложения к интерфейсу главного окна."""
        try:
            # Применяем тему
            try:
                theme = settings.get('theme', 'light')
                self.apply_theme(theme)
            except Exception:
                pass

            # Загружаем списки
            orgs = settings.get('organisations', []) or []
            medics = settings.get('medics', []) or []

            # Организации
            if hasattr(self, 'organisation'):
                try:
                    self.organisation.clear()
                    self.organisation.addItems(orgs)
                except Exception:
                    pass

            # Список врачей
            try:
                if hasattr(self, 'fiovrach'):
                    try:
                        if hasattr(self.fiovrach, 'addItems'):
                            self.fiovrach.clear()
                            if medics:
                                self.fiovrach.addItems(medics)
                        else:
                            if medics:
                                try:
                                    self.fiovrach.setText(medics[0])
                                except Exception:
                                    pass
                    except Exception as e:
                        print('Ошибка заполнения fiovrach:', e)
            except Exception:
                pass

        except Exception as e:
            print('Ошибка применения настроек:', e)


    def update_clock(self):
        now = datetime.datetime.now().strftime('%H:%M')
        try:
            self.LCDtimedate.display(now)
        except Exception:
            pass

    def on_patientfio_edited(self, text):
        try:
            suggestions = list_patients_like(text, limit=50)
            model = QtCore.QStringListModel(suggestions, self)
            self.patientfio.completer().setModel(model)
        except Exception:
            pass

    def collect_patient_from_form(self) -> dict:
        def get_value(w):
            try:
                if isinstance(w, QtWidgets.QLineEdit):
                    return w.text()
                if isinstance(w, QtWidgets.QTextEdit):
                    return w.toPlainText()
                if isinstance(w, QtWidgets.QComboBox):
                    return w.currentText()
                if isinstance(w, QtWidgets.QDateEdit):
                    return w.date().toString('yyyy-MM-dd')
                if isinstance(w, QtWidgets.QCheckBox):
                    return w.isChecked()
            except Exception:
                pass
            return None

        patient = {
            'fio': getattr(self, 'patientfio').text() if hasattr(self, 'patientfio') else '',
            'birthdate': getattr(self, 'patientdate').date().toString('yyyy-MM-dd') if hasattr(self, 'patientdate') else None,
            'phone': getattr(self, 'phone_pole').text() if hasattr(self, 'phone_pole') else '',
            'organisation': getattr(self, 'organisation').currentText() if hasattr(self, 'organisation') else ''
        }

        full = {}
        for w in self.findChildren((QtWidgets.QLineEdit, QtWidgets.QTextEdit, QtWidgets.QComboBox, QtWidgets.QDateEdit, QtWidgets.QCheckBox)):
            try:
                name = w.objectName()
                full[name] = get_value(w)
            except Exception:
                pass

        patient['full_epicrisis'] = full
        return patient

    def on_save_clicked(self):
        self.on_closecase()

    def on_closecase(self):
        try:
            patient = self.collect_patient_from_form()
            # require FIO
            if not patient.get('fio') or not str(patient.get('fio')).strip():
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Введите ФИО пациента перед сохранением.')
                return
            pid = save_patient(patient)
            visit_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            diagnosis = ''
            mkb_code = ''
            outcome = ''
            evacuation_place = ''
            try:
                if hasattr(self, 'diagnosis'):
                    diagnosis = self.diagnosis.text()
                if hasattr(self, 'mkb10list'):
                    mkb_code = self.mkb10list.currentText() if isinstance(self.mkb10list, QtWidgets.QComboBox) else ''
                if hasattr(self, 'outcome'):
                    outcome = self.outcome.currentText() if isinstance(self.outcome, QtWidgets.QComboBox) else ''
                if hasattr(self, 'evacuation'):
                    evacuation_place = self.evacuation.text() if hasattr(self, 'evacuation') else ''
            except Exception:
                pass
            vid = save_visit(pid, visit_datetime, getattr(self, 'vidpriema').currentText() if hasattr(self,'vidpriema') else '',
                             getattr(self, 'obschsost').currentText() if hasattr(self,'obschsost') else '',
                             getattr(self, 'soznanie').currentText() if hasattr(self,'soznanie') else '',
                             get_current_user() or (getattr(self, 'profession').text() if hasattr(self, 'profession') else ''),
                             diagnosis, mkb_code, outcome, evacuation_place, patient['full_epicrisis'])
            QtWidgets.QMessageBox.information(self, 'Сохранено', f'Кейс сохранён (id={vid})')
            try:
                self.load_today_visits()
            except Exception:
                pass
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить кейс: {e}')

    def load_today_visits(self):
        try:
            today = __import__('datetime').date.today().isoformat()
            rows = list_visits_for_date(today)
            try:
                self.patientlist.setColumnCount(4)
                self.patientlist.setHorizontalHeaderLabels(['id','Время','Пациент','МКБ'])
            except Exception:
                pass
            self.patientlist.setRowCount(len(rows))
            for i, r in enumerate(rows):
                id_item = QtWidgets.QTableWidgetItem(str(r.get('id')))
                time_item = QtWidgets.QTableWidgetItem(str(r.get('visit_datetime')))
                fio_item = QtWidgets.QTableWidgetItem(r.get('patient_fio') or '')
                mkb_item = QtWidgets.QTableWidgetItem(r.get('mkb_code') or '')
                try:
                    self.patientlist.setItem(i,0,id_item)
                    self.patientlist.setItem(i,1,time_item)
                    self.patientlist.setItem(i,2,fio_item)
                    self.patientlist.setItem(i,3,mkb_item)
                except Exception:
                    pass
            try:
                self.patientlist.hideColumn(0)
            except Exception:
                pass
        except Exception as e:
            print('load_today_visits error', e)

    def on_patientlist_doubleclick(self, index):
        try:
            row = index.row()
            id_item = self.patientlist.item(row, 0)
            if not id_item:
                return
            vid = int(id_item.text())
            visit = get_visit_by_id(vid)
            if not visit:
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Кейс не найден')
                return
            self.open_visit_in_ui(visit)
        except Exception as e:
            print('on_patientlist_doubleclick error', e)

    def open_visit_in_ui(self, visit):
        fc = visit.get('full_epicrisis', {}) or {}
        for k, v in fc.items():
            if hasattr(self, k):
                w = getattr(self, k)
                try:
                    if isinstance(w, QtWidgets.QLineEdit):
                        w.setText(str(v))
                    elif isinstance(w, QtWidgets.QTextEdit):
                        w.setPlainText(str(v))
                    elif isinstance(w, QtWidgets.QComboBox):
                        idx = w.findText(str(v))
                        if idx>=0:
                            w.setCurrentIndex(idx)
                        else:
                            try:
                                w.setCurrentText(str(v))
                            except Exception:
                                pass
                    elif isinstance(w, QtWidgets.QDateEdit):
                        try:
                            dt = QtCore.QDate.fromString(str(v), 'yyyy-MM-dd')
                            w.setDate(dt)
                        except Exception:
                            pass
                    elif isinstance(w, QtWidgets.QCheckBox):
                        try:
                            w.setChecked(bool(v))
                        except Exception:
                            pass
                except Exception:
                    pass

def show_epikriz(self, visit=None):
    """
    GPT: улучшенная логика формирования эпикриза.
    - Показываются ТОЛЬКО выбранные чекбоксы (True).
    - Используются читаемые подписи (label_map) если доступны, иначе генерируются из objectName.
    - Поля группируются по секциям (group_map), с дефолтными группами для медицины.
    - Чистый формат вывода.
    """
    from PyQt5 import QtCore, QtWidgets
    import datetime, re

    # Получаем данные
    if isinstance(visit, bool):
        visit = None

    if visit is None:
        patient = self.collect_patient_from_form()
        fc = patient.get('full_epicrisis', {}) or {}
        header = f"Пациент: {patient.get('fio') or ''}\\nДата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
    else:
        fc = visit.get('full_epicrisis', {}) or {}
        header = f"Пациент: {visit.get('patient_fio') or ''}\\nДата: {visit.get('visit_datetime') or ''}\\n\\n"

    lines = [header]

    # Try to get label_map / group_map if present in module globals (generated from UI elsewhere)
    label_map = globals().get('label_map', {}) or {}
    group_map = globals().get('group_map', {}) or {}

    # If no explicit label_map, build a human-readable map from fc keys
    def human_label(name):
        # common replacements and prettify
        name = re.sub(r'^(sy|syp|sym|s__?)', '', name, flags=re.IGNORECASE)
        s = re.sub(r'[_\-]+', ' ', name)
        # split camelCase
        s = re.sub('([a-z0-9])([A-Z])', r'\\1 \\2', s)
        s = s.strip().replace('  ', ' ')
        return s.capitalize()

    if not label_map:
        for k in fc.keys():
            label_map[k] = human_label(k)

    # Define groups (use requested Russian names)
    default_groups = {
        "general": "Общее состояние пациента",
        "skin": "Состояние кожи и слизистых",
        "respiratory": "Дыхательная система",
        "cardio": "Сердечно-сосудистая система",
        "digestive": "Пищеварительная система",
        "urinary": "Мочевыделительная система",
        "nervous": "Нервная система",
        "treatment": "Назначенное лечение",
    }

    # Heuristic mapping from field name -> group key
    heur = {
        "skin": ["skin", "kож", "кож", "sypskin", "rash", "syp"],
        "respiratory": ["resp", "dysp", "dyspno", "breath", "odush", "дых", "одыш"],
        "cardio": ["card", "heart", "серд", "пульс", "аритм"],
        "digestive": ["gastro", "digest", "abdom", "печен", " желуд", "стул", "тошн"],
        "urinary": ["urin", "почк", "моч", "diur"],
        "nervous": ["nerv", "neuro", "sozn", "созн", "судор", "голов", "головокруж"],
        "treatment": ["treat", "ther", "lechenie", "назнач"],
        "general": ["fio", "age", "weight", "height", "compl", "жалоб", "obschsost"]
    }

    # If group_map empty, build grouping based on heuristics
    if not group_map:
        group_map = {v: [] for v in default_groups.values()}
        for name in label_map:
            placed = False
            lname = name.lower()
            for gk, keys in heur.items():
                for key in keys:
                    if key in lname:
                        group_map[default_groups[gk]].append((name, label_map.get(name, human_label(name))))
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                # default to general
                group_map[default_groups["general"]].append((name, label_map.get(name, human_label(name))))

    # Now build lines: only show checkboxes that are True and non-empty other fields
    for group, items in group_map.items():
        # skip empty groups
        if not items:
            continue
        lines.append(f"\\n--- {group} ---")
        for name, display_text in items:
            v = fc.get(name, None)
            # Normalize strings that represent booleans
            if isinstance(v, str):
                vl = v.strip().lower()
                if vl in ('false','0','нет','no','none',''):
                    v = False
                elif vl in ('true','1','да','yes'):
                    v = True
            # Detect checkbox widgets if possible: check stored as bool or 0/1 or 'True'
            is_checked = False
            if isinstance(v, bool):
                is_checked = v
            elif isinstance(v, (int, float)) and v != 0:
                is_checked = True
            elif isinstance(v, str) and v.strip().lower() in ('true','1','да','yes'):
                is_checked = True

            # Show only checked checkboxes; other fields: show if non-empty
            if is_checked:
                # render checked checkbox as simple label "DisplayText"
                lines.append(f"{display_text}")
            else:
                # for non-boolean fields, show if present
                if v not in (None, '', False):
                    lines.append(f"{display_text}: {v}")

    text = "\\n".join(lines)

    # Persist and display
    try:
        if visit is None:
            patient['full_epicrisis_text'] = text
        else:
            visit['full_epicrisis_text'] = text
    except Exception:
        pass

    # Display in UI: try several known widget names
    try:
        if hasattr(self, 'ui') and hasattr(self.ui, 'epicriz_output'):
            self.ui.epicriz_output.setPlainText(text)
        else:
            w = getattr(self, 'epicriz_output', None) or getattr(self, 'epikriz_output', None)
            if w is not None and hasattr(w, 'setPlainText'):
                w.setPlainText(text)
            else:
                # Fallback dialog
                dlg = QtWidgets.QDialog(self)
                dlg.setWindowTitle('Эпикриз')
                dlg.resize(800, 600)
                lay = QtWidgets.QVBoxLayout(dlg)
                txt = QtWidgets.QTextEdit(dlg)
                txt.setPlainText(text)
                txt.setReadOnly(True)
                lay.addWidget(txt)
                btns = QtWidgets.QHBoxLayout()
                btn_close = QtWidgets.QPushButton('Закрыть')
                btns.addWidget(btn_close)
                lay.addLayout(btns)
                btn_close.clicked.connect(dlg.accept)
                dlg.exec_()
    except Exception:
        pass

    return text
