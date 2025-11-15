#!/usr/bin/python3
# coding=utf-8

import os
import sys
import subprocess
import time
import json
import threading
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class OneForAllHandler:
    def __init__(self):
        # OneForAll 脚本的路径
        self.oneforall_path = os.path.abspath(r'e:\project\sitesearch\OneForAll\oneforall.py')
        # 确保路径存在
        if not os.path.exists(self.oneforall_path):
            raise FileNotFoundError(f"OneForAll脚本未找到: {self.oneforall_path}")
        
        # 保存任务信息的字典
        self.tasks = {}
        # 线程锁，确保对tasks字典的线程安全访问
        self.tasks_lock = threading.Lock()
        # 线程池，用于管理异步任务
        self.executor = ThreadPoolExecutor(max_workers=5)  # 可根据需要调整最大工作线程数
    
    def _execute_oneforall(self, task_id, cmd):
        """
        在线程中执行OneForAll命令
        
        参数:
            task_id: 任务ID
            cmd: 要执行的命令
        """
        with self.tasks_lock:
            # 获取任务信息的本地副本
            task = self.tasks.get(task_id)
            if not task:
                return
        
        try:
            # 启动子进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(self.oneforall_path)
            )
            
            # 更新任务信息
            with self.tasks_lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['pid'] = process.pid
            
            # 读取输出
            stdout_lines = []
            stderr_lines = []
            
            # 实时读取并更新输出
            while True:
                # 非阻塞读取
                stdout_line = process.stdout.readline()
                if stdout_line:
                    line = stdout_line.strip()
                    stdout_lines.append(line)
                    print(f"[{task_id}] {line}")  # 可选：打印到控制台
                    # 更新任务输出
                    with self.tasks_lock:
                        if task_id in self.tasks:
                            self.tasks[task_id]['output'].append(line)
                
                stderr_line = process.stderr.readline()
                if stderr_line:
                    line = stderr_line.strip()
                    stderr_lines.append(line)
                    print(f"[{task_id} ERROR] {line}")  # 可选：打印错误到控制台
                    # 更新任务错误输出
                    with self.tasks_lock:
                        if task_id in self.tasks:
                            self.tasks[task_id]['error'].append(line)
                
                # 检查进程是否完成
                if process.poll() is not None and not stdout_line and not stderr_line:
                    break
            
            # 更新任务状态
            with self.tasks_lock:
                if task_id in self.tasks:
                    if process.returncode == 0:
                        self.tasks[task_id]['status'] = 'completed'
                    else:
                        self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.tasks[task_id]['return_code'] = process.returncode
                    
        except Exception as e:
            error_msg = str(e)
            with self.tasks_lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'error'
                    self.tasks[task_id]['error'].append(error_msg)
                    self.tasks[task_id]['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{task_id} ERROR] {error_msg}")
    
    def run_oneforall(self, target=None, targets=None, brute=True, dns=True, req=True,
                     port='small', alive=False, fmt='csv', path=None, takeover=False):
        """
        异步运行 OneForAll 脚本
        
        参数与 OneForAll 类的参数对应
        
        返回:
            dict: 包含任务ID和状态的字典
        """
        # 验证必要参数
        if not target and not targets:
            return {"error": "必须提供target或targets参数"}
        
        # 生成唯一的任务ID（使用UUID确保唯一性）
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        # 构建命令行参数
        cmd = [sys.executable, self.oneforall_path]
        
        if target:
            cmd.extend(['--target', target])
        elif targets:
            cmd.extend(['--targets', targets])
        
        # 添加其他参数
        cmd.extend(['--brute', str(brute)])
        cmd.extend(['--dns', str(dns)])
        cmd.extend(['--req', str(req)])
        cmd.extend(['--port', port])
        cmd.extend(['--alive', str(alive)])
        cmd.extend(['--fmt', fmt])
        
        if path:
            cmd.extend(['--path', path])
        
        cmd.extend(['--takeover', str(takeover)])
        cmd.append('run')
        
        # 保存任务信息
        task_info = {
            'command': cmd,
            'status': 'running',
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pid': None,
            'output': [],
            'error': [],
            'return_code': None,
            'target': target,
            'targets': targets
        }
        
        with self.tasks_lock:
            self.tasks[task_id] = task_info
        
        # 提交任务到线程池
        try:
            self.executor.submit(self._execute_oneforall, task_id, cmd)
            return {
                "task_id": task_id,
                "status": "running",
                "message": "OneForAll任务已成功提交并开始执行"
            }
        except Exception as e:
            error_msg = str(e)
            with self.tasks_lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'error'
                    self.tasks[task_id]['error'].append(error_msg)
                    self.tasks[task_id]['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return {
                "task_id": task_id,
                "status": "error",
                "message": f"提交任务时出错: {error_msg}"
            }
    
    def get_task_status(self, task_id):
        """
        获取任务状态
        
        参数:
            task_id: 任务ID
        
        返回:
            dict: 任务状态信息
        """
        with self.tasks_lock:
            if task_id not in self.tasks:
                return {"error": "任务ID不存在"}
            # 返回任务信息的副本，避免并发访问问题
            return dict(self.tasks[task_id])
    
    def stop_task(self, task_id):
        """
        停止指定的任务
        
        参数:
            task_id: 任务ID
        
        返回:
            dict: 操作结果
        """
        with self.tasks_lock:
            if task_id not in self.tasks:
                return {"error": "任务ID不存在"}
            
            task = self.tasks[task_id]
            
            if task['status'] not in ['running']:
                return {"error": "任务不在运行状态"}
            
            pid = task.get('pid')
            if not pid:
                return {"error": "任务进程ID未知，无法停止"}
        
        try:
            # 在Windows上使用taskkill
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], check=True)
            else:
                # 在Unix/Linux上使用kill
                import signal
                os.kill(pid, signal.SIGTERM)
                
            # 更新任务状态
            with self.tasks_lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'stopped'
                    self.tasks[task_id]['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {"message": "任务已成功停止"}
        except Exception as e:
            return {"error": f"停止任务时出错: {str(e)}"}
    
    def list_tasks(self):
        """
        列出所有任务
        
        返回:
            dict: 包含所有任务信息的字典
        """
        with self.tasks_lock:
            # 返回任务信息的副本
            return {task_id: dict(task_info) for task_id, task_info in self.tasks.items()}
    
    def cleanup_tasks(self, days=7):
        """
        清理旧任务
        
        参数:
            days: 保留多少天内的任务记录
        """
        import time
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        with self.tasks_lock:
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                # 检查任务是否已完成且超过保留时间
                if task['status'] in ['completed', 'failed', 'stopped', 'error']:
                    # 计算任务结束时间的时间戳
                    end_time_str = task.get('end_time')
                    if end_time_str:
                        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                        if end_time.timestamp() < cutoff_time:
                            tasks_to_remove.append(task_id)
            
            # 移除旧任务
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
            
            return {"message": f"已清理 {len(tasks_to_remove)} 个旧任务"}

# 创建全局实例
oneforall_handler = OneForAllHandler()

# 测试函数
def test_handler():
    """
    测试OneForAllHandler
    """
    handler = OneForAllHandler()
    result = handler.run_oneforall(target='example.com', brute=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    # 运行测试
    test_handler()