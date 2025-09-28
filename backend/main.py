from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import queries, connections, schema, exports
from app.core.config import settings

app = FastAPI(
    title="AskDash API",
    description="AI-powered database query dashboard API",
    version="1.0.0",
)

# CORS middleware to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])
app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
app.include_router(schema.router, prefix="/api/schema", tags=["schema"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])

@app.get("/")
async def root():
    return {"message": "AskDash API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)