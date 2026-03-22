# EgoZone - AI Digital Twin

A personal AI digital twin system based on Gemini 3.0 Flash.

## Features

- 🧠 **Personalized Conversations**: Simulate user's speaking style and thinking patterns
- 📚 **Knowledge Base Management**: Import and manage personal knowledge and experiences
- 📄 **Multi-format Document Import**: Support PDF, DOCX, CSV, web pages and other formats
- 💬 **Smart Conversation Memory**: Intelligent context management with importance scoring and token limits
- 🎤 **Voice Interaction**: Support voice input and output
- 🤖 **Platform Integration**: Telegram Bot and other platform integrations

## Security Requirements

EgoZone adopts strict password policies. Please follow these security configuration requirements:

1. **Strong Password Policy**: Passwords must contain uppercase and lowercase letters, numbers, and special characters, with a minimum of 12 characters
2. **Default Password Disabled**: Default password configurations must not be used
3. **Environment Isolation**: Sensitive configurations must be set through environment variables

## Requirements

- Python 3.9+ (3.10+ recommended)
- OpenSSL 1.1.1+ (for SSL/TLS connections)

## Quick Start

### 1. Environment Setup

#### Recommended: Use Virtual Environment
```bash
# Create and activate virtual environment
python -m venv egozone_env
source egozone_env/bin/activate  # Linux/macOS
# or
egozone_env\Scripts\activate   # Windows

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Security Settings

#### Option 1: Use Auto Configuration Tool
```bash
# Run security configuration initialization script
python init_security.py
```

#### Option 2: Manual Configuration
```bash
# Copy example configuration
cp .env.example .env

# Edit .env file, set strong passwords and API keys
nano .env  # or use your preferred editor
```

### 4. Run Service

```bash
python -m uvicorn main:app --reload
```

## API Endpoints

- `POST /api/chat/send` - Send message
- `GET /api/chat/history/{chat_id}` - Get chat history
- `POST /api/documents/upload/pdf` - Upload and import PDF
- `POST /api/documents/upload/docx` - Upload and import DOCX
- `POST /api/documents/import/webpage` - Import web page content
- `POST /api/documents/import/text` - Import text content
- `POST /api/documents/upload/csv` - Upload and import CSV

## Environment Troubleshooting

If you encounter compatibility issues, run the environment check tool:
```bash
python check_environment.py
```

## Project Structure

```
EgoZone/
├── main.py                 # Application entry
├── config.py               # Configuration management
├── core/                   # Core modules
│   ├── personality_engine.py   # Personality engine
│   ├── user_profile.py         # User profile
│   ├── knowledge_base.py       # Knowledge base and document import
│   └── memory.py               # Smart conversation memory
├── api/                    # API routes
│   ├── chat.py
│   ├── knowledge.py
│   └── documents.py          # Document import API
├── data/                   # Data storage
├── check_environment.py      # Environment compatibility check tool
└── web/                    # Frontend application
```

## License

MIT License
