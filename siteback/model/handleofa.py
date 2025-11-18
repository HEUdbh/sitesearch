import sys
import os

# 添加 OneForAll 的绝对路径到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../OneForAll')))

# 导入 OneForAll 和 utils 模块
from OneForAll.oneforall import OneForAll
from OneForAll.common import utils

def run_oneforall_task(task_id, params, tasks_dict):
    try:
        from model.database import update_task
        from model.process import TaskProgressMonitor
        
        # 创建进度监测器
        monitor = TaskProgressMonitor(task_id)
        monitor.start_monitoring()
        
        # 更新任务状态为执行中
        update_task(task_id, 'running')
        
        # 创建 OneForAll 实例并配置参数
        ofa = OneForAll(
            target=params.get('target'),
            targets=params.get('targets'),
            brute=params.get('brute'),
            dns=params.get('dns'),
            req=params.get('req'),
            port=params.get('port'),
            alive=params.get('alive'),
            fmt=params.get('fmt'),
            path=params.get('path'),
            takeover=params.get('takeover')
        )
        
        # 禁用网络检查，允许在无网络环境下运行
        ofa.enable_check_network = False
        
        ofa.config_param()
        ofa.check_param()
        
        # 更新进度：参数配置完成
        monitor.update_progress("参数配置", 10)
        
        # 使用 utils 模块获取域名
        ofa.domains = utils.get_domains(ofa.target, ofa.targets)
        
        # 更新进度：域名解析完成
        monitor.update_progress("域名解析", 20, len(ofa.domains))
        
        results = []
        total_domains = len(ofa.domains)
        
        for i, domain in enumerate(ofa.domains):
            ofa.domain = utils.get_main_domain(domain)
            
            # 更新进度：当前域名处理中
            domain_progress = 20 + (i / total_domains) * 70
            monitor.update_progress(f"扫描域名: {domain}", int(domain_progress), i + 1)
            
            result = ofa.main()
            results.append(result)
        
        # 获取结果文件路径
        from OneForAll.config import settings
        import os
        
        # 生成结果文件路径 - 使用OneForAll的导出逻辑
        domain = params.get('target') or 'all_domains'
        fmt = params.get('fmt') or 'csv'
        
        # 使用OneForAll的check_path函数生成正确的文件路径
        result_path = utils.check_path(params.get('path'), domain, fmt)
        
        # 记录任务结果
        tasks_dict[task_id] = {
            'status': 'completed',
            'result': str(result_path)  # 转换为字符串存储
        }
        
        # 更新进度：任务完成
        monitor.update_progress("结果导出", 95)
        
        # 更新任务状态为成功，并记录结果文件路径
        update_task(task_id, 'completed', str(result_path))
        
        # 标记进度监测器为完成
        monitor.complete_task()
        
    except Exception as e:
        # 记录任务错误
        tasks_dict[task_id] = {'status': 'error', 'error': str(e)}
        # 更新任务状态为失败
        update_task(task_id, 'failed', None, str(e))
        
        # 标记进度监测器为失败
        if 'monitor' in locals():
            monitor.fail_task(str(e))