#!/usr/bin/env bash
set -e

echo "=== Building Backend with SAM ==="
sam build -t backend/template.yaml

echo "=== Deploying Backend with SAM (Guided) ==="
sam deploy --guided --template-file .aws-sam/build/template.yaml
