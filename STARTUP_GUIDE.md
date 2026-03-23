# EgoZone Secure Startup Guide

## 🔒 Important Security Notice

Due to the implementation of enhanced security mechanisms, EgoZone now **requires** the use of strong passwords. The service cannot be started with default passwords.

## 📋 Pre-Startup Preparation

### 1. Check Current Security Status
Run the following command to check security configuration:
```bash
python3 -c "from core.security_config import SecurityConfig; result = SecurityConfig.validate_security_configuration(); print('Security Status:', '✅ Secure' if result['is_secure'] else '❌ Needs Fix'); print('Issues:', result['issues'])"
```

### 2. Set Strong Passwords

#### Method A: Use Environment Variable File (Recommended)
1. Copy the secure example file:
```bash
cp .env.example.secure .env
```

2. Edit the `.env` file and change passwords to strong ones:
```bash
# Administrator password (must contain uppercase, lowercase letters, numbers, special characters, 12+ characters)
ADMIN_PASSWORD=YourSecureAdminPass123!@#

# Access password (must contain uppercase, lowercase letters, numbers, special characters, 12+ characters)
ACCESS_PASSWORD=YourSecureAccessPass456!@#
```

3. Ensure passwords meet requirements:
   - ✅ At least 12 characters
   - ✅ Contains uppercase letters (A-Z)
   - ✅ Contains lowercase letters (a-z)
   - ✅ Contains numbers (0-9)
   - ✅ Contains special characters (!@#$%^&* etc.)
   - ✅ Does not contain common words or personal information

#### Method B: Generate Strong Password
Use the built-in password generator:
```python
python3 -c "from core.password_validator import PasswordValidator; validator = PasswordValidator(); pwd = validator.generate_strong_password(16); print('Generated strong password:', pwd)"
```

### 3. Validate Password Strength
```bash
python3 -c "from core.password_validator import PasswordValidator; validator = PasswordValidator(); is_valid, errors = validator.validate_password('YourPasswordHere'); print('Valid:', is_valid); print('Errors:', errors)"
```

## 🚀 Start the Application

### Standard Startup
```bash
python3 main.py
```

### Background Startup (Recommended)
```bash
nohup python3 main.py > egozone.log 2>&1 &
echo $! > egozone.pid
```

### Using Startup Script
```bash
chmod +x start_service.sh
./start_service.sh
```

## ✅ Verify Successful Startup

### Check Service Status
```bash
# View process
ps aux | grep "python3 main.py"

# Check port
netstat -tlnp | grep 8000

# Test health check endpoint
curl http://localhost:8000/health
```

### Verify Security Features
1. **Test Default Password Rejection**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "Wuya2bu2.egozone"}'
# Should return 401 Unauthorized
```

2. **Test Rate Limiting**:
```bash
# Quickly send multiple wrong password requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"password": "wrongpassword"}'
done
# Should trigger 429 Too Many Requests
```

3. **Test Token Persistence**:
```bash
# Login with correct password
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "YourSecureAdminPass123!@#"}'
# Should return a valid token
```

## 🔧 Troubleshooting

### Problem 1: Service Won't Start
**Symptoms**: Exits immediately after startup, no error message
**Solution**: Check security logs, run security check command
```bash
python3 -c "from core.security_config import SecurityConfig; result = SecurityConfig.validate_security_configuration(); print('Issues:', result['issues'])"
```

### Problem 2: Password Rejected
**Symptoms**: Cannot login even with new password
**Solution**: Ensure password meets all requirements, check case sensitivity and special characters

### Problem 3: Rate Limiting False Trigger
**Symptoms**: Normal users get locked out
**Solution**: Wait 30 minutes for automatic unlock, or clear rate limit data
```bash
python3 -c "from core.rate_limiter import cleanup_rate_limit_data; cleanup_rate_limit_data()"
```

## 📊 Security Monitoring

### View Security Logs
```bash
tail -f egozone.log | grep -E "(Security|Login)"
```

### Check Login Statistics
```bash
python3 -c "from core.rate_limiter import get_login_stats; stats = get_login_stats('admin', '127.0.0.1'); print('Login stats:', stats)"
```

### Verify Security Configuration
```bash
python3 -c "
from core.security_config import SecurityConfig
result = SecurityConfig.validate_security_configuration()
print('🔒 Security Configuration Status:', '✅ Secure' if result['is_secure'] else '❌ Needs Fix')
if result['issues']:
    print('Issues:')
    for issue in result['issues']:
        print(f'  ❌ {issue}')
if result['warnings']:
    print('Warnings:')
    for warning in result['warnings']:
        print(f'  ⚠️  {warning}')
"
```

## 🛡️ Security Best Practices

### Production Environment Recommendations
1. **Use HTTPS**: Configure SSL/TLS certificates
2. **Reverse Proxy**: Use Nginx/Apache as reverse proxy
3. **Firewall**: Configure appropriate firewall rules
4. **Regular Updates**: Keep system and dependencies updated
5. **Monitoring & Alerts**: Set up security event monitoring
6. **Backup Strategy**: Regularly backup configuration and data

### Password Management
1. **Regular Rotation**: Change passwords every 3-6 months
2. **Different Systems**: Use different passwords for different systems
3. **Password Manager**: Use professional password management tools
4. **Avoid Reuse**: Do not reuse passwords across multiple systems

## 📞 Support

If you encounter startup issues:
1. First run the security check command
2. Check application logs for detailed information
3. Verify password strength requirements
4. Check if port is already in use
5. Refer to the troubleshooting section

**Important Reminder**: Security mechanisms are designed to protect your system. Please always use strong passwords and keep them secure.