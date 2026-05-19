"""
Health check router — a simple "are you alive?" endpoint.

This is like the "open" sign on a shop door. Other services (like the
frontend, or a load balancer) can ping this URL to check if the backend
is running. If they get back {"status": "ok"}, they know everything is fine.
"""

from fastapi import APIRouter


# Create a router for health-related endpoints
router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    """
    Simple endpoint to verify the API is running.
    Returns {"status": "ok"} if everything is fine.

    This endpoint takes no parameters — just call it and see if you
    get a response. If you do, the server is alive!
    """
    return {"status": "ok", "service": "ReaConnect Chat API"}
