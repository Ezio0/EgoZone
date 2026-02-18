#!/usr/bin/env python3
"""
EgoZone 信任设备管理工具
用于预配置信任设备（家里的电脑、公司的电脑和手机）
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List

TRUSTED_DEVICES_FILE = "data/trusted_devices.json"


def initialize_trusted_devices():
    """初始化信任设备列表，预配置常见的信任设备"""

    # 示例设备指纹和名称
    trusted_devices = {
        # 家里电脑示例 - 实际使用时需要根据实际设备信息生成
        "home_computer_fingerprint_placeholder": {
            "name": "家里的电脑",
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Placeholder for home computer"
        },
        # 公司电脑示例
        "work_computer_fingerprint_placeholder": {
            "name": "公司的电脑",
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Placeholder for work computer"
        },
        # 手机示例（可能有多种设备类型）
        "mobile_phone_fingerprint_placeholder": {
            "name": "个人手机",
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": "Placeholder for mobile phone"
        }
    }

    # 确保目录存在
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)

    # 保存信任设备列表
    with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

    print(f"✅ 信任设备列表已创建: {TRUSTED_DEVICES_FILE}")
    print("📝 注意：您需要将实际的设备指纹替换占位符")
    print("💡 您可以通过首次在信任设备上登录并在请求中勾选“信任此设备”来自动生成指纹")


def add_trusted_device(device_fingerprint: str, device_name: str):
    """添加一个信任设备"""

    # 加载现有信任设备
    if os.path.exists(TRUSTED_DEVICES_FILE):
        with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
            trusted_devices = json.load(f)
    else:
        trusted_devices = {}

    # 添加新设备
    trusted_devices[device_fingerprint] = {
        "name": device_name,
        "added_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "user_agent": "Added via management script"
    }

    # 确保目录存在
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)

    # 保存更新后的信任设备列表
    with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

    print(f"✅ 设备 '{device_name}' 已添加到信任列表")


def list_trusted_devices():
    """列出所有信任设备"""

    if not os.path.exists(TRUSTED_DEVICES_FILE):
        print("❌ 信任设备列表不存在")
        return

    with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
        trusted_devices = json.load(f)

    if not trusted_devices:
        print("📭 没有信任设备")
        return

    print(f"📋 信任设备列表 (共 {len(trusted_devices)} 台设备):")
    for fingerprint, info in trusted_devices.items():
        print(f"  • {info['name']} (指纹: {fingerprint[:16]}...) - 添加时间: {info['added_at']}")


def remove_trusted_device(device_fingerprint: str):
    """移除信任设备"""

    if not os.path.exists(TRUSTED_DEVICES_FILE):
        print("❌ 信任设备列表不存在")
        return

    with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
        trusted_devices = json.load(f)

    if device_fingerprint in trusted_devices:
        device_name = trusted_devices[device_fingerprint]['name']
        del trusted_devices[device_fingerprint]

        with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

        print(f"✅ 设备 '{device_name}' 已从信任列表中移除")
    else:
        print(f"❌ 指纹为 {device_fingerprint} 的设备不在信任列表中")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='EgoZone 信任设备管理工具')
    parser.add_argument('action', choices=['init', 'list', 'add', 'remove'],
                        help='操作类型: init(初始化), list(列出), add(添加), remove(移除)')
    parser.add_argument('--fingerprint', type=str, help='设备指纹')
    parser.add_argument('--name', type=str, help='设备名称')

    args = parser.parse_args()

    if args.action == 'init':
        initialize_trusted_devices()
    elif args.action == 'list':
        list_trusted_devices()
    elif args.action == 'add':
        if not args.fingerprint or not args.name:
            print("❌ 添加设备需要同时提供 --fingerprint 和 --name 参数")
        else:
            add_trusted_device(args.fingerprint, args.name)
    elif args.action == 'remove':
        if not args.fingerprint:
            print("❌ 移除设备需要提供 --fingerprint 参数")
        else:
            remove_trusted_device(args.fingerprint)