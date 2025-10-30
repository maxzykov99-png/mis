import sqlite3
from contextlib import closing
from config import DB_PATH
import json

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_number TEXT UNIQUE,
    fio TEXT,
    birthdate TEXT,
    phone TEXT,
    organisation TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    visit_datetime TEXT,
    vid_priema TEXT,
    obschsost TEXT,
    soznanie TEXT,
    examiner TEXT,
    diagnosis TEXT,
    mkb_code TEXT,
    outcome TEXT,
    evacuation_place TEXT,
    full_epicrisis JSON,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.executescript(SCHEMA)
        conn.commit()

def _generate_patient_number(last_id: int) -> str:
    return f"P{last_id:06d}"

def find_patient(fio: str=None, birthdate: str=None, phone: str=None):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        if phone:
            cur.execute("SELECT * FROM patients WHERE phone=? LIMIT 1", (phone,))
        elif fio and birthdate:
            cur.execute("SELECT * FROM patients WHERE fio=? AND birthdate=? LIMIT 1", (fio, birthdate))
        elif fio:
            cur.execute("SELECT * FROM patients WHERE fio LIKE ? LIMIT 1", (f"%{fio}%",))
        else:
            return None
        row = cur.fetchone()
        return dict(row) if row else None

def save_patient(patient: dict) -> int:
    """Create or update patient. Ensures patient_number exists."""
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        existing = None
        if patient.get('phone'):
            existing = find_patient(phone=patient.get('phone'))
        if not existing and patient.get('fio') and patient.get('birthdate'):
            existing = find_patient(fio=patient.get('fio'), birthdate=patient.get('birthdate'))
        if existing:
            pid = existing['id']
            cur.execute("""UPDATE patients SET fio=?, birthdate=?, phone=?, organisation=? WHERE id=?""",
                        (patient.get('fio'), patient.get('birthdate'), patient.get('phone'), patient.get('organisation'), pid))
            conn.commit()
            return pid
        else:
            cur.execute("""INSERT INTO patients (fio, birthdate, phone, organisation) VALUES (?, ?, ?, ?)""",
                        (patient.get('fio'), patient.get('birthdate'), patient.get('phone'), patient.get('organisation')))
            conn.commit()
            pid = cur.lastrowid
            pnum = _generate_patient_number(pid)
            cur.execute("UPDATE patients SET patient_number=? WHERE id=?", (pnum, pid))
            conn.commit()
            return pid

def get_patient_by_id(pid: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id=?", (pid,))
        row = cur.fetchone()
        return dict(row) if row else None

def list_patients_like(prefix: str, limit=20):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT fio FROM patients WHERE fio LIKE ? GROUP BY fio LIMIT ?", (f"%{prefix}%", limit))
        return [r[0] for r in cur.fetchall()]

def save_visit(patient_id: int, visit_datetime: str, vid_priema: str, obschsost: str, soznanie: str, examiner: str, diagnosis: str, mkb_code: str, outcome: str, evacuation_place: str, full_epicrisis: dict) -> int:
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""INSERT INTO visits (patient_id, visit_datetime, vid_priema, obschsost, soznanie, examiner, diagnosis, mkb_code, outcome, evacuation_place, full_epicrisis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (patient_id, visit_datetime, vid_priema, obschsost, soznanie, examiner, diagnosis, mkb_code, outcome, evacuation_place, json.dumps(full_epicrisis, ensure_ascii=False)))
        conn.commit()
        return cur.lastrowid

def get_visit_by_id(vid: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT v.*, p.fio AS patient_fio, p.patient_number, p.phone, p.organisation FROM visits v LEFT JOIN patients p ON p.id=v.patient_id WHERE v.id=?", (vid,))
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get('full_epicrisis'):
            try:
                data['full_epicrisis'] = json.loads(data['full_epicrisis'])
            except Exception:
                pass
        return data

def list_visits_between(start_date: str, end_date: str):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""SELECT v.*, p.fio AS patient_fio, p.patient_number FROM visits v LEFT JOIN patients p ON p.id=v.patient_id WHERE visit_datetime BETWEEN ? AND ? ORDER BY visit_datetime DESC""", (start_date, end_date))
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get('full_epicrisis'):
                try:
                    r['full_epicrisis'] = json.loads(r['full_epicrisis'])
                except Exception:
                    pass
        return rows

def list_visits_for_date(date_iso: str):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""SELECT v.id, v.visit_datetime, p.fio AS patient_fio, v.mkb_code FROM visits v LEFT JOIN patients p ON p.id=v.patient_id WHERE date(v.visit_datetime) = date(?) ORDER BY v.visit_datetime ASC""", (date_iso,))
        return [dict(r) for r in cur.fetchall()]

def list_all_visits(limit=1000):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""SELECT v.*, p.fio AS patient_fio, p.patient_number FROM visits v LEFT JOIN patients p ON p.id=v.patient_id ORDER BY visit_datetime DESC LIMIT ?""", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get('full_epicrisis'):
                try:
                    r['full_epicrisis'] = json.loads(r['full_epicrisis'])
                except Exception:
                    pass
        return rows
