# EgoZone GCP Deployment Guide

## Prerequisites

1. **GCP Account**: Need a Google Cloud Platform account
2. **gcloud CLI**: Installed and authenticated
3. **Domain Name**: Purchased and ready domain name

## Quick Deployment

### 1. Install gcloud CLI (if not installed)

```bash
# macOS
brew install google-cloud-sdk

# Or download from official website
# https://cloud.google.com/sdk/docs/install
```

### 2. Authenticate and Set Project

```bash
# Login to GCP
gcloud auth login

# Create new project (if needed)
gcloud projects create egozone --name="EgoZone"

# Set current project
gcloud config set project egozone

# Link billing account (required)
gcloud billing projects link egozone --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 3. Set Environment Variables

```bash
# Set project ID
export GCP_PROJECT_ID="egozone"

# Set region (Asian region recommended)
export GCP_REGION="asia-east1"  # Taiwan, lower network latency

# Note: No need to set GEMINI_API_KEY
# This project uses Vertex AI service account for automatic authentication
```

### 4. One-Click Deployment

```bash
# Enter project directory
cd /Users/ezio/Documents/My\ Projects/EgoZone

# Run deployment script
./deploy.sh
```

## Configure Custom Domain

### Method 1: Use Cloud Run Domain Mapping

```bash
# Verify domain ownership (required for first time)
gcloud domains verify egoz.one

# Create domain mapping
gcloud run domain-mappings create \
    --service=egozone \
    --domain=egoz.one \
    --region=asia-east1

# View DNS configuration requirements
gcloud run domain-mappings describe \
    --domain=egoz.one \
    --region=asia-east1
```

### DNS Configuration

Add the following in your domain DNS settings:

| Type | Name | Value |
|------|------|-------|
| A | @ | Load Balancer IP |
| CNAME | www | egoz.one |

## Cost Estimation

| Service | Estimated Cost (Monthly) |
|---------|--------------------------|
| Cloud Run | $5-20 (pay as you go) |
| Cloud Build | Free (first 120 minutes/day) |
| Cloud Storage | $1-2 |
| Load Balancer | $18+ (if used) |
| **Total** | **$5-40** |

> 💡 Cloud Run can scale down to 0 instances when there are no requests, very economical

## Common Commands

```bash
# View service status
gcloud run services describe egozone --region=asia-east1

# View logs
gcloud run services logs read egozone --region=asia-east1

# Update environment variables (example)
gcloud run services update egozone \
    --region=asia-east1 \
    --set-env-vars "ADMIN_PASSWORD=new_password"

# Rollback to previous version
gcloud run services update-traffic egozone \
    --region=asia-east1 \
    --to-revisions=REVISION_NAME=100

# Delete service
gcloud run services delete egozone --region=asia-east1
```

## Troubleshooting

### Service Won't Start

```bash
# View detailed logs
gcloud run services logs read egozone --region=asia-east1 --limit=50

# Check service status
gcloud run services describe egozone --region=asia-east1 --format="yaml(status)"
```

### Domain Cannot Be Accessed

1. Check if DNS has propagated: `dig your-domain.com`
2. SSL certificate issuance may take up to 24 hours
3. Confirm domain ownership has been verified

## Automated Deployment (CI/CD)

The project includes `cloudbuild.yaml` for automated deployment configuration:

1. Create a trigger in Cloud Build
2. Connect GitHub/GitLab repository
3. Set trigger conditions (e.g., push to main branch)
4. No need to configure API Key (uses Vertex AI service account)

Each code push will automatically build and deploy!