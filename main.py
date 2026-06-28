from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from routers import auth, users, abilities, jobs, contracts, websockets
from models import all_tables
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):


    yield


app = FastAPI(
    lifespan=lifespan,
    title="Services API",
    description="Marketplace Services API",
    version="1.0.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(abilities.router)
app.include_router(jobs.router)
app.include_router(contracts.router)
app.include_router(websockets.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def bad_request(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": True, "status_code": 422, "detail": "Bad Request"}
    )

@app.exception_handler(HTTPException)
async def httpexeption(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "status_code": exc.status_code, "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": True, "status_code": 500, "detail": "an error occours"}

    )