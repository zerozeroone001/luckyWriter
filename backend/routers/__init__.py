from routers.novels import router as novels_router
from routers.characters import router as characters_router
from routers.chapters import router as chapters_router
from routers.channels import router as channels_router
from routers.ai import router as ai_router
from routers.outlines import router as outlines_router

__all__ = [
    "novels_router",
    "characters_router",
    "chapters_router",
    "channels_router",
    "ai_router",
    "outlines_router",
]
