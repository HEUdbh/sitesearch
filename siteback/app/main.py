from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import uuid
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.handleofa import run_oneforall_task
from model.database import insert_task, update_task, get_task, get_all_tasks

app = Flask(__name__)

# 配置CORS，允许所有来源的跨域请求
CORS(app, supports_credentials=True)

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
    
    # 如果提供了taskid参数，返回单个任务信息（不包含result和error字段）
    if task_id:
        info = get_task(task_id)
        if info:
            # 过滤掉result和error字段
            filtered_info = {key: value for key, value in info.items() if key not in ['result', 'error']}
            return jsonify(filtered_info)
        else:
            return jsonify({'error': 'Task not found'}), 404
    
    # 如果没有提供taskid参数，返回所有任务信息（不包含result和error字段）
    all_tasks = get_all_tasks()
    # 过滤掉每个任务的result和error字段
    filtered_tasks = []
    for task in all_tasks:
        filtered_task = {key: value for key, value in task.items() if key not in ['result', 'error']}
        filtered_tasks.append(filtered_task)
    
    return jsonify({'tasks': filtered_tasks, 'count': len(filtered_tasks)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)