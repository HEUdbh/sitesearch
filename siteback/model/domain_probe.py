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


# 使用示例
if __name__ == "__main__":
    # 示例用法
    async def example():
        probe = DomainProbe(timeout=5)
        
        # 探测单个域名
        print("=== 探测单个域名 ===")
        results = await probe.probe_domain("example.com")
        for result in results:
            if result['success']:
                print(f"✅ {result['url']} - 状态码: {result['status_code']} - 标题: {result.get('title', 'N/A')}")
            else:
                print(f"❌ {result['url']} - 错误: {result['error']}")
        
        # 批量探测多个域名
        print("\n=== 批量探测多个域名 ===")
        domains = ["google.com", "github.com", "nonexistent-test-domain-12345.com"]
        batch_results = await probe.probe_multiple_domains(domains)
        
        for domain, domain_results in batch_results.items():
            print(f"\n域名: {domain}")
            alive_results = probe.filter_alive_results(domain_results)
            print(f"存活URL数量: {len(alive_results)}")
            
            for result in alive_results:
                print(f"  ✅ {result['url']} - 状态码: {result['status_code']}")
        
        # 汇总信息
        summary = probe.summarize_results(batch_results)
        print(f"\n=== 汇总信息 ===")
        print(f"探测域名总数: {summary['total_domains']}")
        print(f"探测URL总数: {summary['total_urls_probed']}")
        print(f"存活URL数量: {summary['alive_urls']}")
        print(f"存活域名数量: {summary['alive_domains']}")
        print(f"平均响应时间: {summary['average_response_time']}秒")
        print("常见状态码:", summary['common_status_codes'])
    
    # 运行示例
    asyncio.run(example())