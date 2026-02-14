# EgoZone 聊天错误修复说明

如果你在使用 EgoZone 时遇到聊天功能报错，很可能是由于 Google Cloud 配置问题。以下是解决方案：

## 问题原因

错误通常是这样的：
```
404 Publisher Model `projects/.../models/gemini-...` was not found or your project does not have access to it
```

这是因为在没有正确配置 Google Cloud 或无效的 Gemini API 访问权限时，应用无法连接到 Gemini 模型。

## 解决方案

### 方案1：使用 Google AI Studio API（推荐）

1. 访问 [Google AI Studio](https://aistudio.google.com/) 并获取 API 密钥
2. 编辑 `.env` 文件，设置：
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   GEMINI_MODEL=gemini-1.5-pro
   ```
3. 重启应用

### 方案2：配置 Vertex AI（适用于已有 GCP 环境的用户）

1. 确保已正确配置 Google Cloud 项目
2. 启用 Vertex AI API
3. 确保项目 ID 和区域设置正确
4. 确保有适当的 IAM 权限

## 主要改进

我们已更新 `core/gemini_client.py` 文件以支持双模式：

- 当提供了 `GEMINI_API_KEY` 时，使用 Google AI Studio API
- 当未提供 `GEMINI_API_KEY` 时，回退到 Vertex AI
- 这样用户可以选择更容易上手的 API Key 方式

## 验证修复

设置好 API 密钥后，应用应该能正常处理聊天请求而不再报错。