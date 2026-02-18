"""
安全配置管理
提供安全相关的配置和验证功能
"""

import re
from typing import Dict, List, Optional
from config import get_settings


class SecurityConfig:
    """安全配置管理器"""
    
    # 默认密码黑名单（必须修改）
    DEFAULT_PASSWORDS = {
        "admin": ["Wuya2bu2.egozone", "admin123", "password", "123456"],
        "access": ["123321abc0", "access123", "password", "123456"]
    }
    
    # 密码强度要求
    PASSWORD_REQUIREMENTS = {
        "min_length": 8,
        "max_length": 64,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
    }
    
    # 安全头配置
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    }
    
    @staticmethod
    def check_password_strength(password: str) -> Dict[str, any]:
        """检查密码强度"""
        errors = []
        warnings = []
        
        # 长度检查
        if len(password) < SecurityConfig.PASSWORD_REQUIREMENTS["min_length"]:
            errors.append(f"密码长度至少为{SecurityConfig.PASSWORD_REQUIREMENTS['min_length']}个字符")
        
        if len(password) > SecurityConfig.PASSWORD_REQUIREMENTS["max_length"]:
            errors.append(f"密码长度不能超过{SecurityConfig.PASSWORD_REQUIREMENTS['max_length']}个字符")
        
        # 字符类型检查
        if SecurityConfig.PASSWORD_REQUIREMENTS["require_uppercase"] and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含至少一个大写字母")
        
        if SecurityConfig.PASSWORD_REQUIREMENTS["require_lowercase"] and not re.search(r'[a-z]', password):
            errors.append("密码必须包含至少一个小写字母")
        
        if SecurityConfig.PASSWORD_REQUIREMENTS["require_digit"] and not re.search(r'\d', password):
            errors.append("密码必须包含至少一个数字")
        
        if SecurityConfig.PASSWORD_REQUIREMENTS["require_special"] and not re.search(
            f"[{re.escape(SecurityConfig.PASSWORD_REQUIREMENTS['special_chars'])}]", password
        ):
            errors.append("密码必须包含至少一个特殊字符")
        
        # 常见弱密码检查
        weak_patterns = [
            r'123+',  # 连续数字
            r'abc+',  # 连续字母
            r'qwe+',  # 键盘连续
            r'(.)\1{2,}',  # 重复字符
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                warnings.append("密码包含常见模式，建议增加复杂度")
                break
        
        # 个人信息相关检查（简单检查）
        common_info_patterns = [
            r'admin', r'user', r'test', r'password',
            r'202[0-9]', r'19[0-9]{2}',  # 年份
        ]
        
        for pattern in common_info_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                warnings.append("密码不应包含常见词汇或日期")
                break
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": SecurityConfig._calculate_password_score(password, errors, warnings)
        }
    
    @staticmethod
    def _calculate_password_score(password: str, errors: List[str], warnings: List[str]) -> int:
        """计算密码强度评分 (0-100)"""
        if errors:
            return 0
        
        score = 50  # 基础分
        
        # 长度加分
        if len(password) >= 12:
            score += 20
        elif len(password) >= 10:
            score += 10
        
        # 字符多样性加分
        char_types = 0
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'\d', password):
            char_types += 1
        if re.search(r'[^A-Za-z0-9]', password):
            char_types += 1
        
        score += char_types * 5
        
        # 复杂度加分
        if len(password) >= 16:
            score += 10
        
        # 警告扣分
        score -= len(warnings) * 5
        
        return max(0, min(100, score))
    
    @staticmethod
    def is_default_password(password_type: str, password: str) -> bool:
        """检查是否使用了默认密码"""
        if password_type not in SecurityConfig.DEFAULT_PASSWORDS:
            return False
        
        return password in SecurityConfig.DEFAULT_PASSWORDS[password_type]
    
    @staticmethod
    def validate_security_configuration() -> Dict[str, any]:
        """验证安全配置"""
        settings = get_settings()
        issues = []
        warnings = []
        
        # 检查默认密码
        if SecurityConfig.is_default_password('admin', settings.admin_password):
            issues.append("管理员密码使用了默认密码，必须修改")
        
        if SecurityConfig.is_default_password('access', settings.access_password):
            issues.append("访问密码使用了默认密码，必须修改")
        
        # 检查密码强度
        admin_check = SecurityConfig.check_password_strength(settings.admin_password)
        if not admin_check['is_valid']:
            issues.extend([f"管理员密码：{error}" for error in admin_check['errors']])
        elif admin_check['score'] < 70:
            warnings.append("管理员密码强度较低，建议增强")
        
        access_check = SecurityConfig.check_password_strength(settings.access_password)
        if not access_check['is_valid']:
            issues.extend([f"访问密码：{error}" for error in access_check['errors']])
        elif access_check['score'] < 50:
            warnings.append("访问密码强度较低，建议增强")
        
        # 检查调试模式
        import os
        if os.environ.get('DEBUG', 'false').lower() == 'true':
            warnings.append("调试模式已启用，生产环境应关闭")
        
        return {
            "is_secure": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": SecurityConfig._get_security_recommendations(issues, warnings)
        }
    
    @staticmethod
    def _get_security_recommendations(issues: List[str], warnings: List[str]) -> List[str]:
        """获取安全建议"""
        recommendations = []
        
        if issues:
            recommendations.append("立即修复所有安全问题后再部署到生产环境")
        
        if warnings:
            recommendations.append("考虑处理安全警告以提升系统安全性")
        
        recommendations.extend([
            "定期更新密码并监控异常登录",
            "启用HTTPS加密传输",
            "定期备份数据和审计日志",
            "考虑实施多因素认证(MFA)"
        ])
        
        return recommendations
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """获取安全HTTP头"""
        return SecurityConfig.SECURITY_HEADERS.copy()


def check_security_configuration():
    """快速安全检查函数"""
    result = SecurityConfig.validate_security_configuration()
    
    if not result['is_secure']:
        print("❌ 发现严重安全问题：")
        for issue in result['issues']:
            print(f"   - {issue}")
        return False
    
    if result['warnings']:
        print("⚠️  发现安全警告：")
        for warning in result['warnings']:
            print(f"   - {warning}")
    
    print("✅ 基础安全检查通过")
    return True


if __name__ == "__main__":
    check_security_configuration()