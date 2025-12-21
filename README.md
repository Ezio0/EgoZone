# EgoZone - AI 数字分身

基于 Gemini 3.0 Pro 的个人 AI 数字分身系统。

## 功能特性

- 🧠 **个性化对话**：模拟用户的说话风格和思维方式
- 📚 **知识库管理**：导入和管理个人知识、经验
- 🎤 **语音交互**：支持语音输入和输出
- 🤖 **平台集成**：Telegram Bot 等平台接入

## 技术栈

- **后端**: Python FastAPI
- **前端**: React + TypeScript
- **AI**: Google Gemini 3.0 Pro
- **数据库**: PostgreSQL + pgvector
- **缓存**: Redis

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 3. 运行服务

```bash
python -m uvicorn main:app --reload
```

## 项目结构

```
EgoZone/
├── main.py                 # 应用入口
├── config.py               # 配置管理
├── core/                   # 核心模块
│   ├── personality_engine.py   # 个性化引擎
│   ├── user_profile.py         # 用户画像
│   ├── knowledge_base.py       # 知识库
│   └── memory.py               # 对话记忆
├── api/                    # API 路由
│   ├── chat.py
│   └── knowledge.py
├── data/                   # 数据采集
│   ├── chat_importer.py
│   └── document_importer.py
├── integrations/           # 平台集成
│   └── telegram_bot.py
└── web/                    # 前端应用
```

## 许可证

MIT License
