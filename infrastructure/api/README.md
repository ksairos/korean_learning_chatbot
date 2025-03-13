# API Server Module

This module implements a FastAPI server for webhook handling and API endpoints.

## Overview

The API server provides HTTP endpoints for Telegram webhooks and additional functionality for external systems. It shares the same configuration as the main bot.

## Key Components

- **app.py**: Defines the FastAPI application with:
  - Webhook endpoint for receiving updates
  - Integration with the bot instance
  - Logging configuration
  
- **requirements.txt**: Lists dependencies specific to the API server

## Usage

### Running the API Server

With Docker Compose:
```bash
docker-compose up api
```

Standalone:
```bash
cd infrastructure/api
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Setting Up Telegram Webhooks

1. Configure your Telegram Bot to use webhooks:
```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://yourdomain.com/webhook
```

2. Ensure the API server is accessible at the configured URL

### Adding New Endpoints

Add new endpoints in app.py:

```python
@app.get("/api/resource")
async def get_resource():
    # Implementation
    return {"status": "success", "data": {...}}
```

## Security Considerations

- The API server should be placed behind a reverse proxy (e.g., Nginx)
- API endpoints should implement proper authentication
- Webhook endpoints should validate Telegram's signature when possible