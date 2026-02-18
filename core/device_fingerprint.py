"""
增强的设备指纹生成模块
提供更安全的设备识别机制
"""

import hashlib
import json
from typing import Dict, Optional
from datetime import datetime
import re


class DeviceFingerprint:
    """增强的设备指纹生成器"""
    
    @staticmethod
    def generate_enhanced_fingerprint(user_agent: str, ip_address: str,
                                    accept_language: Optional[str] = None,
                                    accept_encoding: Optional[str] = None,
                                    dnt: Optional[str] = None) -> str:
        """
        生成增强的设备指纹
        
        Args:
            user_agent: 用户代理字符串
            ip_address: IP地址
            accept_language: 接受语言
            accept_encoding: 接受编码
            dnt: 请勿追踪标志
            
        Returns:
            设备指纹哈希值
        """
        # 解析User-Agent获取设备信息
        device_info = DeviceFingerprint._parse_user_agent(user_agent)
        
        # 构建设备特征向量
        features = {
            'user_agent': user_agent,
            'ip_address': ip_address,
            'browser': device_info.get('browser', 'unknown'),
            'browser_version': device_info.get('browser_version', 'unknown'),
            'os': device_info.get('os', 'unknown'),
            'os_version': device_info.get('os_version', 'unknown'),
            'device_type': device_info.get('device_type', 'unknown'),
            'accept_language': accept_language or 'unknown',
            'accept_encoding': accept_encoding or 'unknown',
            'dnt': dnt or 'unknown',
        }
        
        # 按字母顺序排序确保一致性
        sorted_features = json.dumps(features, sort_keys=True)
        
        # 使用SHA-256生成指纹
        fingerprint = hashlib.sha256(sorted_features.encode('utf-8')).hexdigest()
        
        return fingerprint
    
    @staticmethod
    def _parse_user_agent(user_agent: str) -> Dict[str, str]:
        """解析User-Agent字符串"""
        info = {
            'browser': 'unknown',
            'browser_version': 'unknown',
            'os': 'unknown',
            'os_version': 'unknown',
            'device_type': 'desktop'
        }
        
        if not user_agent:
            return info
        
        user_agent_lower = user_agent.lower()
        
        # 浏览器检测
        if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
            info['browser'] = 'chrome'
            version_match = re.search(r'chrome/(\d+\.\d+)', user_agent_lower)
            if version_match:
                info['browser_version'] = version_match.group(1)
        elif 'firefox' in user_agent_lower:
            info['browser'] = 'firefox'
            version_match = re.search(r'firefox/(\d+\.\d+)', user_agent_lower)
            if version_match:
                info['browser_version'] = version_match.group(1)
        elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
            info['browser'] = 'safari'
            version_match = re.search(r'version/(\d+\.\d+)', user_agent_lower)
            if version_match:
                info['browser_version'] = version_match.group(1)
        elif 'edg' in user_agent_lower:
            info['browser'] = 'edge'
            version_match = re.search(r'edg/(\d+\.\d+)', user_agent_lower)
            if version_match:
                info['browser_version'] = version_match.group(1)
        
        # 操作系统检测
        if 'windows nt 10.0' in user_agent_lower:
            info['os'] = 'windows'
            info['os_version'] = '10'
        elif 'windows nt 6.3' in user_agent_lower:
            info['os'] = 'windows'
            info['os_version'] = '8.1'
        elif 'windows nt 6.1' in user_agent_lower:
            info['os'] = 'windows'
            info['os_version'] = '7'
        elif 'mac os x' in user_agent_lower:
            info['os'] = 'macos'
            version_match = re.search(r'mac os x (\d+[_\.]\d+)', user_agent_lower)
            if version_match:
                info['os_version'] = version_match.group(1).replace('_', '.')
        elif 'linux' in user_agent_lower:
            info['os'] = 'linux'
        elif 'android' in user_agent_lower:
            info['os'] = 'android'
            version_match = re.search(r'android (\d+\.\d+)', user_agent_lower)
            if version_match:
                info['os_version'] = version_match.group(1)
        elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            info['os'] = 'ios'
            version_match = re.search(r'os (\d+[_\.]\d+)', user_agent_lower)
            if version_match:
                info['os_version'] = version_match.group(1).replace('_', '.')
        
        # 设备类型检测
        if 'mobile' in user_agent_lower:
            info['device_type'] = 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            info['device_type'] = 'tablet'
        elif 'android' in user_agent_lower and 'mobile' not in user_agent_lower:
            info['device_type'] = 'tablet'
        
        return info
    
    @staticmethod
    def get_device_risk_score(fingerprint_data: Dict) -> float:
        """
        计算设备风险评分
        
        Returns:
            风险评分 (0.0 - 1.0)，越高风险越大
        """
        risk_score = 0.0
        
        # 基础风险评分
        user_agent = fingerprint_data.get('user_agent', '')
        
        # 空或极短的User-Agent是高风险
        if not user_agent or len(user_agent) < 20:
            risk_score += 0.3
        
        # 缺少关键信息增加风险
        if 'unknown' in str(fingerprint_data.values()):
            risk_score += 0.2
        
        # 自动化工具特征
        suspicious_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python', 'java', 'httpclient', 'okhttp', 'axios'
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if pattern in user_agent_lower:
                risk_score += 0.4
                break
        
        # 确保评分在合理范围内
        return min(risk_score, 1.0)
    
    @staticmethod
    def is_suspicious_device(user_agent: str, ip_address: str) -> bool:
        """快速检查是否为可疑设备"""
        if not user_agent:
            return True
        
        user_agent_lower = user_agent.lower()
        
        # 自动化工具黑名单（降低敏感度，只拦截明显的机器人）
        automation_signatures = [
            'bot', 'crawler', 'spider', 'scraper',
            'selenium', 'phantomjs', 'headless', 'puppeteer',
            'python-requests', 'httpclient', 'okhttp'
        ]
        
        for signature in automation_signatures:
            if signature in user_agent_lower:
                return True
        
        # 检查User-Agent格式是否异常
        if len(user_agent) < 10 or len(user_agent) > 500:
            return True
        
        # 检查是否缺少常见浏览器特征（放宽限制，允许开发工具）
        common_browsers = ['chrome', 'firefox', 'safari', 'edge', 'curl', 'wget']
        has_browser = any(browser in user_agent_lower for browser in common_browsers)
        
        # 更宽松的条件：只有非常短且不包含任何常见特征的才视为可疑
        if not has_browser and len(user_agent) < 20:
            return True
        
        return False


def generate_device_fingerprint(user_agent: str, ip_address: str,
                              accept_language: Optional[str] = None,
                              accept_encoding: Optional[str] = None,
                              dnt: Optional[str] = None) -> str:
    """兼容旧接口的设备指纹生成函数"""
    return DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )