# EgoZone GCP 部署指南

## 前置条件

1. **GCP 账号**：需要有 Google Cloud Platform 账号
2. **gcloud CLI**：已安装并完成认证
3. **域名**：已购买并准备好的域名

## 快速部署

### 1. 安装 gcloud CLI（如未安装）

```bash
# macOS
brew install google-cloud-sdk

# 或者从官网下载
# https://cloud.google.com/sdk/docs/install
```

### 2. 认证并设置项目

```bash
# 登录 GCP
gcloud auth login

# 创建新项目（如果需要）
gcloud projects create egozone --name="EgoZone"

# 设置当前项目
gcloud config set project egozone

# 关联计费账号（必须）
gcloud billing projects link egozone --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 3. 设置环境变量

```bash
# 设置项目 ID
export GCP_PROJECT_ID="egozone"

# 设置区域（推荐亚洲区域）
export GCP_REGION="asia-east1"  # 台湾，网络延迟较低

# 注意：无需设置 GEMINI_API_KEY
# 本项目使用 Vertex AI 服务账号自动认证
```

### 4. 一键部署

```bash
# 进入项目目录
cd /Users/ezio/Documents/My\ Projects/EgoZone

# 运行部署脚本
./deploy.sh
```

## 配置自定义域名

### 方式一：使用 Cloud Run 域名映射

```bash
# 验证域名所有权（首次需要）
gcloud domains verify egoz.one

# 创建域名映射
gcloud run domain-mappings create \
    --service=egozone \
    --domain=egoz.one \
    --region=asia-east1

# 查看 DNS 配置要求
gcloud run domain-mappings describe \
    --domain=egoz.one \
    --region=asia-east1
```

### DNS 配置

在你的域名 DNS 设置中添加：

| 类型 | 名称 | 值 |
|------|------|------|
| A | @ | 负载均衡器 IP |
| CNAME | www | egoz.one |

## 成本估算

| 服务 | 估算费用（月） |
|------|----------------|
| Cloud Run | $5-20（按实际使用） |
| Cloud Build | 免费（前 120 分钟/天） |
| Cloud Storage | $1-2 |
| Load Balancer | $18+（如使用） |
| **总计** | **$5-40** |

> 💡 Cloud Run 在无请求时可缩容到 0 实例，非常经济

## 常用命令

```bash
# 查看服务状态
gcloud run services describe egozone --region=asia-east1

# 查看日志
gcloud run services logs read egozone --region=asia-east1

# 更新环境变量（示例）
gcloud run services update egozone \
    --region=asia-east1 \
    --set-env-vars "ADMIN_PASSWORD=新密码"

# 回滚到上一版本
gcloud run services update-traffic egozone \
    --region=asia-east1 \
    --to-revisions=REVISION_NAME=100

# 删除服务
gcloud run services delete egozone --region=asia-east1
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
gcloud run services logs read egozone --region=asia-east1 --limit=50

# 检查服务状态
gcloud run services describe egozone --region=asia-east1 --format="yaml(status)"
```

### 域名无法访问

1. 检查 DNS 是否已生效：`dig 你的域名.com`
2. SSL 证书签发可能需要 24 小时
3. 确认域名已验证所有权

## 自动化部署（CI/CD）

项目已包含 `cloudbuild.yaml`，可配置自动部署：

1. 在 Cloud Build 中创建触发器
2. 连接 GitHub/GitLab 仓库
3. 设置触发条件（如 push 到 main 分支）
4. 无需配置 API Key（使用 Vertex AI 服务账号）

每次代码推送后会自动构建并部署！
