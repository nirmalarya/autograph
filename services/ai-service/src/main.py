"""AI Service - AI diagram generation with MGA."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import logging
from dotenv import load_dotenv

from .providers import AIProviderFactory, DiagramType

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AutoGraph v3 AI Service",
    description="AI diagram generation service with Bayer MGA primary provider",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class GenerateDiagramRequest(BaseModel):
    """Request to generate a diagram."""
    prompt: str = Field(..., description="Natural language prompt describing the diagram")
    diagram_type: Optional[str] = Field(None, description="Preferred diagram type (architecture, sequence, erd, flowchart)")
    model: Optional[str] = Field(None, description="Specific AI model to use")
    provider: Optional[str] = Field(None, description="Specific provider (bayer_mga, openai, anthropic, gemini)")


class GenerateDiagramResponse(BaseModel):
    """Response containing generated diagram."""
    mermaid_code: str
    diagram_type: str
    explanation: str
    provider: str
    model: str
    tokens_used: int
    timestamp: str


class ProvidersStatusResponse(BaseModel):
    """Status of configured AI providers."""
    primary_provider: Optional[str]
    available_providers: List[str]
    fallback_chain: List[str]
    mga_configured: bool
    openai_configured: bool
    anthropic_configured: bool
    gemini_configured: bool


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/ai/providers", response_model=ProvidersStatusResponse)
async def get_providers_status():
    """Get status of configured AI providers."""
    mga_key = os.getenv("MGA_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    available = []
    fallback_chain = []
    
    if mga_key:
        available.append("bayer_mga")
        fallback_chain.append("Bayer MGA (PRIMARY)")
    if openai_key:
        available.append("openai")
        fallback_chain.append("OpenAI (Fallback 1)")
    if anthropic_key:
        available.append("anthropic")
        fallback_chain.append("Anthropic (Fallback 2)")
    if gemini_key:
        available.append("gemini")
        fallback_chain.append("Gemini (Fallback 3)")
    
    return {
        "primary_provider": "bayer_mga" if mga_key else (available[0] if available else None),
        "available_providers": available,
        "fallback_chain": fallback_chain,
        "mga_configured": bool(mga_key),
        "openai_configured": bool(openai_key),
        "anthropic_configured": bool(anthropic_key),
        "gemini_configured": bool(gemini_key)
    }


@app.post("/api/ai/generate", response_model=GenerateDiagramResponse)
async def generate_diagram(request: GenerateDiagramRequest):
    """
    Generate a diagram from natural language prompt.
    
    Uses Bayer MGA as primary provider with automatic fallback chain:
    MGA → OpenAI → Anthropic → Gemini
    """
    try:
        logger.info(f"Generating diagram for prompt: {request.prompt[:100]}...")
        
        # Convert diagram_type string to enum if provided
        diagram_type_enum = None
        if request.diagram_type:
            try:
                diagram_type_enum = DiagramType(request.diagram_type.lower())
            except ValueError:
                logger.warning(f"Invalid diagram type: {request.diagram_type}, will auto-detect")
        
        # Generate using fallback chain
        result = await AIProviderFactory.generate_with_fallback(
            prompt=request.prompt,
            diagram_type=diagram_type_enum,
            model=request.model
        )
        
        # Add timestamp
        result["timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(f"✓ Successfully generated {result['diagram_type']} diagram using {result['provider']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Diagram generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate diagram: {str(e)}"
        )


@app.post("/api/ai/refine")
async def refine_diagram(
    current_code: str,
    refinement_prompt: str,
    model: Optional[str] = None
):
    """
    Refine an existing diagram based on feedback.
    
    Example: "Make the database node bigger" or "Add caching layer"
    """
    try:
        # Build refinement prompt
        full_prompt = f"""Current Mermaid diagram:
{current_code}

Refinement request: {refinement_prompt}

Generate an improved version of this diagram incorporating the requested changes. Output only valid Mermaid code."""
        
        result = await AIProviderFactory.generate_with_fallback(
            prompt=full_prompt,
            diagram_type=None,
            model=model
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Diagram refinement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine diagram: {str(e)}"
        )


@app.get("/api/ai/models")
async def get_available_models():
    """Get list of available models per provider."""
    return {
        "bayer_mga": {
            "models": ["gpt-4.1", "gpt-4", "gpt-3.5-turbo"],
            "default": "gpt-4.1"
        },
        "openai": {
            "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "default": "gpt-4-turbo"
        },
        "anthropic": {
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
            "default": "claude-3-5-sonnet-20241022"
        },
        "gemini": {
            "models": ["gemini-pro", "gemini-1.5-pro"],
            "default": "gemini-pro"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AI_SERVICE_PORT", "8084")))
