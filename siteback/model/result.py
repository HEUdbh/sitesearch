import os
import sqlite3
import pandas as pd
import json
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), 'tasks.db')

def get_task_result_path(task_id):
    """根据任务ID获取结果文件路径"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT result FROM task_info WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        return row[0]
    return None

def read_csv_result(file_path):
    """读取CSV格式的结果文件"""
    try:
        if not os.path.exists(file_path):
            return None
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 转换为字典列表
        results = df.to_dict('records')
        
        return {
            'format': 'csv',
            'count': len(results),
            'data': results
        }
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return None

def read_json_result(file_path):
    """读取JSON格式的结果文件"""
    try:
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'format': 'json',
            'count': len(data) if isinstance(data, list) else 1,
            'data': data
        }
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return None

def read_txt_result(file_path):
    """读取TXT格式的结果文件"""
    try:
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 清理空行
        lines = [line.strip() for line in lines if line.strip()]
        
        return {
            'format': 'txt',
            'count': len(lines),
            'data': lines
        }
    except Exception as e:
        print(f"读取TXT文件失败: {e}")
        return None

def get_task_result(task_id):
    """获取任务结果数据"""
    # 获取结果文件路径
    result_path = get_task_result_path(task_id)
    
    if not result_path:
        return {
            'success': False,
            'error': '任务结果文件路径不存在或任务未完成'
        }
    
    # 检查文件是否存在
    if not os.path.exists(result_path):
        return {
            'success': False,
            'error': '结果文件不存在'
        }
    
    # 根据文件扩展名选择读取方法
    file_extension = Path(result_path).suffix.lower()
    
    result_data = None
    if file_extension == '.csv':
        result_data = read_csv_result(result_path)
    elif file_extension == '.json':
        result_data = read_json_result(result_path)
    elif file_extension in ['.txt', '.log']:
        result_data = read_txt_result(result_path)
    else:
        # 尝试自动检测文件格式
        result_data = read_csv_result(result_path) or \
                     read_json_result(result_path) or \
                     read_txt_result(result_path)
    
    if result_data:
        return {
            'success': True,
            'task_id': task_id,
            **result_data
        }
    else:
        return {
            'success': False,
            'error': '无法读取结果文件或文件格式不支持'
        }

def get_result_summary(task_id):
    """获取结果摘要信息（不包含详细数据）"""
    result_path = get_task_result_path(task_id)
    
    if not result_path or not os.path.exists(result_path):
        return None
    
    file_extension = Path(result_path).suffix.lower()
    file_size = os.path.getsize(result_path)
    
    # 尝试获取记录数量
    record_count = 0
    try:
        if file_extension == '.csv':
            df = pd.read_csv(result_path)
            record_count = len(df)
        elif file_extension == '.json':
            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                record_count = len(data) if isinstance(data, list) else 1
        elif file_extension in ['.txt', '.log']:
            with open(result_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                record_count = len([line for line in lines if line.strip()])
    except:
        record_count = 0
    
    return {
        'task_id': task_id,
        'file_path': result_path,
        'file_size': file_size,
        'format': file_extension.lstrip('.'),
        'record_count': record_count,
        'exists': True
    }