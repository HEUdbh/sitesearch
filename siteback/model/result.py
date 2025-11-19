import sqlite3
import os
from typing import Dict, List, Any, Optional

def get_task_result(domain: str) -> Dict[str, Any]:
    """
    根据域名从 OneForAll 数据库获取子域名扫描结果
    
    Args:
        domain: 目标域名，如 "baidu.com"
        
    Returns:
        包含查询结果的字典，包含 success 状态和 data 数据
    """
    # 数据库文件路径（相对路径）
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "OneForAll", "results", "result.sqlite3")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        return {
            "success": False,
            "error": f"数据库文件不存在: {db_path}",
            "data": []
        }
    
    # 将域名中的点替换为下划线作为表名
    table_name = domain.replace('.', '_')
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 启用行工厂，方便转换为字典
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone()
        
        if not table_exists:
            return {
                "success": False,
                "error": f"域名 {domain} 对应的表 {table_name} 不存在",
                "data": []
            }
        
        # 查询表中的所有数据
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # 将查询结果转换为字典列表
        data = []
        for row in rows:
            # 将 sqlite3.Row 对象转换为字典
            row_dict = dict(row)
            data.append(row_dict)
        
        # 关闭连接
        conn.close()
        
        return {
            "success": True,
            "domain": domain,
            "table_name": table_name,
            "count": len(data),
            "data": data
        }
        
    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"数据库查询错误: {str(e)}",
            "data": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}",
            "data": []
        }

def get_available_domains() -> List[str]:
    """
    获取数据库中所有可用的域名（表名）
    
    Returns:
        域名列表
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "OneForAll", "results", "result.sqlite3")
    
    if not os.path.exists(db_path):
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # 将表名转换回域名格式（将下划线替换为点）
        domains = [table[0].replace('_', '.') for table in tables]
        
        conn.close()
        return domains
        
    except sqlite3.Error:
        return []

# 测试函数
if __name__ == "__main__":
    # 测试获取可用域名
    domains = get_available_domains()
    print("可用域名:", domains)
    
    # 测试查询特定域名的数据
    if domains:
        test_domain = domains[0]
        result = get_task_result(test_domain)
        print(f"查询 {test_domain} 的结果:")
        print(f"成功: {result['success']}")
        print(f"数据条数: {result.get('count', 0)}")
        if result['success'] and result['data']:
            print("第一条数据示例:")
            print(result['data'][0])