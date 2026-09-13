#!/usr/bin/env bash
set -e

PROFILE=${AWS_PROFILE:-"rakesh"}
REGION=${AWS_REGION:-"us-east-1"}
BUCKET_NAME=${FRONTEND_BUCKET_NAME:-""}
DISTRIBUTION_ID=${CLOUDFRONT_DIST_ID:-""}

echo "=== Building Frontend with Astro ==="
npm --prefix frontend run build

if [ -z "$BUCKET_NAME" ]; then
  echo "FRONTEND_BUCKET_NAME not set. Built files ready in frontend/dist/"
  echo "To sync to an S3 bucket, set FRONTEND_BUCKET_NAME and run this script again:"
  echo "  FRONTEND_BUCKET_NAME=my-bucket ./scripts/deploy_frontend.sh"
  exit 0
fi

echo "=== Syncing static assets to S3: s3://$BUCKET_NAME ==="
aws s3 sync frontend/dist/ "s3://$BUCKET_NAME" --delete --region "$REGION" --profile "$PROFILE"

if [ -n "$DISTRIBUTION_ID" ]; then
  echo "=== Invalidating CloudFront Cache ==="
  aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*" --profile "$PROFILE"
fi

echo "=== Frontend Deployment Completed ==="
