"""AI Service - AI diagram generation with MGA."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import os
import logging
from dotenv import load_dotenv
import uuid

from .providers import AIProviderFactory, DiagramType
from .layout_algorithms import LayoutAlgorithm
from .icon_intelligence import IconIntelligence
from .quality_validation import QualityValidator, QualityReport
from .refinement import (
    IterativeRefinement, 
    SessionContextManager, 
    RefinementHistory
)
from .templates import DiagramTemplateLibrary, DiagramDomain

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
    layout_algorithm: Optional[str] = Field(None, description="Layout algorithm (force_directed, tree, circular, hierarchical)")
    enable_quality_validation: bool = Field(True, description="Enable quality validation with auto-retry")
    enable_icon_intelligence: bool = Field(True, description="Enable icon intelligence")


class GenerateDiagramResponse(BaseModel):
    """Response containing generated diagram."""
    mermaid_code: str
    diagram_type: str
    explanation: str
    provider: str
    model: str
    tokens_used: int
    timestamp: str
    quality_score: Optional[float] = None
    quality_passed: Optional[bool] = None
    quality_issues: Optional[List[str]] = None
    quality_metrics: Optional[Dict] = None
    icon_suggestions: Optional[List[Dict]] = None
    layout_algorithm: Optional[str] = None
    enhanced: Optional[bool] = False


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
    
    New Features:
    - Layout algorithms: force-directed, tree, circular (Features #321-323)
    - Icon intelligence: auto-detect AWS, Azure, GCP services (Features #324-326)
    - Quality validation: check overlaps, spacing, alignment (Features #327-330)
    - Auto-retry: regenerate if quality score < 80
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
        
        # Convert layout_algorithm string to enum if provided
        layout_algorithm_enum = None
        if request.layout_algorithm:
            try:
                layout_algorithm_enum = LayoutAlgorithm(request.layout_algorithm.lower())
            except ValueError:
                logger.warning(f"Invalid layout algorithm: {request.layout_algorithm}")
        
        # Generate using enhanced method
        result = await AIProviderFactory.generate_enhanced(
            prompt=request.prompt,
            diagram_type=diagram_type_enum,
            model=request.model,
            layout_algorithm=layout_algorithm_enum,
            enable_icon_intelligence=request.enable_icon_intelligence,
            enable_quality_validation=request.enable_quality_validation
        )
        
        # Add timestamp
        result["timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(f"✓ Successfully generated {result['diagram_type']} diagram using {result['provider']}")
        
        if result.get('quality_score'):
            logger.info(f"  Quality score: {result['quality_score']:.1f}/100")
        
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


@app.post("/api/ai/validate")
async def validate_diagram(mermaid_code: str, context: str = ""):
    """
    Validate diagram quality.
    
    Features #327-330:
    - Check overlapping nodes
    - Check spacing minimum 50px
    - Check alignment
    - Calculate readability score 0-100
    
    Returns quality score and improvement suggestions.
    """
    try:
        validation = QualityValidator.validate_diagram(mermaid_code, context)
        report = QualityReport.generate_report(validation)
        suggestions = QualityValidator.generate_improvement_suggestions(validation)
        
        return {
            "score": validation.score,
            "passed": validation.passed,
            "issues": validation.issues,
            "metrics": validation.metrics,
            "suggestions": suggestions,
            "report": report
        }
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate diagram: {str(e)}"
        )


@app.get("/api/ai/suggest-icons")
async def suggest_icons(prompt: str):
    """
    Suggest appropriate icons based on prompt.
    
    Features #324-326: Icon intelligence
    - Detects AWS, Azure, GCP services
    - Maps databases and frameworks
    - Context-aware suggestions
    """
    try:
        suggestions = IconIntelligence.suggest_icons(prompt)
        
        return {
            "suggestions": [
                {"service": service, "icon": icon}
                for service, icon in suggestions
            ],
            "count": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Icon suggestion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest icons: {str(e)}"
        )


@app.get("/api/ai/enhance-with-icons")
async def enhance_with_icons(mermaid_code: str, context: str = ""):
    """
    Enhance Mermaid diagram with icon labels.
    
    Feature #326: Context-aware icon selection
    """
    try:
        enhanced_code = IconIntelligence.enhance_mermaid_with_icons(mermaid_code, context)
        validation = IconIntelligence.validate_icon_usage(enhanced_code)
        
        return {
            "original_code": mermaid_code,
            "enhanced_code": enhanced_code,
            "validation": validation
        }
    except Exception as e:
        logger.error(f"Icon enhancement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enhance with icons: {str(e)}"
        )


@app.get("/api/ai/layout-algorithms")
async def get_layout_algorithms():
    """
    Get available layout algorithms.
    
    Features #321-323:
    - Force-directed layout
    - Tree layout
    - Circular layout
    - Hierarchical layout (default)
    """
    return {
        "algorithms": [
            {
                "id": "hierarchical",
                "name": "Hierarchical (Sugiyama)",
                "description": "Default Mermaid layout, good for most diagrams",
                "use_cases": ["architecture", "flowchart", "general"]
            },
            {
                "id": "force_directed",
                "name": "Force-Directed",
                "description": "Spring/physics-based layout, nodes repel and edges attract",
                "use_cases": ["network", "relationship", "graph"]
            },
            {
                "id": "tree",
                "name": "Tree Layout",
                "description": "Hierarchical tree structure, good for org charts",
                "use_cases": ["hierarchy", "org_chart", "file_system"]
            },
            {
                "id": "circular",
                "name": "Circular Layout",
                "description": "Nodes arranged in a circle",
                "use_cases": ["small_graphs", "relationships", "cycles"]
            }
        ],
        "default": "hierarchical"
    }


@app.post("/api/ai/refine-diagram")
async def refine_diagram_endpoint(
    current_code: str,
    refinement_prompt: str,
    session_id: Optional[str] = None,
    model: Optional[str] = None
):
    """
    Iteratively refine an existing diagram.
    
    Features #332-335:
    - #332: 'Add caching layer'
    - #333: 'Make database bigger'
    - #334: 'Change colors to blue'
    - #335: Context awareness (remembers session)
    """
    try:
        # Get or create session context (Feature #335)
        context = None
        if session_id:
            context_mgr = SessionContextManager()
            context = context_mgr.get_session(session_id)
        
        # Build refinement prompt (Features #332-334)
        enhanced_prompt = IterativeRefinement.build_refinement_prompt(
            current_code, 
            refinement_prompt,
            context
        )
        
        # Generate refined diagram
        result = await AIProviderFactory.generate_with_fallback(
            prompt=enhanced_prompt,
            diagram_type=None,
            model=model
        )
        
        # Apply heuristics to validate refinement
        refined_code = IterativeRefinement.apply_refinement_heuristics(
            current_code,
            result["mermaid_code"],
            refinement_prompt
        )
        
        result["mermaid_code"] = refined_code
        result["timestamp"] = datetime.utcnow().isoformat()
        result["refinement_applied"] = True
        
        # Detect refinement type
        refinement_info = IterativeRefinement.detect_refinement_type(refinement_prompt)
        result["refinement_type"] = refinement_info["type"]
        
        logger.info(
            f"✓ Successfully refined diagram: {refinement_info['type']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Diagram refinement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine diagram: {str(e)}"
        )


@app.get("/api/ai/templates")
async def get_templates(domain: Optional[str] = None):
    """
    Get diagram templates.
    
    Feature #336: Template-based generation
    Features #337-340: Domain-specific templates
    """
    try:
        # Parse domain if provided
        domain_enum = None
        if domain:
            try:
                domain_enum = DiagramDomain(domain.lower())
            except ValueError:
                pass
        
        templates = DiagramTemplateLibrary.list_templates_by_domain(domain_enum)
        
        return {
            "templates": templates,
            "domains": [d.value for d in DiagramDomain],
            "count": len(templates)
        }
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get templates: {str(e)}"
        )


@app.post("/api/ai/generate-from-template")
async def generate_from_template(
    prompt: str,
    template_id: Optional[str] = None,
    domain: Optional[str] = None,
    model: Optional[str] = None
):
    """
    Generate diagram using template.
    
    Feature #336: Template-based generation
    Features #337-340: Domain-specific generation
    """
    try:
        # Find matching template
        template = None
        
        if template_id:
            # Use specified template
            template_data = DiagramTemplateLibrary.TEMPLATES.get(template_id)
            if template_data:
                template = {"id": template_id, **template_data}
        else:
            # Auto-detect template from prompt
            template = DiagramTemplateLibrary.find_matching_template(prompt)
        
        if template:
            logger.info(f"Using template: {template['id']}")
            enhanced_prompt = DiagramTemplateLibrary.enhance_prompt_with_template(
                prompt, template
            )
        else:
            # No template found, use domain-specific guidance
            domain_enum = DiagramDomain(domain.lower()) if domain else None
            if not domain_enum:
                domain_enum = DiagramTemplateLibrary.detect_domain(prompt)
            
            guidance = DiagramTemplateLibrary.get_domain_specific_guidance(domain_enum)
            enhanced_prompt = f"{prompt}\n\n{guidance}" if guidance else prompt
            
            logger.info(f"Using domain guidance: {domain_enum}")
        
        # Generate diagram
        result = await AIProviderFactory.generate_with_fallback(
            prompt=enhanced_prompt,
            diagram_type=None,
            model=model
        )
        
        result["timestamp"] = datetime.utcnow().isoformat()
        result["template_used"] = template["id"] if template else None
        result["domain_detected"] = DiagramTemplateLibrary.detect_domain(prompt).value
        
        return result
        
    except Exception as e:
        logger.error(f"Template-based generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate from template: {str(e)}"
        )


@app.get("/api/ai/detect-domain")
async def detect_domain(prompt: str):
    """
    Detect domain from prompt.
    
    Features #337-340: Domain detection
    """
    try:
        domain = DiagramTemplateLibrary.detect_domain(prompt)
        matching_template = DiagramTemplateLibrary.find_matching_template(prompt)
        
        return {
            "domain": domain.value,
            "matching_template": matching_template["id"] if matching_template else None,
            "available_templates": [
                t["id"] for t in DiagramTemplateLibrary.list_templates_by_domain(domain)
            ]
        }
    except Exception as e:
        logger.error(f"Domain detection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect domain: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AI_SERVICE_PORT", "8084")))
