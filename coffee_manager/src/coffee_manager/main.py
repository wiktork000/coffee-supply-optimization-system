import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from coffee_manager.database import Base, engine
from coffee_manager.routers import (
    api_keys,
    auth,
    buildings,
    distributors,
    inventory,
    optimization,
    orders,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Bootstrap: Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    print("Bootstrap: Database tables ready.")
    yield


app = FastAPI(title="Coffee Supply Management API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(traceback.format_exc(), status_code=500)


app.include_router(auth.router)
app.include_router(distributors.router)
app.include_router(api_keys.router)
app.include_router(buildings.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(optimization.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "coffee-supply-api", "version": "1.0.0"}
