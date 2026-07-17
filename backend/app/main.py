from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import chat, profile, recaps

app = FastAPI(title="DrowzyDiary API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(recaps.router)
app.include_router(profile.router)


@app.get("/health")
def health():
    return {"status": "ok"}
