#!/usr/bin/env python3
"""
安全配置验证脚本
用于验证 EgoZone 安全配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_security_config():
    """测试安全配置"""
    print("🔐 测试安全配置...")

    try:
        # 测试配置加载
        from config import get_settings
        settings = get_settings()
        print("✅ 配置加载正常")

        # 测试增强安全验证
        from core.enhanced_security import enhanced_security_validation, print_security_report
        is_secure, errors, warnings = enhanced_security_validation()

        print_security_report(is_secure, errors, warnings)

        # 测试密码生成器
        from init_security import generate_strong_password, generate_secret_key
        test_admin_pwd = generate_strong_password()
        test_access_pwd = generate_strong_password()
        test_secret = generate_secret_key()

        print(f"\n✅ 密码生成器测试通过")
        print(f"   生成的管理员密码: {test_admin_pwd[:8]}...")
        print(f"   生成的访问密码: {test_access_pwd[:8]}...")
        print(f"   生成的密钥: {test_secret[:8]}...")

        # 检查密码是否符合基本要求
        assert len(test_admin_pwd) >= 12, "管理员密码长度不足"
        assert len(test_access_pwd) >= 12, "访问密码长度不足"
        assert len(test_secret) >= 24, "密钥长度不足"

        # 检查字符复杂度
        import re
        assert re.search(r'[A-Z]', test_admin_pwd), "管理员密码缺少大写字母"
        assert re.search(r'[a-z]', test_admin_pwd), "管理员密码缺少小写字母"
        assert re.search(r'\d', test_admin_pwd), "管理员密码缺少数字"
        assert re.search(r'[!@#$%^&*(),.?":{}|<>[\]\\`~;\'_+=)(*-]', test_admin_pwd), "管理员密码缺少特殊字符"

        print("✅ 密码强度测试通过")
        print("\n🎉 所有安全配置测试通过！")
        return True

    except Exception as e:
        print(f"❌ 安全配置测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_security_config()
    if not success:
        sys.exit(1)