# EgoZone 安全配置指南

## 安全配置要求

EgoZone 项目采用严格的密码策略，确保系统的安全性。

### 密码强度要求

1. **管理员密码** (`ADMIN_PASSWORD`)
   - 最少12个字符
   - 必须包含大写字母、小写字母、数字和特殊字符
   - 不能使用常见密码模式（如123、abc、password等）

2. **访问密码** (`ACCESS_PASSWORD`)
   - 最少12个字符
   - 必须包含大写字母、小写字母、数字和特殊字符
   - 不能使用常见密码模式

### 配置说明

1. 将 `.env.example` 复制为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 修改 `.env` 文件中的密码：
   ```bash
   ADMIN_PASSWORD=YourStrongAdminPassword123!
   ACCESS_PASSWORD=YourStrongAccessPassword456@
   ```

3. 生成强密码的方法：
   ```python
   python -c "
   import secrets
   import string
   alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
   password = ''.join(secrets.choice(alphabet) for i in range(16))
   print('推荐密码:', password)
   "
   ```

### 环境变量说明

| 变量 | 说明 | 是否必需 |
|------|------|----------|
| APP_NAME | 应用名称 | 否 |
| DEBUG | 调试模式 | 否 |
| SECRET_KEY | 应用密钥 | 是 |
| GEMINI_API_KEY | Google AI API密钥 | 否（可使用服务账号） |
| GEMINI_MODEL | 使用的模型 | 否 |
| GCP_PROJECT | GCP项目ID | 是 |
| GCP_LOCATION | GCP地区 | 否 |
| DATABASE_URL | 数据库连接URL | 否 |
| ADMIN_PASSWORD | 管理员密码 | 是 |
| ACCESS_PASSWORD | 访问密码 | 是 |

### 安全检查机制

系统在启动时会自动进行安全检查，包括：
- 验证密码强度是否符合要求
- 检测是否使用了默认或常见密码
- 确保关键配置项不为空

如果安全检查失败，系统将拒绝启动并显示相应的错误信息。