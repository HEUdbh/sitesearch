"""
OneForAll进度监测模块
提供扫描任务的实时进度监测功能
"""

import os
import time
import threading
from datetime import datetime
from model.database import get_task

# 全局变量存储任务进度信息
task_progress = {}

class TaskProgressMonitor:
    """任务进度监测器"""
    
    def __init__(self, task_id):
        self.task_id = task_id
        self.start_time = None
        self.current_stage = "pending"  # pending, running, completed, failed
        self.progress_percentage = 0
        self.current_module = ""
        self.subdomains_found = 0
        self.elapsed_time = 0
        self.estimated_remaining_time = 0
        self.last_update_time = None
        
    def start_monitoring(self):
        """开始监测任务"""
        self.start_time = datetime.now()
        self.current_stage = "running"
        self.last_update_time = datetime.now()
        
        # 将任务添加到全局进度字典
        task_progress[self.task_id] = self
        
    def update_progress(self, module_name, progress_percentage, subdomains_count=0):
        """更新任务进度"""
        self.current_module = module_name
        self.progress_percentage = progress_percentage
        self.subdomains_found = subdomains_count
        self.last_update_time = datetime.now()
        
        # 计算已用时间
        if self.start_time:
            self.elapsed_time = (datetime.now() - self.start_time).total_seconds()
            
            # 估算剩余时间（基于当前进度）
            if progress_percentage > 0:
                total_estimated_time = self.elapsed_time / (progress_percentage / 100)
                self.estimated_remaining_time = max(0, total_estimated_time - self.elapsed_time)
        
    def complete_task(self):
        """标记任务完成"""
        self.current_stage = "completed"
        self.progress_percentage = 100
        self.elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.estimated_remaining_time = 0
        
    def fail_task(self, error_message):
        """标记任务失败"""
        self.current_stage = "failed"
        self.current_module = f"错误: {error_message}"
        self.elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
    def get_progress_info(self):
        """获取进度信息"""
        # 从数据库获取任务基本信息
        task_info = get_task(self.task_id)
        
        if not task_info:
            return {
                'success': False,
                'error': '任务不存在'
            }
        
        progress_info = {
            'success': True,
            'task_id': self.task_id,
            'status': self.current_stage,
            'progress_percentage': self.progress_percentage,
            'current_module': self.current_module,
            'subdomains_found': self.subdomains_found,
            'elapsed_time': int(self.elapsed_time),
            'estimated_remaining_time': int(self.estimated_remaining_time),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'target': task_info.get('target'),
            'database_status': task_info.get('status')
        }
        
        return progress_info

def get_task_progress(task_id):
    """获取任务进度信息"""
    
    # 检查任务是否在进度监测中
    if task_id in task_progress:
        monitor = task_progress[task_id]
        return monitor.get_progress_info()
    
    # 如果任务不在进度监测中，从数据库获取基本信息
    task_info = get_task(task_id)
    
    if not task_info:
        return {
            'success': False,
            'error': '任务不存在'
        }
    
    # 根据数据库状态返回基本信息
    status = task_info.get('status', 'unknown')
    
    if status == 'completed':
        progress_percentage = 100
        current_module = "任务已完成"
    elif status == 'failed':
        progress_percentage = 0
        current_module = f"任务失败: {task_info.get('error', '未知错误')}"
    elif status == 'running':
        progress_percentage = 50  # 默认进度
        current_module = "扫描进行中"
    else:
        progress_percentage = 0
        current_module = "任务等待中"
    
    return {
        'success': True,
        'task_id': task_id,
        'status': status,
        'progress_percentage': progress_percentage,
        'current_module': current_module,
        'subdomains_found': 0,
        'elapsed_time': 0,
        'estimated_remaining_time': 0,
        'target': task_info.get('target'),
        'database_status': status,
        'message': '任务未启用详细进度监测'
    }

def simulate_progress_monitoring(task_id, target_domain):
    """模拟进度监测（用于演示和测试）"""
    
    if task_id not in task_progress:
        monitor = TaskProgressMonitor(task_id)
        monitor.start_monitoring()
    else:
        monitor = task_progress[task_id]
    
    # 模拟OneForAll扫描进度
    modules = [
        ("DNS解析", 10),
        ("子域名爆破", 30),
        ("HTTP请求", 60),
        ("端口扫描", 80),
        ("存活检测", 95),
        ("结果导出", 100)
    ]
    
    subdomain_counts = [5, 25, 50, 75, 90, 100]  # 模拟发现的子域名数量
    
    for i, (module_name, progress) in enumerate(modules):
        monitor.update_progress(module_name, progress, subdomain_counts[i])
        time.sleep(2)  # 模拟每个模块执行时间
    
    monitor.complete_task()
    return monitor