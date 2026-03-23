#!/bin/bash
# EgoZone GCP deployment script
# Please ensure gcloud CLI is installed and authenticated before use

set -e

# Configuration variables
PROJECT_ID="${GCP_PROJECT_ID:-egozone}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="egozone"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting deployment of EgoZone to GCP Cloud Run..."
echo "📦 Project: ${PROJECT_ID}"
echo "🌏 Region: ${REGION}"

# Load .env file
if [ -f .env ]; then
    echo "📄 Loading .env configuration..."
    set -a  # Auto export variables
    source .env
    set +a
fi

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null 2>&1; then
    echo "❌ Please run 'gcloud auth login' to authenticate first"
    exit 1
fi

# Set project
echo "⚙️  Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable necessary APIs
echo "🔧 Enabling necessary GCP APIs..."
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com --quiet

# Build Docker image
echo "🔨 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}:latest .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
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

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📝 Next step: Configure custom domain"
echo "   Run: gcloud run domain-mappings create --service=${SERVICE_NAME} --domain=your-domain --region=${REGION}"