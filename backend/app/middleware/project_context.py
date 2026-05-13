"""
Project Context Middleware
Intercepts requests and resolves project context from headers
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from ..core.db_router import get_project_db

logger = logging.getLogger(__name__)


class ProjectContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts project context from request headers
    and injects project database connection into request state
    """
    
    # Paths that don't require project context (admin endpoints)
    SKIP_PATHS = [
        "/api/auth/",
        "/api/projects",
        "/api/admin",
        "/api/ai/",  # AI endpoints (admin only)
        "/docs",
        "/openapi.json",
        "/health",
        "/v1/auth/",  # New multi-tenant auth endpoints
        "/"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip middleware for admin endpoints
        if any(request.url.path.startswith(path) for path in self.SKIP_PATHS):
            return await call_next(request)
        
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # Extract project context from headers
            project_id = request.headers.get("x-project-id")
            auth_header = request.headers.get("authorization")
            
            # Log request
            logger.info(f"{request.method} {request.url.path} - Project: {project_id}")
            
            if not project_id:
                logger.warning(f"Missing x-project-id header for {request.url.path}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Missing x-project-id header"}
                )
            
            # Extract ANON_KEY from Bearer token
            anon_key = None
            if auth_header:
                if auth_header.startswith("Bearer "):
                    anon_key = auth_header.split(" ", 1)[1]
                elif auth_header.startswith("bearer "):
                    anon_key = auth_header.split(" ", 1)[1]
            
            if not anon_key:
                logger.warning(f"Missing or invalid Authorization header for {request.url.path}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid Authorization header. Expected: Bearer <ANON_KEY>"}
                )
            
            # Validate and get project database
            try:
                project_db = await get_project_db(project_id, anon_key)
            except HTTPException as e:
                logger.error(f"Project validation failed: {e.detail}")
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
            
            # Inject into request state
            request.state.project_id = project_id
            request.state.project_db = project_db
            request.state.anon_key = anon_key
            
            logger.debug(f"Project context injected: {project_id}")
            
            # Continue to endpoint
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal server error: {str(e)}"}
            )
