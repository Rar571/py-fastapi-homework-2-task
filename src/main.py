from fastapi import FastAPI, Request
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"


@app.exception_handler(ValidationError)
async def handle_validation_exceptions(request: Request, exception: ValidationError):
    return JSONResponse(status_code=400, content={"detail": "Invalid input data."})

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
