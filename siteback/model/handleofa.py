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
        ofa.config_param()
        ofa.check_param()
        # 使用 utils 模块获取域名
        ofa.domains = utils.get_domains(ofa.target, ofa.targets)
        results = []
        for domain in ofa.domains:
            ofa.domain = utils.get_main_domain(domain)
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
        
        # 更新任务状态为成功，并记录结果文件路径
        update_task(task_id, 'success', str(result_path))
        
    except Exception as e:
        # 记录任务错误
        tasks_dict[task_id] = {'status': 'error', 'error': str(e)}
        # 更新任务状态为失败
        update_task(task_id, 'failed', None, str(e))