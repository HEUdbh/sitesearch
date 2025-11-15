#!/usr/bin/python3
# coding=utf-8

from flask import Flask, request, jsonify, g
import os
import sys
import threading
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入OneForAll处理器
from siteback.code.handleofa import oneforall_handler

# 创建Flask应用实例
app = Flask(__name__)

# 配置CORS（允许跨域请求）
from flask_cors import CORS
CORS(app)

@app.route('/')
def index():
    """
    API根路径，提供基本信息
    """
    return jsonify({
        "message": "OneForAll API服务运行中",
        "version": "1.0",
        "endpoints": {
            "run": "POST /api/run - 异步运行OneForAll子域名收集",
            "status": "GET /api/status/<task_id> - 获取任务状态",
            "stop": "POST /api/stop/<task_id> - 停止任务",
            "tasks": "GET /api/tasks - 列出所有任务",
            "cleanup": "POST /api/cleanup - 清理旧任务"
        }
    })

@app.route('/api/run', methods=['POST'])
def run_oneforall():
    """
    异步运行OneForAll子域名收集工具
    
    POST参数:
    - target: 单个目标域名 (与targets二选一)
    - targets: 包含多个域名的文件路径 (与target二选一)
    - brute: 是否使用暴力破解模块 (默认: true)
    - dns: 是否进行DNS解析 (默认: true)
    - req: 是否进行HTTP请求 (默认: true)
    - port: HTTP请求的端口范围 (默认: 'small')
    - alive: 是否只导出存活的子域名 (默认: false)
    - fmt: 结果格式 (默认: 'csv')
    - path: 结果保存路径 (可选)
    - takeover: 是否扫描子域名接管漏洞 (默认: false)
    """
    try:
        # 获取请求数据
        data = request.json or request.form.to_dict()
        
        # 提取参数
        target = data.get('target')
        targets = data.get('targets')
        brute = data.get('brute', 'true').lower() == 'true'
        dns = data.get('dns', 'true').lower() == 'true'
        req = data.get('req', 'true').lower() == 'true'
        port = data.get('port', 'small')
        alive = data.get('alive', 'false').lower() == 'true'
        fmt = data.get('fmt', 'csv')
        path = data.get('path')
        takeover = data.get('takeover', 'false').lower() == 'true'
        
        # 记录请求信息
        request_id = f"req_{threading.get_ident()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"[{request_id}] 接收到OneForAll执行请求: target={target}, targets={targets}")
        
        # 运行OneForAll（异步执行）
        result = oneforall_handler.run_oneforall(
            target=target,
            targets=targets,
            brute=brute,
            dns=dns,
            req=req,
            port=port,
            alive=alive,
            fmt=fmt,
            path=path,
            takeover=takeover
        )
        
        # 检查是否有错误
        if 'error' in result:
            logger.error(f"[{request_id}] 任务提交失败: {result['error']}")
            return jsonify({
                "error": result['error'],
                "status": "error"
            }), 400
        
        logger.info(f"[{request_id}] 任务已成功提交: task_id={result['task_id']}")
        return jsonify({
            "message": "OneForAll任务已成功提交并异步执行",
            "data": result,
            "status": "success"
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"处理请求时发生异常: {error_msg}", exc_info=True)
        return jsonify({
            "error": f"处理请求时出错: {error_msg}",
            "status": "error"
        }), 500

@app.route('/api/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    获取任务状态
    
    路径参数:
    - task_id: 任务ID
    """
    try:
        logger.info(f"请求获取任务状态: task_id={task_id}")
        
        # 获取任务状态（现在是线程安全的）
        status = oneforall_handler.get_task_status(task_id)
        
        # 检查是否有错误
        if 'error' in status:
            logger.warning(f"任务不存在: task_id={task_id}")
            return jsonify({
                "error": status['error'],
                "status": "error"
            }), 404
        
        # 确保返回的信息不包含敏感数据（如完整命令行参数）
        safe_status = dict(status)
        # 可以根据需要过滤掉敏感信息
        
        logger.info(f"成功获取任务状态: task_id={task_id}, status={status.get('status')}")
        return jsonify({
            "message": "获取任务状态成功",
            "data": safe_status,
            "status": "success"
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取任务状态时发生异常: task_id={task_id}, error={error_msg}", exc_info=True)
        return jsonify({
            "error": f"获取任务状态时出错: {error_msg}",
            "status": "error"
        }), 500

@app.route('/api/stop/<task_id>', methods=['POST'])
def stop_task(task_id):
    """
    停止指定的任务
    
    路径参数:
    - task_id: 任务ID
    """
    try:
        logger.info(f"请求停止任务: task_id={task_id}")
        
        # 停止任务（现在是线程安全的）
        result = oneforall_handler.stop_task(task_id)
        
        # 检查是否有错误
        if 'error' in result:
            logger.warning(f"停止任务失败: task_id={task_id}, error={result['error']}")
            return jsonify({
                "error": result['error'],
                "status": "error"
            }), 400
        
        logger.info(f"任务已成功停止: task_id={task_id}")
        return jsonify({
            "message": result['message'],
            "status": "success"
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"停止任务时发生异常: task_id={task_id}, error={error_msg}", exc_info=True)
        return jsonify({
            "error": f"停止任务时出错: {error_msg}",
            "status": "error"
        }), 500

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """
    列出所有任务
    
    返回所有任务的状态信息
    """
    try:
        logger.info("请求列出所有任务")
        
        # 获取所有任务（线程安全）
        tasks = oneforall_handler.list_tasks()
        
        # 统计不同状态的任务数量
        status_count = {}
        for task_info in tasks.values():
            status = task_info.get('status')
            status_count[status] = status_count.get(status, 0) + 1
        
        logger.info(f"成功获取任务列表，共 {len(tasks)} 个任务")
        return jsonify({
            "message": "获取任务列表成功",
            "data": {
                "tasks": tasks,
                "count": len(tasks),
                "status_summary": status_count
            },
            "status": "success"
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取任务列表时发生异常: {error_msg}", exc_info=True)
        return jsonify({
            "error": f"获取任务列表时出错: {error_msg}",
            "status": "error"
        }), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_tasks():
    """
    清理旧任务
    
    POST参数:
    - days: 保留多少天内的任务记录（可选，默认7天）
    """
    try:
        # 获取请求数据
        data = request.json or request.form.to_dict()
        days = int(data.get('days', 7))
        
        logger.info(f"请求清理旧任务，保留 {days} 天内的记录")
        
        # 执行清理操作
        result = oneforall_handler.cleanup_tasks(days=days)
        
        logger.info(result['message'])
        return jsonify({
            "message": result['message'],
            "status": "success"
        })
        
    except ValueError:
        logger.warning("无效的days参数，必须是整数")
        return jsonify({
            "error": "days参数必须是有效的整数",
            "status": "error"
        }), 400
    except Exception as e:
        error_msg = str(e)
        logger.error(f"清理任务时发生异常: {error_msg}", exc_info=True)
        return jsonify({
            "error": f"清理任务时出错: {error_msg}",
            "status": "error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """
    处理404错误
    """
    return jsonify({
        "error": "请求的资源不存在",
        "status": "error"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """
    处理405错误
    """
    return jsonify({
        "error": "不允许的请求方法",
        "status": "error"
    }), 405

# 添加请求处理钩子，用于资源清理
@app.teardown_appcontext
def cleanup_appcontext(exception):
    """
    应用上下文销毁时执行的清理操作
    """
    # 这里可以添加一些清理操作，例如关闭资源连接等
    pass

if __name__ == '__main__':
    # 获取环境变量中的配置，默认为开发模式
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    # 如果在生产环境运行，禁用调试模式
    if os.environ.get('FLASK_ENV') == 'production':
        debug = False
    
    # 启动Flask应用
    logger.info(f"启动OneForAll API服务在 http://{host}:{port}")
    logger.info(f"调试模式: {debug}")
    logger.info("可用端点:")
    logger.info("  - POST /api/run - 异步运行OneForAll子域名收集")
    logger.info("  - GET /api/status/<task_id> - 获取任务状态")
    logger.info("  - POST /api/stop/<task_id> - 停止任务")
    logger.info("  - GET /api/tasks - 列出所有任务")
    logger.info("  - POST /api/cleanup - 清理旧任务")
    
    # 在开发模式下也打印到控制台
    if debug:
        print(f"启动OneForAll API服务在 http://{host}:{port}")
        print(f"调试模式: {debug}")
        print("可用端点:")
        print("  - POST /api/run - 异步运行OneForAll子域名收集")
        print("  - GET /api/status/<task_id> - 获取任务状态")
        print("  - POST /api/stop/<task_id> - 停止任务")
        print("  - GET /api/tasks - 列出所有任务")
        print("  - POST /api/cleanup - 清理旧任务")
    
    # 启动应用
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在优雅关闭服务...")
    finally:
        logger.info("服务已停止")
        # 可以在这里添加额外的清理操作，例如关闭线程池等
        # oneforall_handler.executor.shutdown(wait=True)
        pass