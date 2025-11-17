import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'tasks.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_info (
            id TEXT PRIMARY KEY,
            target TEXT,
            targets TEXT,
            brute INTEGER,
            dns INTEGER,
            req INTEGER,
            port TEXT,
            alive INTEGER,
            fmt TEXT,
            path TEXT,
            takeover INTEGER,
            status TEXT,
            result TEXT,
            error TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_task(task_id, params):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO task_info (id, target, targets, brute, dns, req, port, alive, fmt, path, takeover, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        task_id,
        params.get('target'),
        params.get('targets'),
        int(bool(params.get('brute'))),
        int(bool(params.get('dns'))),
        int(bool(params.get('req'))),
        params.get('port'),
        int(bool(params.get('alive'))),
        params.get('fmt'),
        params.get('path'),
        int(bool(params.get('takeover'))),
        'pending'
    ))
    conn.commit()
    conn.close()

def update_task(task_id, status, result=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE task_info SET status=?, result=?, error=? WHERE id=?
    ''', (status, result, error, task_id))
    conn.commit()
    conn.close()

def get_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM task_info WHERE id=?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        columns = [
            'id', 'target', 'targets', 'brute', 'dns', 'req', 'port', 'alive',
            'fmt', 'path', 'takeover', 'status', 'result', 'error'
        ]
        return dict(zip(columns, row))
    return None

def get_all_tasks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM task_info ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    columns = [
        'id', 'target', 'targets', 'brute', 'dns', 'req', 'port', 'alive',
        'fmt', 'path', 'takeover', 'status', 'result', 'error'
    ]
    
    tasks = []
    for row in rows:
        task_dict = dict(zip(columns, row))
        tasks.append(task_dict)
    
    return tasks

init_db()