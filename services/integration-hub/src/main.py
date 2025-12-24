"""Integration Hub - Notion, Confluence, Slack, Jira integrations."""
from fastapi import FastAPI
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AutoGraph v3 Integration Hub",
    description="Third-party integrations service",
    version="1.0.0"
)

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "integration-hub",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("INTEGRATION_HUB_PORT", "8099")))
