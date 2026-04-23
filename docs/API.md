"""DevFlow Engine API Documentation

# Overview

DevFlow Engine provides a RESTful API for managing AI-driven development pipelines.
All operations are exposed through HTTP endpoints with JSON request/response bodies.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. In production, implement JWT or API key authentication.

## Common Headers

```
Content-Type: application/json
Accept: application/json
```

## Error Responses

All errors follow a standard format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

# Endpoints

## Health

### Health Check

Check API health status.

```
GET /health
```

**Response**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "api": true,
    "llm": true
  }
}
```

---

## Pipelines

### Create Pipeline

Create a new pipeline definition.

```
POST /pipelines
```

**Request Body**

```json
{
  "name": "My Pipeline",
  "description": "Pipeline description",
  "stages": [
    {
      "id": "demand-analysis",
      "name": "需求分析",
      "stage_type": "demand_analysis",
      "description": "Analyze requirements",
      "agent": {
        "name": "DemandAnalyzer",
        "provider": "openai",
        "model": "gpt-4-turbo-preview",
        "system_prompt": "",
        "temperature": 0.7,
        "max_tokens": 4096
      },
      "is_checkpoint": false,
      "depends_on": []
    }
  ]
}
```

**Response** (201 Created)

```json
{
  "id": "uuid",
  "name": "My Pipeline",
  "description": "Pipeline description",
  "stages": [...],
  "status": "created",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "metadata": {}
}
```

### List Pipelines

Get all pipelines with pagination.

```
GET /pipelines?page=1&page_size=20
```

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (1-indexed) |
| page_size | int | 20 | Items per page (max 100) |

**Response**

```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### Get Pipeline

Get a specific pipeline.

```
GET /pipelines/{pipeline_id}
```

**Response**

```json
{
  "id": "uuid",
  "name": "My Pipeline",
  ...
}
```

### Update Pipeline

Update a pipeline.

```
PUT /pipelines/{pipeline_id}
```

**Request Body**

```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Pipeline

Delete a pipeline.

```
DELETE /pipelines/{pipeline_id}
```

**Response**: 204 No Content

---

## Executions

### Create Execution

Create and start a pipeline execution.

```
POST /executions
```

**Request Body**

```json
{
  "pipeline_id": "pipeline-uuid",
  "demand": "用户需要登录功能...",
  "config": {}
}
```

**Response** (201 Created)

```json
{
  "id": "execution-uuid",
  "pipeline_id": "pipeline-uuid",
  "status": "pending",
  "current_stage_id": null,
  "results": {},
  "checkpoints": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "completed_at": null
}
```

### List Executions

Get all executions with optional pipeline filter.

```
GET /executions?pipeline_id=pipeline-uuid&page=1&page_size=20
```

**Query Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| pipeline_id | string | Filter by pipeline ID |
| page | int | Page number |
| page_size | int | Items per page |

### Get Execution Status

Get detailed execution status.

```
GET /executions/{execution_id}
```

**Response**

```json
{
  "id": "execution-uuid",
  "pipeline_id": "pipeline-uuid",
  "status": "running",
  "current_stage_id": "code-generation",
  "current_stage_name": "代码生成",
  "progress": 60.0,
  "results": {
    "demand-analysis": {
      "stage_id": "demand-analysis",
      "status": "completed",
      "output": {"response": "..."},
      "artifacts": [],
      "started_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:01:00Z"
    }
  },
  "checkpoints": {},
  "error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:02:00Z"
}
```

### Cancel Execution

Cancel a running execution.

```
POST /executions/{execution_id}/cancel
```

### Pause Execution

Pause a running execution.

```
POST /executions/{execution_id}/pause
```

### Resume Execution

Resume a paused execution.

```
POST /executions/{execution_id}/resume
```

---

## Checkpoints

### List Pending Checkpoints

Get all pending approval checkpoints.

```
GET /checkpoints?execution_id=execution-uuid
```

**Response**

```json
{
  "items": [
    {
      "id": "checkpoint-uuid",
      "execution_id": "execution-uuid",
      "stage_id": "scheme-design",
      "stage_result": {...},
      "status": "waiting_approval",
      "created_at": "2024-01-01T00:00:00Z",
      "decided_at": null,
      "decided_by": null,
      "comment": null,
      "approval_action": null
    }
  ],
  "total": 1,
  "pending": 1
}
```

### Get Checkpoint

Get a specific checkpoint.

```
GET /checkpoints/{execution_id}/{stage_id}
```

### Approve Checkpoint

Approve a checkpoint to proceed.

```
POST /checkpoints/{execution_id}/{stage_id}/approve
```

**Request Body**

```json
{
  "comment": "方案看起来不错，同意继续",
  "approver": "human"
}
```

### Reject Checkpoint

Reject a checkpoint and trigger rollback.

```
POST /checkpoints/{execution_id}/{stage_id}/reject
```

**Request Body**

```json
{
  "comment": "方案需要修改，API设计不够清晰",
  "rejector": "human"
}
```

### Get Checkpoint Summary

Get summary of all checkpoints for an execution.

```
GET /checkpoints/{execution_id}/summary
```

**Response**

```json
{
  "execution_id": "execution-uuid",
  "total": 2,
  "pending": 1,
  "approved": 1,
  "rejected": 0,
  "checkpoints": [...]
}
```

---

# Stage Types

| Type | Description |
|------|-------------|
| `demand_analysis` | Analyze and structure requirements |
| `scheme_design` | Design technical solution |
| `code_generation` | Generate code changes |
| `code_review` | Review code quality |
| `delivery` | Prepare delivery package |

---

# Execution Status

| Status | Description |
|--------|-------------|
| `pending` | Execution created, not started |
| `running` | Currently executing |
| `waiting_approval` | Paused at checkpoint |
| `approved` | Checkpoint approved |
| `rejected` | Checkpoint rejected |
| `completed` | Successfully completed |
| `failed` | Execution failed |
| `cancelled` | Execution cancelled |

---

# Example Usage

## cURL Examples

### Create Pipeline

```bash
curl -X POST http://localhost:8000/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Pipeline",
    "description": "A demo pipeline",
    "stages": [...]
  }'
```

### Start Execution

```bash
curl -X POST http://localhost:8000/executions \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "your-pipeline-id",
    "demand": "我需要一个登录功能..."
  }'
```

### Check Execution Status

```bash
curl http://localhost:8000/executions/execution-id
```

### Approve Checkpoint

```bash
curl -X POST http://localhost:8000/checkpoints/execution-id/scheme-design/approve \
  -H "Content-Type: application/json" \
  -d '{"comment": "同意此方案"}'
```

## Python Client Example

```python
import httpx
import asyncio

async def main():
    client = httpx.AsyncClient(base_url="http://localhost:8000")

    # Create execution
    response = await client.post("/executions", json={
        "pipeline_id": "your-pipeline-id",
        "demand": "我需要一个登录功能..."
    })
    execution = response.json()
    execution_id = execution["id"]

    # Poll for status
    while True:
        response = await client.get(f"/executions/{execution_id}")
        status = response.json()

        if status["status"] == "waiting_approval":
            print("Checkpoint reached! Review required.")
            # Get checkpoint details
            checkpoint = await client.get(
                f"/checkpoints/{execution_id}/{status['current_stage_id']}"
            )
            print(checkpoint.json())
            break

        if status["status"] == "completed":
            print("Pipeline completed!")
            break

        await asyncio.sleep(5)

asyncio.run(main())
```

---

# OpenAPI/Swagger

Full API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
"""
