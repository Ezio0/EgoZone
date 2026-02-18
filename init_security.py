#!/usr/bin/env python3
"""
EgoZone 安全配置初始化脚本
用于生成强密码和配置安全设置
"""

import secrets
import string
import os
from pathlib import Path

def generate_strong_password(length=16):
    """生成强密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # 确保密码包含所有类型的字符
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in "!@#$%^&*()_+-=" for c in password)):
            return password

def generate_secret_key(length=32):
    """生成密钥"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def initialize_security_config():
    """初始化安全配置"""
    print("🔐 EgoZone 安全配置初始化")
    print("=" * 40)

    # 检查 .env 文件是否存在
    env_path = Path(".env")
    example_path = Path(".env.example")

    if not example_path.exists():
        print("❌ 未找到 .env.example 文件")
        return False

    if env_path.exists():
        print("⚠️  检测到 .env 文件已存在")
        response = input("是否覆盖现有配置? (y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return False

    # 生成强密码
    admin_password = generate_strong_password()
    access_password = generate_strong_password()
    secret_key = generate_secret_key()

    print(f"\n✅ 生成的安全配置:")
    print(f"   管理员密码: {admin_password}")
    print(f"   访问密码: {access_password}")
    print(f"   应用密钥: {secret_key}")

    # 读取 .env.example 并替换密码
    with open(example_path, 'r') as f:
        env_content = f.read()

    # 替换密码值
    env_content = env_content.replace("在此处设置强管理员密码", admin_password)
    env_content = env_content.replace("在此处设置强访问密码", access_password)
    env_content = env_content.replace("在此处设置强密钥-推荐使用随机生成的长字符串", secret_key)

    # 如果仍有示例值，生成项目ID
    if "your-gcp-project-id" in env_content:
        # 生成一个示例项目ID
        project_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        env_content = env_content.replace("your-gcp-project-id", f"egozone-{project_suffix}")

    # 保存到 .env
    with open(env_path, 'w') as f:
        f.write(env_content)

    print(f"\n✅ 安全配置已保存到 {env_path}")
    print("\n📋 重要提醒:")
    print("   1. 请妥善保管这些密码")
    print("   2. 不要将 .env 文件提交到版本控制系统")
    print("   3. 如需修改配置，请直接编辑 .env 文件")
    print("   4. 重启服务使配置生效")

    return True

if __name__ == "__main__":
    initialize_security_config()