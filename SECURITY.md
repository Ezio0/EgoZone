# EgoZone Security Configuration Guide

## Security Configuration Requirements

The EgoZone project enforces a strict password policy to ensure system security.

### Password Strength Requirements

1. **Administrator Password** (`ADMIN_PASSWORD`)
   - Minimum 12 characters
   - Must contain uppercase letters, lowercase letters, numbers, and special characters
   - Cannot use common password patterns (such as 123, abc, password, etc.)

2. **Access Password** (`ACCESS_PASSWORD`)
   - Minimum 12 characters
   - Must contain uppercase letters, lowercase letters, numbers, and special characters
   - Cannot use common password patterns

### Configuration Instructions

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Modify passwords in the `.env` file:
   ```bash
   ADMIN_PASSWORD=YourStrongAdminPassword123!
   ACCESS_PASSWORD=YourStrongAccessPassword456@
   ```

3. Method to generate strong passwords:
   ```python
   python -c "
   import secrets
   import string
   alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
   password = ''.join(secrets.choice(alphabet) for i in range(16))
   print('Recommended password:', password)
   "
   ```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| APP_NAME | Application name | No |
| DEBUG | Debug mode | No |
| SECRET_KEY | Application secret key | Yes |
| GEMINI_API_KEY | Google AI API key | No (service account can be used) |
| GEMINI_MODEL | Model to use | No |
| GCP_PROJECT | GCP project ID | Yes |
| GCP_LOCATION | GCP region | No |
| DATABASE_URL | Database connection URL | No |
| ADMIN_PASSWORD | Administrator password | Yes |
| ACCESS_PASSWORD | Access password | Yes |

### Security Check Mechanism

The system automatically performs security checks at startup, including:
- Verifying password strength meets requirements
- Detecting use of default or common passwords
- Ensuring critical configuration items are not empty

If security checks fail, the system will refuse to start and display corresponding error messages.