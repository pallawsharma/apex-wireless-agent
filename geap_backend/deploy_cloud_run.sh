#!/usr/bin/env bash
# ==============================================================================
# Deploy Script: Apex Wireless GEAP Multi-Agent Microservice to Google Cloud Run
# Target Project: NextGen Sandbox (354292934503)
# ==============================================================================

set -e

PROJECT_ID="${PROJECT_ID:-google.com:nextgen-sandbox}"
PROJECT_NUMBER="${PROJECT_NUMBER:-354292934503}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="apex-wireless-geap-backend"
IMAGE_NAME="gcr.io/${PROJECT_NUMBER}/${SERVICE_NAME}:latest"
AUTH_TOKEN="${APEX_AUTH_TOKEN:-apex-enterprise-secret-token-2026}"

echo "======================================================================"
echo "Deploying ${SERVICE_NAME} to Google Cloud Run"
echo "Project: ${PROJECT_ID} (${PROJECT_NUMBER}) | Region: ${REGION}"
echo "======================================================================"

# 1. Build container image via Google Cloud Build
echo "Building container image with Cloud Build..."
gcloud builds submit --project="${PROJECT_NUMBER}" --tag="${IMAGE_NAME}" .

# 2. Deploy to Cloud Run with IAM service account and authentication
echo "Deploying image to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_NUMBER}" \
    --image="${IMAGE_NAME}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=${PROJECT_NUMBER},GOOGLE_CLOUD_LOCATION=${REGION},APEX_ENFORCE_AUTH=1,APEX_AUTH_TOKEN=${AUTH_TOKEN}"

# 3. Retrieve service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_NUMBER}" --region="${REGION}" --format='value(status.url)')

echo "======================================================================"
echo "Deployment successful!"
echo "Service URL: ${SERVICE_URL}"
echo "Health Check: curl -s ${SERVICE_URL}/healthz"
echo "OpenAPI Dispatch: POST ${SERVICE_URL}/api/dispatch"
echo "Dialogflow CX Webhook: POST ${SERVICE_URL}/webhook/cx"
echo "======================================================================"
