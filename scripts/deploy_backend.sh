#!/usr/bin/env bash
set -e

STACK_NAME=${STACK_NAME:-"dsa-coach-backend"}
REGION=${AWS_REGION:-"us-east-1"}
PROFILE=${AWS_PROFILE:-"rakesh"}

echo "=== Building Backend with SAM (Containerized) ==="
sam build -t backend/template.yaml --use-container

echo "=== Deploying Backend with SAM ==="
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --profile "$PROFILE" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-fail-on-empty-changeset

echo "=== Deployment Completed ==="
