# EgoZone 安全启动指南

## 🔒 重要安全提醒

由于实施了强化的安全机制，EgoZone现在**强制要求**使用强密码。使用默认密码将无法启动服务。

## 📋 启动前准备

### 1. 检查当前安全状态
运行以下命令检查安全配置：
```bash
python3 -c "from core.security_config import SecurityConfig; result = SecurityConfig.validate_security_configuration(); print('安全状态:', '✅ 安全' if result['is_secure'] else '❌ 需要修复'); print('问题:', result['issues'])"
```

### 2. 设置强密码

#### 方法A：使用环境变量文件（推荐）
1. 复制安全示例文件：
```bash
cp .env.example.secure .env
```

2. 编辑 `.env` 文件，修改密码为强密码：
```bash
# 管理员密码（必须包含大小写字母、数字、特殊字符，12位以上）
ADMIN_PASSWORD=YourSecureAdminPass123!@#

# 访问密码（必须包含大小写字母、数字、特殊字符，12位以上）  
ACCESS_PASSWORD=YourSecureAccessPass456!@#
```

3. 确保密码满足要求：
- ✅ 至少12个字符
- ✅ 包含大写字母（A-Z）
- ✅ 包含小写字母（a-z）
- ✅ 包含数字（0-9）
- ✅ 包含特殊字符（!@#$%^&*等）
- ✅ 不包含常见单词或个人信息

#### 方法B：生成强密码
使用内置的密码生成器：
```python
python3 -c "from core.password_validator import PasswordValidator; validator = PasswordValidator(); pwd = validator.generate_strong_password(16); print('生成的强密码:', pwd)"
```

### 3. 验证密码强度
```bash
python3 -c "from core.password_validator import PasswordValidator; validator = PasswordValidator(); is_valid, errors = validator.validate_password('YourPasswordHere'); print('有效:', is_valid); print('错误:', errors)"
```

## 🚀 启动应用

### 标准启动
```bash
python3 main.py
```

### 后台启动（推荐）
```bash
nohup python3 main.py > egozone.log 2>&1 &
echo $! > egozone.pid
```

### 使用启动脚本
```bash
chmod +x start_service.sh
./start_service.sh
```

## ✅ 启动成功验证

### 检查服务状态
```bash
# 查看进程
ps aux | grep "python3 main.py"

# 检查端口
netstat -tlnp | grep 8000

# 测试健康检查端点
curl http://localhost:8000/health
```

### 验证安全功能
1. **测试默认密码拒绝**：
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "Wuya2bu2.egozone"}'
# 应该返回401 Unauthorized
```

2. **测试限流机制**：
```bash
# 快速发送多个错误密码请求
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"password": "wrongpassword"}'
done
# 应该触发429 Too Many Requests
```

3. **测试令牌持久化**：
```bash
# 使用正确密码登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "YourSecureAdminPass123!@#"}'
# 应该返回有效的令牌
```

## 🔧 故障排除

### 问题1：服务无法启动
**症状**：启动后立即退出，无错误信息
**解决**：检查安全日志，运行安全检查命令
```bash
python3 -c "from core.security_config import SecurityConfig; result = SecurityConfig.validate_security_configuration(); print('问题:', result['issues'])"
```

### 问题2：密码被拒绝
**症状**：使用新密码仍无法登录
**解决**：确保密码满足所有要求，检查大小写和特殊字符

### 问题3：限流误触发
**症状**：正常用户被锁定
**解决**：等待30分钟自动解锁，或清理限流数据
```bash
python3 -c "from core.rate_limiter import cleanup_rate_limit_data; cleanup_rate_limit_data()"
```

## 📊 安全监控

### 查看安全日志
```bash
tail -f egozone.log | grep -E "(安全|Security|登录|Login)"
```

### 检查登录统计
```bash
python3 -c "from core.rate_limiter import get_login_stats; stats = get_login_stats('admin', '127.0.0.1'); print('登录统计:', stats)"
```

### 验证安全配置
```bash
python3 -c "
from core.security_config import SecurityConfig
result = SecurityConfig.validate_security_configuration()
print('🔒 安全配置状态:', '✅ 安全' if result['is_secure'] else '❌ 需要修复')
if result['issues']:
    print('问题:')
    for issue in result['issues']:
        print(f'  ❌ {issue}')
if result['warnings']:
    print('警告:')
    for warning in result['warnings']:
        print(f'  ⚠️  {warning}')
"
```

## 🛡️ 安全最佳实践

### 生产环境建议
1. **使用HTTPS**：配置SSL/TLS证书
2. **反向代理**：使用Nginx/Apache作为反向代理
3. **防火墙**：配置适当的防火墙规则
4. **定期更新**：保持系统和依赖库更新
5. **监控告警**：设置安全事件监控
6. **备份策略**：定期备份配置和数据

### 密码管理
1. **定期更换**：每3-6个月更换一次密码
2. **不同系统**：为不同系统使用不同密码
3. **密码管理器**：使用专业的密码管理工具
4. **避免重用**：不要在多个系统重用密码

## 📞 支持

如遇到启动问题：
1. 首先运行安全检查命令
2. 查看应用日志获取详细信息
3. 验证密码强度要求
4. 检查端口是否被占用
5. 参考故障排除部分

**重要提醒**：安全机制是为了保护您的系统，请务必使用强密码并妥善保管。