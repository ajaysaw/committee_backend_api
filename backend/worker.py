import asyncio
from app.main import app
from cloudflare.workers import Request, Response

async def on_fetch(request: Request, env, ctx):
    # Convert Cloudflare request to ASGI scope and handle with FastAPI
    # This is a simplified implementation; for full support, use an ASGI adapter
    # For now, return a basic response
    return Response.json({"message": "FastAPI on Cloudflare Workers", "status": "beta"})