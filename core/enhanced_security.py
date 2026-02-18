"""
增强的密码安全验证模块
用于更严格的安全检查
"""

import re
from typing import Dict, List, Tuple
from config import get_settings


def enhanced_security_validation() -> Tuple[bool, List[str], List[str]]:
    """
    增强的安全验证
    返回: (是否通过, 错误列表, 警告列表)
    """
    settings = get_settings()
    errors = []
    warnings = []

    # 检查必要的安全配置是否存在
    if not settings.admin_password or settings.admin_password.strip() == "":
        errors.append("❌ 管理员密码不能为空")

    if not settings.access_password or settings.access_password.strip() == "":
        errors.append("❌ 访问密码不能为空")

    if not settings.secret_key or settings.secret_key == "change-me-in-production":
        errors.append("❌ 必须修改默认的SECRET_KEY")

    if not hasattr(settings, 'gcp_project') or not settings.gcp_project or settings.gcp_project == "egozone":
        errors.append("❌ 必须设置有效的GCP_PROJECT")

    # 更严格密码强度检查
    if settings.admin_password:
        admin_checks = _detailed_password_check(settings.admin_password, "管理员")
        errors.extend(admin_checks[0])
        warnings.extend(admin_checks[1])

    if settings.access_password:
        access_checks = _detailed_password_check(settings.access_password, "访问")
        errors.extend(access_checks[0])
        warnings.extend(access_checks[1])

    # 额外安全检查
    if settings.debug and settings.debug is True:
        warnings.append("⚠️ 调试模式已启用，生产环境应关闭")

    # 检查是否使用了默认密码
    if settings.admin_password in ["Wuya2bu2.egozone", "admin123", "password", "123456", "admin"]:
        errors.append("❌ 检测到使用默认管理员密码，请立即修改")

    if settings.access_password in ["123321abc0", "access123", "password", "123456", "access"]:
        errors.append("❌ 检测到使用默认访问密码，请立即修改")

    return len(errors) == 0, errors, warnings


def _detailed_password_check(password: str, password_type: str) -> Tuple[List[str], List[str]]:
    """
    详细密码检查
    返回: (错误列表, 警告列表)
    """
    errors = []
    warnings = []

    if len(password) < 12:
        errors.append(f"❌ {password_type}密码长度至少为12位")

    if not re.search(r'[A-Z]', password):
        errors.append(f"❌ {password_type}密码必须包含大写字母")

    if not re.search(r'[a-z]', password):
        errors.append(f"❌ {password_type}密码必须包含小写字母")

    if not re.search(r'\d', password):
        errors.append(f"❌ {password_type}密码必须包含数字")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>[\]\\`~;\'_+=)(*-]', password):
        errors.append(f"❌ {password_type}密码必须包含特殊字符")

    # 检查常见弱密码模式
    weak_patterns = [
        (r'(.)\1{2,}', f"{password_type}密码不应包含连续重复字符"),
        (r'(123|abc|qwe|asd)', f"{password_type}密码不应包含常见字符序列"),
        (r'(password|admin|access|changeme|default)', f"{password_type}密码不应包含常见词汇"),
    ]

    for pattern, msg in weak_patterns:
        if re.search(pattern, password.lower()):
            warnings.append(f"⚠️ {msg}")

    # 检查字符复杂度
    unique_chars = len(set(password))
    if unique_chars < len(password) * 0.6:
        warnings.append(f"⚠️ {password_type}密码字符多样性不足")

    return errors, warnings


def print_security_report(is_secure: bool, errors: List[str], warnings: List[str]):
    """打印安全报告"""
    print("\n🔒 安全配置检查报告")
    print("=" * 40)

    if errors:
        print("\n🚨 检测到以下安全问题:")
        for error in errors:
            print(f"   {error}")

    if warnings:
        print("\n⚠️ 检测到以下安全警告:")
        for warning in warnings:
            print(f"   {warning}")

    if not errors and not warnings:
        print("\n✅ 所有安全检查均已通过")
    elif not errors and warnings:
        print(f"\n⚠️ 基础安全要求已满足，但建议处理 {len(warnings)} 个安全警告")
    elif errors:
        print(f"\n❌ 检测到 {len(errors)} 个严重安全问题，必须修复后才能启动服务")

    print("=" * 40)


if __name__ == "__main__":
    is_secure, errors, warnings = enhanced_security_validation()
    print_security_report(is_secure, errors, warnings)