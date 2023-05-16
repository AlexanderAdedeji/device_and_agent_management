from fastapi import APIRouter
from backend.app.api.routes import authentication, users, user_types, device, api_key,agent

router = APIRouter()
router.include_router(authentication.router, tags=["Authentication"], prefix="/auth")
router.include_router(agent.router, tags=['Agents'], prefix='/agents')
router.include_router(users.router, tags=["User"], prefix="/users")
router.include_router(user_types.router, tags=["User Types"], prefix="/user_types")
router.include_router(device.router, tags=["Devices"], prefix="/devices")
router.include_router(api_key.router, tags=["API Keys"], prefix="/api_keys")

