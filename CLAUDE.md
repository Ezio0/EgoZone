# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# EgoZone - AI 数字分身项目指南

## 项目概述
EgoZone 是一个基于 Google Gemini 的个人 AI 数字分身系统，具有个性化对话、知识库管理、语音交互和平台集成功能。

## 技术架构
- **后端**: Python FastAPI
- **AI 引擎**: Google Gemini (通过 Vertex AI SDK)
- **数据库**: SQLite (默认) 或 PostgreSQL + pgvector
- **向量存储**: ChromaDB
- **前端**: React + TypeScript (位于 web/ 目录)

## 核心组件架构
- [main.py](main.py): 应用入口，负责初始化所有核心组件
- [core/](core/) 目录包含：
  - [gemini_client.py](core/gemini_client.py): 封装 Vertex AI 客户端，处理 Gemini API 调用
  - [personality_engine.py](core/personality_engine.py): 个性化对话引擎，整合用户画像、知识库和对话记忆
  - [user_profile.py](core/user_profile.py): 用户画像管理系统
  - [knowledge_base.py](core/knowledge_base.py): 知识库管理 (使用 ChromaDB)
  - [memory.py](core/memory.py): 对话记忆和历史管理
- [api/](api/) 目录包含所有 REST API 路由

## 开发命令
- **安装依赖**: `pip install -r requirements.txt`
- **运行开发服务器**: `python -m uvicorn main:app --reload`
- **运行测试** (如果有): `pytest` 或 `python -m pytest`
- **运行单个测试**: `python -m pytest path/to/test_file.py`

## 配置管理
- 配置通过 [config.py](config.py) 中的 Settings 类管理
- 环境变量存储在 `.env` 文件中 (参考 `.env.example`)
- 主要配置包括：GCP 项目信息、Gemini 模型设置、数据库连接、管理员密码等

## API 端点
- `/api/chat/` - 对话功能 (发送消息、获取历史)
- `/api/knowledge/` - 知识库管理
- `/api/interview/` - 问答采集功能
- `/api/auth/` - 认证功能
- `/api/settings/` - 设置管理

## 认证机制
- 管理员功能需要密码保护 (默认密码在 config.py 中)
- 对话功能有公共访问密码 (防止滥用)

## 部署选项
- **本地运行**: 使用 uvicorn 直接启动
- **容器化**: 使用 [Dockerfile](Dockerfile)，暴露 8080 端口
- **GCP 部署**: 支持 Cloud Run 等部署方式 (参考 DEPLOY.md)

## 重要注意事项
- 项目使用 Vertex AI SDK，需正确配置 GCP 凭据
- 对话历史存储在内存中，可通过 GCS 持久化
- 生产环境中需要更改默认的管理员和访问密码