from datetime import datetime
from fastapi import Request

async def log_request_data(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    print(f"Request: {request.method} {request.url} completed in {process_time}s")
    return response
