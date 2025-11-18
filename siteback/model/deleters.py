"""
扫描结果文件定时删除模块
定时删除OneForAll扫描结果文件，保留时间为24小时
"""

import os
import time
import threading
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResultFileCleaner:
    """扫描结果文件清理器"""
    
    def __init__(self, results_dir: str, retention_hours: int = 24):
        """
        初始化清理器
        
        Args:
            results_dir: 扫描结果目录路径
            retention_hours: 文件保留时间（小时），默认24小时
        """
        self.results_dir = results_dir
        self.retention_hours = retention_hours
        self.cleanup_interval = 3600  # 清理间隔（秒），默认1小时
        self.is_running = False
        self.cleanup_thread = None
        
    def should_delete_file(self, file_path: str) -> bool:
        """
        判断文件是否应该被删除
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 如果文件应该被删除返回True
        """
        try:
            # 获取文件修改时间
            file_mtime = os.path.getmtime(file_path)
            file_age_hours = (time.time() - file_mtime) / 3600
            
            # 如果文件年龄超过保留时间，则删除
            return file_age_hours > self.retention_hours
            
        except (OSError, Exception) as e:
            logger.warning(f"无法获取文件信息 {file_path}: {e}")
            return False
    
    def cleanup_old_files(self):
        """清理过期文件"""
        try:
            if not os.path.exists(self.results_dir):
                logger.warning(f"扫描结果目录不存在: {self.results_dir}")
                return
            
            deleted_count = 0
            total_size = 0
            
            # 遍历结果目录
            for root, dirs, files in os.walk(self.results_dir):
                # 跳过temp目录
                if 'temp' in dirs:
                    dirs.remove('temp')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if self.should_delete_file(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size += file_size
                            logger.info(f"已删除过期文件: {file_path} (大小: {file_size} bytes)")
                        except (OSError, Exception) as e:
                            logger.error(f"删除文件失败 {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"清理完成: 删除了 {deleted_count} 个文件，释放了 {total_size} bytes 空间")
            else:
                logger.info("没有需要清理的过期文件")
                
        except Exception as e:
            logger.error(f"清理过程中发生错误: {e}")
    
    def cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                self.cleanup_old_files()
                # 等待下一个清理周期
                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"清理循环错误: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    def start_cleanup(self):
        """启动定时清理"""
        if self.is_running:
            logger.warning("清理器已经在运行中")
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self.cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info(f"扫描结果文件清理器已启动，保留时间: {self.retention_hours}小时，清理间隔: {self.cleanup_interval}秒")
    
    def stop_cleanup(self):
        """停止定时清理"""
        if not self.is_running:
            logger.warning("清理器未在运行")
            return
        
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=10)
        logger.info("扫描结果文件清理器已停止")
    
    def get_cleanup_status(self) -> dict:
        """获取清理器状态"""
        return {
            'is_running': self.is_running,
            'results_dir': self.results_dir,
            'retention_hours': self.retention_hours,
            'cleanup_interval': self.cleanup_interval
        }

# 全局清理器实例
_cleaner_instance = None

def init_cleaner(results_dir: str, retention_hours: int = 24):
    """初始化全局清理器"""
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = ResultFileCleaner(results_dir, retention_hours)
    return _cleaner_instance

def start_cleanup_service():
    """启动清理服务"""
    global _cleaner_instance
    if _cleaner_instance:
        _cleaner_instance.start_cleanup()

def stop_cleanup_service():
    """停止清理服务"""
    global _cleaner_instance
    if _cleaner_instance:
        _cleaner_instance.stop_cleanup()

def get_cleanup_status() -> dict:
    """获取清理服务状态"""
    global _cleaner_instance
    if _cleaner_instance:
        return _cleaner_instance.get_cleanup_status()
    return {'is_running': False, 'error': '清理器未初始化'}

def manual_cleanup():
    """手动执行一次清理"""
    global _cleaner_instance
    if _cleaner_instance:
        _cleaner_instance.cleanup_old_files()
    else:
        logger.error("清理器未初始化，无法执行手动清理")

# 初始化清理器（在模块导入时自动初始化）
def _auto_init():
    """自动初始化清理器"""
    try:
        # 获取OneForAll结果目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.abspath(os.path.join(current_dir, '../OneForAll/results'))
        
        init_cleaner(results_dir)
        logger.info(f"自动初始化清理器，结果目录: {results_dir}")
    except Exception as e:
        logger.error(f"自动初始化清理器失败: {e}")

# 模块导入时自动初始化
_auto_init()