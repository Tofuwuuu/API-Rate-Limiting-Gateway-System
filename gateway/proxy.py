"""Reverse proxy routing for the API gateway."""

import httpx
from fastapi import Request, Response
from fastapi.responses import StreamingResponse

from .config import settings


async def proxy_request(request: Request, target_path: str) -> Response:
    """
    Forward the request to the backend service and stream the response.
    """
    backend_url = settings.upstream_url.rstrip("/")
    target_url = f"{backend_url}{target_path}"

    # Build headers - forward relevant headers, exclude hop-by-hop
    headers = dict(request.headers)
    headers_to_remove = ["host", "connection", "transfer-encoding", "content-length"]
    for h in headers_to_remove:
        headers.pop(h.lower(), None)

    # Read request body
    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )
