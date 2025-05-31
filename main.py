from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from database import engine, Base
from routers import dogs, health
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PedigreeDatabase", description="Dog Pedigree Management System", version="1.0.0")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Test files for mobile localStorage testing
@app.get("/mobile_test.html")
async def mobile_test():
    return FileResponse("mobile_test.html")

@app.get("/test_localStorage.html")  
async def test_localstorage():
    return FileResponse("test_localStorage.html")

@app.get("/test_mobile_storage.html")
async def test_mobile_storage():
    return FileResponse("test_mobile_storage.html")

# Include routers
app.include_router(dogs.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8007)
