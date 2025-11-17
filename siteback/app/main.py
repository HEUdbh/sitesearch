from flask import Flask, request, jsonify
import threading
import uuid
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.handleofa import run_oneforall_task
from model.database import insert_task, update_task, get_task

app = Flask(__name__)

tasks = {}

def run_task_and_update_db(task_id, params, tasks_dict):
    try:
        run_oneforall_task(task_id, params, tasks_dict)
        # handleofa.py中的run_oneforall_task函数已经负责更新数据库状态
        # 这里不需要再次调用update_task，避免重复更新
    except Exception as e:
        # 如果handleofa.py中的异常处理失败，这里作为最后的保障
        update_task(task_id, 'failed', None, str(e))

@app.route('/api/run', methods=['POST'])
def api_run():
    try:
        data = request.get_json(force=True)
        oneforall_args = {
            'target': data.get('target'),
            'targets': data.get('targets'),
            'brute': data.get('brute'),
            'dns': data.get('dns'),
            'req': data.get('req'),
            'port': data.get('port'),
            'alive': data.get('alive'),
            'fmt': data.get('fmt'),
            'path': data.get('path'),
            'takeover': data.get('takeover')
        }
        task_id = str(uuid.uuid4())
        insert_task(task_id, oneforall_args)
        thread = threading.Thread(target=run_task_and_update_db, args=(task_id, oneforall_args, tasks))
        thread.start()
        return jsonify({'task_id': task_id, 'accepted': True})
    except Exception as e:
        return jsonify({'error': str(e), 'accepted': False}), 400

@app.route('/api/task', methods=['GET'])
def api_task():
    task_id = request.args.get('taskid')
    if not task_id:
        return jsonify({'error': 'Missing taskid parameter'}), 400
    info = get_task(task_id)
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)