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

# Include routers
app.include_router(dogs.router)
app.include_router(health.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "PedigreeDatabase API is running"}

# Development mode only
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting PedigreeDatabase development server...")
    print("🌐 Main App: http://127.0.0.1:8007")
    print("📊 Swagger UI: http://127.0.0.1:8007/docs")
    print("📖 ReDoc: http://127.0.0.1:8007/redoc")
    print("💚 Health Check: http://127.0.0.1:8007/health")
    uvicorn.run(app, host="127.0.0.1", port=8007)
