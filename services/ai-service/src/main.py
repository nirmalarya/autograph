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
from .analytics import (
    get_analytics,
    GenerationAnalytics,
    GENERATION_PRESETS,
    PROMPT_TEMPLATES,
    get_prompt_template,
    PROVIDER_PRICING,
)

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


# =============================================================================
# Feature #341-350: AI Generation Analytics and Management
# =============================================================================


class GenerationSettingsRequest(BaseModel):
    """Request to generate with custom settings."""
    prompt: str
    diagram_type: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature (0-2)")
    max_tokens: int = Field(2000, ge=100, le=4000, description="Max tokens")
    preset: Optional[str] = Field(None, description="Use preset (creative, balanced, precise, concise, detailed)")
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class RegenerateRequest(BaseModel):
    """Request to regenerate from a previous generation."""
    generation_id: str
    user_id: Optional[str] = None


class CostOptimizationRequest(BaseModel):
    """Request for cost-optimized generation."""
    prompt: str
    diagram_type: Optional[str] = None
    optimize_for: str = Field("balance", description="balance, cost, quality, or speed")


@app.post("/api/ai/generate-with-settings")
async def generate_with_settings(request: GenerationSettingsRequest):
    """
    Feature #348-349: Generate diagram with custom temperature and max_tokens.
    
    Supports presets: creative, balanced, precise, concise, detailed
    """
    try:
        analytics = get_analytics()
        
        # Apply preset if specified
        temperature = request.temperature
        max_tokens = request.max_tokens
        
        if request.preset and request.preset in GENERATION_PRESETS:
            preset = GENERATION_PRESETS[request.preset]
            temperature = preset["temperature"]
            max_tokens = preset["max_tokens"]
        
        # Get provider
        provider_name = request.provider or "bayer_mga"
        model_name = request.model
        
        factory = AIProviderFactory()
        provider = factory.get_provider(provider_name)
        
        if not model_name:
            model_name = provider.get_default_model()
        
        # Start tracking
        import time
        start_time = time.time()
        
        record = analytics.start_generation(
            prompt=request.prompt,
            diagram_type=request.diagram_type or "architecture",
            provider=provider_name,
            model=model_name,
            user_id=request.user_id,
            session_id=request.session_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Generate
        result = await provider.generate_diagram(
            prompt=request.prompt,
            diagram_type=DiagramType(request.diagram_type) if request.diagram_type else None,
            model=model_name
        )
        
        generation_time = time.time() - start_time
        
        # Validate quality
        validator = QualityValidator()
        quality_report = validator.validate_diagram(result["mermaid_code"])
        
        # Complete tracking
        analytics.complete_generation(
            record=record,
            mermaid_code=result["mermaid_code"],
            tokens_used=result.get("tokens_used", 0),
            generation_time=generation_time,
            quality_score=quality_report.overall_score,
            quality_details={
                "has_overlaps": quality_report.has_overlaps,
                "min_spacing": quality_report.min_spacing,
                "alignment_score": quality_report.alignment_score,
                "readability_score": quality_report.readability_score,
            }
        )
        
        return {
            "generation_id": record.generation_id,
            "mermaid_code": result["mermaid_code"],
            "diagram_type": result.get("diagram_type", "unknown"),
            "explanation": result.get("explanation", ""),
            "provider": provider_name,
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "preset_used": request.preset,
            "tokens_used": result.get("tokens_used", 0),
            "generation_time": generation_time,
            "quality_score": quality_report.overall_score,
            "cost_estimate": record.cost_estimate.cost_usd if record.cost_estimate else 0.0,
        }
        
    except Exception as e:
        logger.error(f"Generation with settings failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate: {str(e)}"
        )


@app.get("/api/ai/generation-presets")
async def get_generation_presets():
    """
    Feature #348: Get available generation presets.
    """
    return {
        "presets": GENERATION_PRESETS
    }


@app.get("/api/ai/generation-history")
async def get_generation_history(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Feature #346: Get generation history with pagination.
    """
    try:
        analytics = get_analytics()
        history = analytics.get_generation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        
        return {
            "generations": history,
            "count": len(history),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )


@app.get("/api/ai/generation/{generation_id}")
async def get_generation(generation_id: str):
    """
    Feature #346: Get specific generation by ID.
    """
    try:
        analytics = get_analytics()
        generation = analytics.get_generation_by_id(generation_id)
        
        if not generation:
            raise HTTPException(
                status_code=404,
                detail=f"Generation {generation_id} not found"
            )
        
        return generation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get generation: {str(e)}"
        )


@app.post("/api/ai/regenerate")
async def regenerate(request: RegenerateRequest):
    """
    Feature #347: Regenerate from a previous generation using same prompt.
    """
    try:
        analytics = get_analytics()
        
        # Get previous generation
        previous = analytics.get_generation_by_id(request.generation_id)
        if not previous:
            raise HTTPException(
                status_code=404,
                detail=f"Generation {request.generation_id} not found"
            )
        
        # Regenerate with same settings
        factory = AIProviderFactory()
        provider = factory.get_provider(previous["provider"])
        
        import time
        start_time = time.time()
        
        # Start new tracking
        record = analytics.start_generation(
            prompt=previous["prompt"],
            diagram_type=previous["diagram_type"],
            provider=previous["provider"],
            model=previous["model"],
            user_id=request.user_id,
            session_id=previous.get("session_id"),
            temperature=previous.get("temperature", 0.7),
            max_tokens=previous.get("max_tokens", 2000),
        )
        
        # Generate
        result = await provider.generate_diagram(
            prompt=previous["prompt"],
            diagram_type=DiagramType(previous["diagram_type"]) if previous["diagram_type"] else None,
            model=previous["model"]
        )
        
        generation_time = time.time() - start_time
        
        # Validate quality
        validator = QualityValidator()
        quality_report = validator.validate_diagram(result["mermaid_code"])
        
        # Complete tracking
        analytics.complete_generation(
            record=record,
            mermaid_code=result["mermaid_code"],
            tokens_used=result.get("tokens_used", 0),
            generation_time=generation_time,
            quality_score=quality_report.overall_score,
            quality_details={
                "has_overlaps": quality_report.has_overlaps,
                "min_spacing": quality_report.min_spacing,
                "alignment_score": quality_report.alignment_score,
                "readability_score": quality_report.readability_score,
            }
        )
        
        return {
            "generation_id": record.generation_id,
            "original_generation_id": request.generation_id,
            "mermaid_code": result["mermaid_code"],
            "diagram_type": result.get("diagram_type", "unknown"),
            "explanation": result.get("explanation", ""),
            "provider": previous["provider"],
            "model": previous["model"],
            "tokens_used": result.get("tokens_used", 0),
            "generation_time": generation_time,
            "quality_score": quality_report.overall_score,
            "cost_estimate": record.cost_estimate.cost_usd if record.cost_estimate else 0.0,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regenerate failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate: {str(e)}"
        )


@app.get("/api/ai/provider-comparison")
async def get_provider_comparison():
    """
    Feature #343: Compare providers by quality, cost, and performance.
    """
    try:
        analytics = get_analytics()
        comparison = analytics.get_provider_comparison()
        
        return {
            "providers": comparison,
            "count": len(comparison),
        }
    except Exception as e:
        logger.error(f"Provider comparison failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare providers: {str(e)}"
        )


@app.post("/api/ai/suggest-provider")
async def suggest_provider(request: CostOptimizationRequest):
    """
    Feature #344-345: Suggest best provider/model based on optimization criteria.
    
    optimize_for options:
    - balance: Best overall (default)
    - cost: Cheapest option
    - quality: Highest quality
    - speed: Fastest generation
    """
    try:
        analytics = get_analytics()
        
        provider, model, reason = analytics.suggest_best_provider(
            prompt=request.prompt,
            diagram_type=request.diagram_type or "architecture",
            optimize_for=request.optimize_for,
        )
        
        # Get pricing info
        pricing = PROVIDER_PRICING.get(provider, {}).get(model, {})
        
        return {
            "recommended_provider": provider,
            "recommended_model": model,
            "reason": reason,
            "optimize_for": request.optimize_for,
            "pricing": {
                "prompt_cost_per_1k": pricing.get("prompt", 0.01),
                "completion_cost_per_1k": pricing.get("completion", 0.03),
            }
        }
    except Exception as e:
        logger.error(f"Provider suggestion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest provider: {str(e)}"
        )


@app.get("/api/ai/usage-summary")
async def get_usage_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    Feature #341-342: Get usage summary with token and cost totals.
    """
    try:
        analytics = get_analytics()
        
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        summary = analytics.get_usage_summary(
            start_date=start_dt,
            end_date=end_dt,
        )
        
        return summary
    except Exception as e:
        logger.error(f"Usage summary failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage summary: {str(e)}"
        )


@app.get("/api/ai/pricing")
async def get_pricing():
    """
    Feature #342: Get pricing information for all providers and models.
    """
    return {
        "pricing": PROVIDER_PRICING,
        "currency": "USD",
        "unit": "per 1000 tokens",
    }


@app.get("/api/ai/prompt-templates")
async def get_prompt_templates():
    """
    Feature #350: Get available prompt templates.
    """
    return {
        "templates": PROMPT_TEMPLATES,
        "categories": list(PROMPT_TEMPLATES.keys()),
    }


@app.get("/api/ai/prompt-template/{category}/{template_name}")
async def get_specific_prompt_template(
    category: str,
    template_name: str,
):
    """
    Feature #350: Get a specific prompt template.
    """
    if category not in PROMPT_TEMPLATES:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found"
        )
    
    templates = PROMPT_TEMPLATES[category]
    if template_name not in templates:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found in category '{category}'"
        )
    
    return {
        "category": category,
        "template_name": template_name,
        "template": templates[template_name],
    }


@app.get("/api/ai/available-models")
async def get_available_models():
    """
    Feature #344: Get all available models by provider.
    """
    return {
        "providers": {
            "bayer_mga": {
                "models": ["gpt-4.1", "gpt-4-turbo", "gpt-3.5-turbo"],
                "default": "gpt-4.1",
                "description": "Bayer MGA (Primary Provider)",
            },
            "openai": {
                "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "default": "gpt-4-turbo",
                "description": "OpenAI (Fallback 1)",
            },
            "anthropic": {
                "models": ["claude-3-5-sonnet", "claude-3-sonnet", "claude-3-haiku"],
                "default": "claude-3-5-sonnet",
                "description": "Anthropic (Fallback 2)",
            },
            "gemini": {
                "models": ["gemini-1.5-pro", "gemini-pro"],
                "default": "gemini-pro",
                "description": "Google Gemini (Fallback 3)",
            },
        }
    }


# ============================================================================
# FEATURES #354-365: PROMPT ENGINEERING & ADVANCED GENERATION
# ============================================================================

from .prompt_engineering import (
    get_prompt_engineer,
    get_diagram_analyzer,
    PROMPT_BEST_PRACTICES,
    PROMPT_EXAMPLES,
)
from .error_handling import (
    get_error_handler,
    AIServiceError,
    ErrorCode,
)


class AnalyzePromptRequest(BaseModel):
    """Request to analyze prompt quality."""
    prompt: str


class PromptAnalysisResponse(BaseModel):
    """Response with prompt analysis."""
    original_prompt: str
    quality: str
    quality_score: float
    issues: List[str]
    suggestions: List[str]
    improved_prompt: Optional[str]
    estimated_complexity: str
    detected_type: Optional[str]
    detected_technologies: List[str]


class AutocompleteRequest(BaseModel):
    """Request for prompt autocomplete."""
    partial_prompt: str
    limit: int = 5


class ExplainDiagramRequest(BaseModel):
    """Request to explain a diagram."""
    mermaid_code: str
    diagram_type: str
    original_prompt: str


class CritiqueDiagramRequest(BaseModel):
    """Request to critique a diagram."""
    mermaid_code: str
    diagram_type: str
    original_prompt: str


class BatchGenerateRequest(BaseModel):
    """Request to generate multiple diagram variations."""
    prompt: str
    variations: int = Field(3, ge=1, le=5, description="Number of variations (1-5)")
    diagram_type: Optional[str] = None
    provider: Optional[str] = None


class GenerationProgressUpdate(BaseModel):
    """Progress update during generation."""
    generation_id: str
    status: str
    progress: float  # 0-100
    message: str
    timestamp: str


@app.get("/api/ai/best-practices")
async def get_prompt_best_practices():
    """
    Feature #354: Get prompt engineering best practices guide.
    """
    return {
        "best_practices": PROMPT_BEST_PRACTICES,
        "examples": PROMPT_EXAMPLES,
        "tips": [
            "Always specify the technology stack",
            "Mention the diagram type if known",
            "Describe relationships and data flow",
            "Include context about system purpose",
            "Be specific about components",
        ]
    }


@app.post("/api/ai/analyze-prompt")
async def analyze_prompt(request: AnalyzePromptRequest):
    """
    Feature #355: Analyze prompt quality and provide suggestions.
    
    Returns quality assessment and improvement suggestions.
    """
    engineer = get_prompt_engineer()
    analysis = engineer.analyze_prompt(request.prompt)
    
    # Add to history
    engineer.add_to_history(request.prompt)
    
    return PromptAnalysisResponse(
        original_prompt=analysis.original_prompt,
        quality=analysis.quality.value,
        quality_score=analysis.quality_score,
        issues=analysis.issues,
        suggestions=analysis.suggestions,
        improved_prompt=analysis.improved_prompt,
        estimated_complexity=analysis.estimated_complexity.value,
        detected_type=analysis.detected_type,
        detected_technologies=analysis.detected_technologies
    )


@app.post("/api/ai/autocomplete-prompt")
async def autocomplete_prompt(request: AutocompleteRequest):
    """
    Feature #360: Autocomplete prompt from history.
    
    Returns matching prompts from user's history.
    """
    engineer = get_prompt_engineer()
    suggestions = engineer.autocomplete_prompt(request.partial_prompt, request.limit)
    
    return {
        "partial": request.partial_prompt,
        "suggestions": suggestions,
        "count": len(suggestions)
    }


@app.post("/api/ai/explain-diagram")
async def explain_diagram(request: ExplainDiagramRequest):
    """
    Feature #357: Generate explanation of a diagram.
    
    AI analyzes the diagram and provides human-readable explanation.
    """
    analyzer = get_diagram_analyzer()
    explanation = analyzer.explain_diagram(
        request.mermaid_code,
        request.diagram_type,
        request.original_prompt
    )
    
    return {
        "explanation": explanation,
        "diagram_type": request.diagram_type,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/ai/critique-diagram")
async def critique_diagram(request: CritiqueDiagramRequest):
    """
    Feature #358: Critique diagram and suggest improvements.
    Feature #356: AI suggestions to add missing components.
    
    AI analyzes diagram quality and suggests improvements.
    """
    analyzer = get_diagram_analyzer()
    critique = analyzer.critique_diagram(
        request.mermaid_code,
        request.diagram_type,
        request.original_prompt
    )
    
    return {
        "critique": critique,
        "diagram_type": request.diagram_type,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/ai/batch-generate")
async def batch_generate(request: BatchGenerateRequest):
    """
    Feature #361: Generate multiple diagram variations.
    
    Generates multiple variations of the same diagram with different approaches.
    """
    variations = []
    
    # Different temperature settings for variations
    temperatures = [0.3, 0.7, 0.9][:request.variations]
    
    for i, temp in enumerate(temperatures, 1):
        try:
            # Create variation with different temperature
            gen_request = GenerateDiagramRequest(
                prompt=request.prompt,
                diagram_type=request.diagram_type,
                provider=request.provider,
            )
            
            # Generate with custom settings
            factory = AIProviderFactory()
            provider = factory.get_provider(
                provider_name=request.provider,
                model=None
            )
            
            # Get analytics for tracking
            analytics = get_analytics()
            gen_id = analytics.start_generation(
                prompt=request.prompt,
                diagram_type=request.diagram_type or "architecture",
                provider=provider.provider_name,
                model=provider.model_name,
                temperature=temp,
                max_tokens=2000,
                user_id=None,
                session_id=None
            )
            
            # Generate
            result = await provider.generate_diagram(request.prompt, request.diagram_type)
            
            # Track completion
            analytics.complete_generation(
                generation_id=gen_id,
                mermaid_code=result.get("mermaid_code", ""),
                tokens_used=result.get("tokens_used", 0),
                quality_score=None
            )
            
            variations.append({
                "variation_number": i,
                "temperature": temp,
                "mermaid_code": result.get("mermaid_code", ""),
                "diagram_type": result.get("diagram_type", request.diagram_type),
                "explanation": result.get("explanation", ""),
            })
            
        except Exception as e:
            logger.error(f"Error generating variation {i}: {str(e)}")
            variations.append({
                "variation_number": i,
                "temperature": temp,
                "error": str(e)
            })
    
    return {
        "prompt": request.prompt,
        "variations": variations,
        "total_variations": len(variations),
        "successful": sum(1 for v in variations if "error" not in v),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/ai/generation-progress/{generation_id}")
async def get_generation_progress(generation_id: str):
    """
    Feature #362: Get generation progress status.
    
    Returns current progress of an ongoing generation.
    """
    analytics = get_analytics()
    generation = analytics.get_generation(generation_id)
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Determine progress based on generation state
    if generation.success:
        status = "completed"
        progress = 100.0
        message = "Generation completed successfully"
    elif generation.error:
        status = "failed"
        progress = 100.0
        message = f"Generation failed: {generation.error}"
    else:
        status = "in_progress"
        progress = 50.0
        message = "Generating diagram..."
    
    return GenerationProgressUpdate(
        generation_id=generation_id,
        status=status,
        progress=progress,
        message=message,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/api/ai/error-statistics")
async def get_error_statistics():
    """
    Get error statistics for monitoring.
    
    Returns error counts and most common errors.
    """
    error_handler = get_error_handler()
    stats = error_handler.get_error_statistics()
    
    return {
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/ai/supported-languages")
async def get_supported_languages():
    """
    Feature #359: Get supported languages for multi-language prompts.
    
    Returns list of supported language codes.
    """
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "de", "name": "Deutsch (German)"},
            {"code": "es", "name": "Español (Spanish)"},
            {"code": "fr", "name": "Français (French)"},
        ],
        "default": "en",
        "note": "Prompts can be provided in any of these languages. Error messages will be returned in the requested language."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AI_SERVICE_PORT", "8084")))
