#!/bin/bash
# EgoZone GCP 部署脚本
# 使用前请确保已安装 gcloud CLI 并完成认证

set -e

# 配置变量
PROJECT_ID="${GCP_PROJECT_ID:-egozone}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="egozone"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 开始部署 EgoZone 到 GCP Cloud Run..."
echo "📦 项目: ${PROJECT_ID}"
echo "🌏 区域: ${REGION}"

# 加载 .env 文件
if [ -f .env ]; then
    echo "📄 加载 .env 配置..."
    set -a  # 自动导出变量
    source .env
    set +a
fi

# 检查 gcloud 是否已认证
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null 2>&1; then
    echo "❌ 请先运行 'gcloud auth login' 完成认证"
    exit 1
fi

# 设置项目
echo "⚙️  设置 GCP 项目..."
gcloud config set project ${PROJECT_ID}

# 启用必要的 API
echo "🔧 启用必要的 GCP API..."
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com --quiet

# 构建 Docker 镜像
echo "🔨 构建 Docker 镜像..."
gcloud builds submit --tag ${IMAGE_NAME}:latest .

# 部署到 Cloud Run
echo "🚀 部署到 Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY},GCP_PROJECT=${GCP_PROJECT},GCP_LOCATION=${GCP_LOCATION},ADMIN_PASSWORD=${ADMIN_PASSWORD},ACCESS_PASSWORD=${ACCESS_PASSWORD},SECRET_KEY=${SECRET_KEY},APP_NAME=${APP_NAME},GEMINI_MODEL=${GEMINI_MODEL}"

# 获取服务 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo ""
echo "✅ 部署完成!"
echo "🌐 服务 URL: ${SERVICE_URL}"
echo ""
echo "📝 下一步: 配置自定义域名"
echo "   运行: gcloud run domain-mappings create --service=${SERVICE_NAME} --domain=你的域名 --region=${REGION}"
