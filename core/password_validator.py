"""
密码验证器 - 强制密码安全策略
"""

import re
import hashlib
import secrets
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel


class PasswordPolicy(BaseModel):
    """密码策略配置"""
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True
    min_special_chars: int = 2
    forbidden_patterns: List[str] = [
        "123", "abc", "qwe", "password", "admin", "egozone",
        "test", "demo", "default", "changeme", "123456"
    ]
    max_consecutive_chars: int = 3
    min_entropy_bits: float = 30.0


class PasswordValidator:
    """密码强度验证器"""
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
    
    def validate_password(self, password: str, username: str = None) -> Tuple[bool, List[str]]:
        """
        验证密码强度
        
        Args:
            password: 要验证的密码
            username: 用户名（用于检查是否包含用户名）
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 长度检查
        if len(password) < self.policy.min_length:
            errors.append(f"密码长度至少为 {self.policy.min_length} 位")
        
        if len(password) > self.policy.max_length:
            errors.append(f"密码长度不能超过 {self.policy.max_length} 位")
        
        # 字符类型检查
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        
        if self.policy.require_digits and not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        
        if self.policy.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")
        
        # 特殊字符数量检查
        special_count = len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', password))
        if special_count < self.policy.min_special_chars:
            errors.append(f"密码必须包含至少 {self.policy.min_special_chars} 个特殊字符")
        
        # 禁止模式检查
        password_lower = password.lower()
        for pattern in self.policy.forbidden_patterns:
            if pattern.lower() in password_lower:
                errors.append(f"密码不能包含常见模式 '{pattern}'")
        
        # 用户名检查
        if username and username.lower() in password_lower:
            errors.append("密码不能包含用户名")
        
        # 连续字符检查
        consecutive_pattern = r'(.)\1{' + str(self.policy.max_consecutive_chars) + ',}'
        if re.search(consecutive_pattern, password):
            errors.append(f"密码不能包含超过 {self.policy.max_consecutive_chars + 1} 个连续相同字符")
        
        # 熵值检查（复杂度估算）
        entropy = self._calculate_entropy(password)
        if entropy < self.policy.min_entropy_bits:
            errors.append(f"密码复杂度不足（熵值: {entropy:.1f}，要求: {self.policy.min_entropy_bits}）")
        
        return len(errors) == 0, errors
    
    def _calculate_entropy(self, password: str) -> float:
        """计算密码熵值"""
        char_counts = {}
        for char in password:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        entropy = 0.0
        password_length = len(password)
        for count in char_counts.values():
            probability = count / password_length
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy * len(set(password))
    
    def generate_strong_password(self, length: int = 16) -> str:
        """生成强密码"""
        if length < self.policy.min_length:
            length = self.policy.min_length
        
        # 字符集
        lowercase = 'abcdefghijklmnopqrstuvwxyz'
        uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        special = '!@#$%^&*(),.?":{}|<>[]'
        
        # 确保包含所有必需字符类型
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special),
            secrets.choice(special),  # 至少2个特殊字符
        ]
        
        # 填充剩余长度
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))
        
        # 打乱顺序
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def hash_password(self, password: str, salt: bytes = None) -> Tuple[str, bytes]:
        """安全哈希密码"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # 使用 PBKDF2 + SHA256
        hashed = hashlib.pbkdf2_hmac('sha256', 
                                   password.encode('utf-8'), 
                                   salt, 
                                   100000)  # 100,000 次迭代
        
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """验证密码"""
        calculated_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, hashed_password)


class DefaultPasswordChecker:
    """默认密码检查器"""
    
    # 已知的默认密码列表
    DEFAULT_PASSWORDS = {
        'admin_password': [
            'Wuya2bu2.egozone', 'admin', 'password', '123456', 'admin123',
            'egozone', 'egozone123', 'default', 'changeme'
        ],
        'access_password': [
            '123321abc0', '123456', 'password', 'access', 'access123',
            '123321', 'abc123', 'default', 'changeme'
        ]
    }
    
    @classmethod
    def is_default_password(cls, password: str, password_type: str) -> bool:
        """检查是否为默认密码"""
        default_list = cls.DEFAULT_PASSWORDS.get(password_type, [])
        return password in default_list
    
    @classmethod
    def get_security_recommendations(cls) -> List[str]:
        """获取安全建议"""
        return [
            "立即修改默认密码",
            "使用至少12位的复杂密码",
            "包含大小写字母、数字和特殊字符",
            "避免使用常见单词或个人信息",
            "定期更换密码",
            "为不同账户使用不同密码"
        ]


def validate_configuration_passwords(admin_pwd: str, access_pwd: str) -> Dict[str, any]:
    """验证配置文件中的密码"""
    validator = PasswordValidator()
    checker = DefaultPasswordChecker()
    
    results = {
        'admin_password': {
            'is_valid': False,
            'is_default': False,
            'errors': [],
            'recommendations': []
        },
        'access_password': {
            'is_valid': False,
            'is_default': False,
            'errors': [],
            'recommendations': []
        }
    }
    
    # 检查管理员密码
    is_valid, errors = validator.validate_password(admin_pwd)
    results['admin_password']['is_valid'] = is_valid
    results['admin_password']['errors'] = errors
    results['admin_password']['is_default'] = checker.is_default_password(admin_pwd, 'admin_password')
    
    if not is_valid or results['admin_password']['is_default']:
        results['admin_password']['recommendations'] = [
            "管理员密码必须满足强密码要求",
            "不能使用默认密码或常见密码",
            f"建议密码: {validator.generate_strong_password()}"
        ]
    
    # 检查访问密码
    is_valid, errors = validator.validate_password(access_pwd)
    results['access_password']['is_valid'] = is_valid
    results['access_password']['errors'] = errors
    results['access_password']['is_default'] = checker.is_default_password(access_pwd, 'access_password')
    
    if not is_valid or results['access_password']['is_default']:
        results['access_password']['recommendations'] = [
            "访问密码必须满足强密码要求",
            "不能使用默认密码或常见密码",
            f"建议密码: {validator.generate_strong_password()}"
        ]
    
    return results