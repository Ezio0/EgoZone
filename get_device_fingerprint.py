#!/usr/bin/env python3
"""
设备指纹生成工具
帮助您获取特定设备的指纹，用于添加到信任设备列表
"""

import hashlib
import sys
import platform


def generate_device_fingerprint(user_agent, ip_address):
    """
    生成设备指纹
    这与EgoZone内部使用的算法相同
    """
    return hashlib.sha256(f"{user_agent}_{ip_address}".encode()).hexdigest()


def main():
    print("=== EgoZone 设备指纹生成工具 ===\n")

    print("要获取设备指纹，您需要提供以下信息：")
    print("1. User-Agent 字符串")
    print("2. 设备IP地址\n")

    print("如何获取User-Agent字符串：")
    print("- Chrome浏览器: 按F12，Console标签页，输入 navigator.userAgent 并回车")
    print("- Firefox浏览器: 按F12，Console标签页，输入 navigator.userAgent 并回车")
    print("- Safari浏览器: 开发菜单开启后，按Option+Cmd+C，输入 navigator.userAgent 并回车\n")

    # 如果从命令行传入参数
    if len(sys.argv) >= 3:
        user_agent = sys.argv[1]
        ip_address = sys.argv[2]
        device_fingerprint = generate_device_fingerprint(user_agent, ip_address)

        print(f"User-Agent: {user_agent}")
        print(f"IP Address: {ip_address}")
        print(f"设备指纹: {device_fingerprint}")
        print(f"设备指纹(截短): {device_fingerprint[:16]}...")

        # 添加到信任设备列表
        import os
        import json
        from datetime import datetime

        TRUSTED_DEVICES_FILE = "data/trusted_devices.json"

        # 加载现有设备列表
        if os.path.exists(TRUSTED_DEVICES_FILE):
            with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
                trusted_devices = json.load(f)
        else:
            trusted_devices = {}

        # 添加新设备
        device_name = input(f"\n请输入此设备的名称 (例如: '家里的电脑'): ").strip()
        if not device_name:
            device_name = "家里的电脑"

        trusted_devices[device_fingerprint] = {
            "name": device_name,
            "added_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "user_agent": user_agent[:200]
        }

        # 保存
        os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)
        with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

        print(f"✅ 设备 '{device_name}' 已添加到信任列表")
        print(f"   指纹: {device_fingerprint}")
        return

    # 如果没有命令行参数，提供交互式界面
    print("或者，您也可以手动输入信息：")
    user_agent = input("请输入User-Agent字符串: ").strip()
    if not user_agent:
        print("未输入User-Agent，退出。")
        return

    ip_address = input("请输入IP地址 (如果不知道可输入'unknown'): ").strip()
    if not ip_address:
        ip_address = "unknown"

    device_fingerprint = generate_device_fingerprint(user_agent, ip_address)

    print(f"\n生成的设备指纹: {device_fingerprint}")
    print(f"用于匹配的截短版本: {device_fingerprint[:16]}...")

    # 添加到信任设备列表
    import os
    import json
    from datetime import datetime

    TRUSTED_DEVICES_FILE = "data/trusted_devices.json"

    # 加载现有设备列表
    if os.path.exists(TRUSTED_DEVICES_FILE):
        with open(TRUSTED_DEVICES_FILE, 'r', encoding='utf-8') as f:
            trusted_devices = json.load(f)
    else:
        trusted_devices = {}

    # 添加新设备
    device_name = input(f"\n请输入此设备的名称 (例如: '家里的电脑'): ").strip()
    if not device_name:
        device_name = "家里的电脑"

    trusted_devices[device_fingerprint] = {
        "name": device_name,
        "added_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "user_agent": user_agent[:200]
    }

    # 保存
    os.makedirs(os.path.dirname(TRUSTED_DEVICES_FILE), exist_ok=True)
    with open(TRUSTED_DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(trusted_devices, f, ensure_ascii=False, indent=2)

    print(f"✅ 设备 '{device_name}' 已添加到信任列表")
    print(f"   指纹: {device_fingerprint}")


if __name__ == "__main__":
    main()