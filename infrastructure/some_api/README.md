# External API Integration Module

This module provides integration with external APIs for the Korean Learning Bot.

## Overview

External API integrations often require resilient connection handling, proper error management, and consistent interfaces. This module implements these concerns with a robust client architecture.

## Key Components

- **base.py**: Implements a robust BaseClient with:
  - Automatic retries with exponential backoff
  - Connection pooling and session management
  - Error handling and logging

- **api.py**: Implements the specific API client using the BaseClient

## Usage

```python
from infrastructure.some_api.api import ApiClient

async def get_data():
    client = ApiClient()
    try:
        # The client handles retries and error logging internally
        data = await client.get_resource("endpoint/path")
        return data
    finally:
        # Always close the client when done
        await client.close()
```

## Adding New API Integrations

To integrate with a new API:

1. Create a new class extending BaseClient
2. Implement specific API methods using the base client's request methods
3. Add proper error handling for API-specific errors
4. Document the available methods and parameters

All clients should handle:
- Authentication and token refresh
- Rate limits through backoff strategies
- Connection pooling for efficiency
- Clean resource release