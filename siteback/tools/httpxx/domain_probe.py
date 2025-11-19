"""
httpx快速域名探活工具
支持多协议、多端口快速探活，获取响应状态码和页面标题
"""

import asyncio
import httpx
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DomainProbe:
    """域名探活工具类"""
    
    def __init__(self, timeout: int = 10, max_connections: int = 100):
        """
        初始化探活工具
        
        Args:
            timeout: 请求超时时间（秒）
            max_connections: 最大并发连接数
        """
        self.timeout = timeout
        self.max_connections = max_connections
        self.default_ports = {
            'http': 80,
            'https': 443
        }
        
        # 常用端口列表
        self.common_ports = [80, 443, 8080, 8443, 8000, 3000, 5000, 9000]
        
        # 支持的协议
        self.supported_protocols = ['http', 'https']
    
    async def probe_single_url(self, client: httpx.AsyncClient, url: str) -> Dict:
        """
        探测单个URL
        
        Args:
            client: httpx异步客户端
            url: 要探测的URL
            
        Returns:
            探测结果字典
        """
        result = {
            'url': url,
            'status_code': None,
            'title': None,
            'response_time': None,
            'error': None,
            'protocol': urlparse(url).scheme,
            'success': False
        }
        
        try:
            start_time = time.time()
            
            # 发送HEAD请求获取状态码（更快）
            head_response = await client.head(url, timeout=self.timeout, follow_redirects=True)
            result['status_code'] = head_response.status_code
            result['response_time'] = round(time.time() - start_time, 3)
            
            # 如果状态码是200，再发送GET请求获取标题
            if head_response.status_code == 200:
                get_response = await client.get(url, timeout=self.timeout, follow_redirects=True)
                
                # 从响应内容中提取标题
                if 'text/html' in get_response.headers.get('content-type', ''):
                    content = get_response.text
                    title_start = content.find('<title>')
                    title_end = content.find('</title>')
                    
                    if title_start != -1 and title_end != -1:
                        result['title'] = content[title_start + 7:title_end].strip()
                
                result['success'] = True
            else:
                result['success'] = True  # 即使不是200，也算探测成功
                
        except httpx.TimeoutException:
            result['error'] = '请求超时'
        except httpx.ConnectError:
            result['error'] = '连接失败'
        except httpx.HTTPStatusError as e:
            result['status_code'] = e.response.status_code
            result['error'] = f'HTTP错误: {e.response.status_code}'
            result['success'] = True  # 有状态码就算成功
        except Exception as e:
            result['error'] = f'探测失败: {str(e)}'
        
        return result
    
    def generate_urls(self, domain: str, protocols: List[str] = None, ports: List[int] = None) -> List[str]:
        """
        生成要探测的URL列表
        
        Args:
            domain: 域名
            protocols: 协议列表，默认['http', 'https']
            ports: 端口列表，默认常用端口
            
        Returns:
            URL列表
        """
        if protocols is None:
            protocols = self.supported_protocols
        
        if ports is None:
            ports = self.common_ports
        
        urls = []
        
        for protocol in protocols:
            if protocol not in self.supported_protocols:
                logger.warning(f"不支持的协议: {protocol}")
                continue
            
            # 添加默认端口URL
            default_port = self.default_ports.get(protocol)
            if default_port:
                if default_port == 80 and protocol == 'http':
                    urls.append(f"{protocol}://{domain}")
                elif default_port == 443 and protocol == 'https':
                    urls.append(f"{protocol}://{domain}")
                else:
                    urls.append(f"{protocol}://{domain}:{default_port}")
            
            # 添加其他端口URL
            for port in ports:
                if port != default_port:  # 避免重复添加默认端口
                    urls.append(f"{protocol}://{domain}:{port}")
        
        return urls
    
    async def probe_domain(self, domain: str, protocols: List[str] = None, 
                          ports: List[int] = None) -> List[Dict]:
        """
        探测单个域名的存活状态
        
        Args:
            domain: 域名
            protocols: 协议列表
            ports: 端口列表
            
        Returns:
            探测结果列表
        """
        urls = self.generate_urls(domain, protocols, ports)
        
        if not urls:
            logger.warning(f"没有生成有效的URL用于探测域名: {domain}")
            return []
        
        logger.info(f"开始探测域名 {domain}，共 {len(urls)} 个URL")
        
        # 创建异步客户端
        limits = httpx.Limits(max_connections=self.max_connections)
        
        async with httpx.AsyncClient(limits=limits, timeout=self.timeout) as client:
            tasks = [self.probe_single_url(client, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"探测过程中出现异常: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def probe_multiple_domains(self, domains: List[str], protocols: List[str] = None,
                                    ports: List[int] = None) -> Dict[str, List[Dict]]:
        """
        批量探测多个域名的存活状态
        
        Args:
            domains: 域名列表
            protocols: 协议列表
            ports: 端口列表
            
        Returns:
            按域名分组的探测结果字典
        """
        results = {}
        
        for domain in domains:
            domain_results = await self.probe_domain(domain, protocols, ports)
            results[domain] = domain_results
        
        return results
    
    def filter_alive_results(self, results: List[Dict]) -> List[Dict]:
        """
        过滤出存活的探测结果
        
        Args:
            results: 探测结果列表
            
        Returns:
            存活的探测结果列表
        """
        alive_results = []
        
        for result in results:
            if result.get('success') and result.get('status_code') is not None:
                alive_results.append(result)
        
        return alive_results
    
    def summarize_results(self, results: Dict[str, List[Dict]]) -> Dict:
        """
        汇总探测结果
        
        Args:
            results: 探测结果字典
            
        Returns:
            汇总信息
        """
        summary = {
            'total_domains': len(results),
            'total_urls_probed': 0,
            'alive_urls': 0,
            'alive_domains': 0,
            'common_status_codes': {},
            'average_response_time': 0
        }
        
        total_response_time = 0
        response_time_count = 0
        
        for domain, domain_results in results.items():
            summary['total_urls_probed'] += len(domain_results)
            
            alive_domain_results = self.filter_alive_results(domain_results)
            if alive_domain_results:
                summary['alive_domains'] += 1
                summary['alive_urls'] += len(alive_domain_results)
            
            for result in domain_results:
                if result.get('status_code'):
                    status_code = result['status_code']
                    summary['common_status_codes'][status_code] = summary['common_status_codes'].get(status_code, 0) + 1
                
                if result.get('response_time'):
                    total_response_time += result['response_time']
                    response_time_count += 1
        
        if response_time_count > 0:
            summary['average_response_time'] = round(total_response_time / response_time_count, 3)
        
        return summary


# 同步接口函数（便于直接调用）
def probe_domain_sync(domain: str, protocols: List[str] = None, 
                     ports: List[int] = None, timeout: int = 10) -> List[Dict]:
    """
    同步探测单个域名
    
    Args:
        domain: 域名
        protocols: 协议列表
        ports: 端口列表
        timeout: 超时时间
        
    Returns:
        探测结果列表
    """
    probe = DomainProbe(timeout=timeout)
    return asyncio.run(probe.probe_domain(domain, protocols, ports))


def probe_multiple_domains_sync(domains: List[str], protocols: List[str] = None,
                               ports: List[int] = None, timeout: int = 10) -> Dict[str, List[Dict]]:
    """
    同步批量探测多个域名
    
    Args:
        domains: 域名列表
        protocols: 协议列表
        ports: 端口列表
        timeout: 超时时间
        
    Returns:
        探测结果字典
    """
    probe = DomainProbe(timeout=timeout)
    return asyncio.run(probe.probe_multiple_domains(domains, protocols, ports))


import argparse
import json

def main():
    """主函数 - 命令行接口"""
    parser = argparse.ArgumentParser(description='httpx快速域名探活工具')
    parser.add_argument('-d', '--domain', type=str, help='单个域名进行探测')
    parser.add_argument('-f', '--file', type=str, help='包含多个域名的文件路径（每行一个域名）')
    parser.add_argument('-p', '--protocols', nargs='+', default=['http', 'https'], 
                       help='协议列表，默认: http https')
    parser.add_argument('--ports', nargs='+', type=int, default=[80, 443, 8080, 8443, 8000, 3000, 5000, 9000],
                       help='端口列表，默认: 80 443 8080 8443 8000 3000 5000 9000')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='请求超时时间（秒），默认: 10')
    parser.add_argument('-o', '--output', type=str, help='结果输出文件路径')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出结果')
    parser.add_argument('--alive-only', action='store_true', help='只显示存活的URL')
    
    args = parser.parse_args()
    
    # 检查输入参数
    if not args.domain and not args.file:
        parser.error('必须指定域名(-d)或域名文件(-f)')
    
    # 获取域名列表
    domains = []
    if args.domain:
        domains.append(args.domain)
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    domain = line.strip()
                    if domain and not domain.startswith('#'):  # 跳过空行和注释
                        domains.append(domain)
        except FileNotFoundError:
            print(f"错误: 文件 '{args.file}' 不存在")
            return
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return
    
    if not domains:
        print("错误: 没有找到有效的域名")
        return
    
    # 去重
    domains = list(set(domains))
    
    print(f"开始探测 {len(domains)} 个域名...")
    print(f"协议: {args.protocols}")
    print(f"端口: {args.ports}")
    print(f"超时: {args.timeout}秒")
    print("-" * 50)
    
    # 执行探测
    try:
        probe = DomainProbe(timeout=args.timeout)
        results = probe_multiple_domains_sync(domains, args.protocols, args.ports, args.timeout)
        
        # 处理输出
        output_data = {}
        
        if args.json:
            # JSON格式输出
            for domain, domain_results in results.items():
                if args.alive_only:
                    output_data[domain] = probe.filter_alive_results(domain_results)
                else:
                    output_data[domain] = domain_results
            
            output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
        else:
            # 文本格式输出
            output_lines = []
            
            for domain, domain_results in results.items():
                output_lines.append(f"域名: {domain}")
                
                if args.alive_only:
                    domain_results = probe.filter_alive_results(domain_results)
                
                if not domain_results:
                    output_lines.append("  没有探测到存活的URL")
                else:
                    for result in domain_results:
                        if result['success']:
                            status_emoji = "✅"
                            status_info = f"状态码: {result['status_code']}"
                            if result.get('title'):
                                status_info += f" - 标题: {result['title']}"
                            if result.get('response_time'):
                                status_info += f" - 响应时间: {result['response_time']}秒"
                        else:
                            status_emoji = "❌"
                            status_info = f"错误: {result['error']}"
                        
                        output_lines.append(f"  {status_emoji} {result['url']} - {status_info}")
                
                output_lines.append("")
            
            # 添加汇总信息
            summary = probe.summarize_results(results)
            output_lines.append("=" * 50)
            output_lines.append("汇总信息:")
            output_lines.append(f"探测域名总数: {summary['total_domains']}")
            output_lines.append(f"探测URL总数: {summary['total_urls_probed']}")
            output_lines.append(f"存活URL数量: {summary['alive_urls']}")
            output_lines.append(f"存活域名数量: {summary['alive_domains']}")
            output_lines.append(f"平均响应时间: {summary['average_response_time']}秒")
            output_lines.append(f"常见状态码: {summary['common_status_codes']}")
            
            output_str = '\n'.join(output_lines)
        
        # 输出结果
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_str)
                print(f"结果已保存到: {args.output}")
            except Exception as e:
                print(f"保存文件时出错: {e}")
        else:
            print(output_str)
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"探测过程中出错: {e}")


if __name__ == "__main__":
    main()