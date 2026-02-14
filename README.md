# EgoZone - AI 数字分身

基于 Gemini 3.0 Flash 的个人 AI 数字分身系统。

## 功能特性

- 🧠 **个性化对话**：模拟用户的说话风格和思维方式
- 📚 **知识库管理**：导入和管理个人知识、经验
- 📄 **多格式文档导入**：支持 PDF、DOCX、CSV、网页等多种格式文档导入
- 💬 **智能对话记忆**：支持重要性评分、token数量限制的智能上下文管理
- 🎤 **语音交互**：支持语音输入和输出
- 🤖 **平台集成**：Telegram Bot 等平台接入

## 环境要求

- Python 3.9+ (推荐 3.10+)
- OpenSSL 1.1.1+ (用于 SSL/TLS 连接)

## 快速开始

### 1. 环境准备

#### 推荐方式：使用虚拟环境
```bash
# 创建并激活虚拟环境
python -m venv egozone_env
source egozone_env/bin/activate  # Linux/macOS
# 或
egozone_env\Scripts\activate   # Windows

# 升级 pip
pip install --upgrade pip
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 4. 运行服务

```bash
python -m uvicorn main:app --reload
```

## API 端点

- `POST /api/chat/send` - 发送消息
- `GET /api/chat/history/{chat_id}` - 获取对话历史
- `POST /api/documents/upload/pdf` - 上传并导入 PDF
- `POST /api/documents/upload/docx` - 上传并导入 DOCX
- `POST /api/documents/import/webpage` - 导入网页内容
- `POST /api/documents/import/text` - 导入文本内容
- `POST /api/documents/upload/csv` - 上传并导入 CSV

## 环境故障排除

如果遇到兼容性问题，请运行环境检查工具：
```bash
python check_environment.py
```

## 项目结构

```
EgoZone/
├── main.py                 # 应用入口
├── config.py               # 配置管理
├── core/                   # 核心模块
│   ├── personality_engine.py   # 个性化引擎
│   ├── user_profile.py         # 用户画像
│   ├── knowledge_base.py       # 知识库及文档导入
│   └── memory.py               # 智能对话记忆
├── api/                    # API 路由
│   ├── chat.py
│   ├── knowledge.py
│   └── documents.py          # 文档导入 API
├── data/                   # 数据存储
├── check_environment.py      # 环境兼容性检查工具
└── web/                    # 前端应用
```

## 许可证

MIT License
