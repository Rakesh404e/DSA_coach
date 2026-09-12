# Architecture: Test-Case Triage Coach

## Overview
- **Backend Graph**: LangGraph state graph evaluating user code against test cases in a sandboxed runtime.
- **Classification & Hints**: Amazon Bedrock classifies failures and generates progressive hints across 3 tiers (0: conceptual nudge, 1: targeted pointer, 2: full patch).
- **Session Persistence**: Amazon DynamoDB stores triage state and tracks hint escalation across attempts.
- **Serverless API**: AWS SAM (API Gateway + AWS Lambda).
- **Frontend**: Astro application with an interactive form island.
