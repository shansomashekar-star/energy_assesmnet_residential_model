
#!/bin/bash

# Configuration
PROJECT_ID="your-gcp-project-id" # REPLACE THIS
APP_NAME="energy-audit-api"
REGION="us-central1"

echo "Deploying $APP_NAME to GCP Project: $PROJECT_ID in $REGION..."

# 1. Enable Services (First time only)
# gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# 2. Submit Build to Container Registry / Artifact Registry
echo "Building container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$APP_NAME

# 3. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $APP_NAME \
  --image gcr.io/$PROJECT_ID/$APP_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2

echo "Deployment Complete!"
echo "Your API URL should be visible above."
echo "Provide this URL to the Lovable App team."
