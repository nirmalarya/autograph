"""
AI Generation Analytics and Tracking System

Features implemented:
- Feature #341: Token usage tracking
- Feature #342: Cost estimation
- Feature #343: Provider comparison and quality metrics
- Feature #344: Model selection
- Feature #345: Cost optimization
- Feature #346: Generation history
- Feature #347: Regenerate functionality
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """AI Provider types."""
    BAYER_MGA = "bayer_mga"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


@dataclass
class TokenUsage:
    """Token usage data for a generation."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @property
    def usage_ratio(self) -> float:
        """Ratio of completion to prompt tokens."""
        if self.prompt_tokens == 0:
            return 0.0
        return self.completion_tokens / self.prompt_tokens


@dataclass
class CostEstimate:
    """Cost estimation for AI generation."""
    provider: str
    model: str
    token_usage: TokenUsage
    cost_usd: float
    cost_per_1k_prompt: float
    cost_per_1k_completion: float
    
    @classmethod
    def calculate(
        cls,
        provider: str,
        model: str,
        token_usage: TokenUsage,
        pricing: Optional[Dict[str, float]] = None
    ) -> "CostEstimate":
        """Calculate cost based on token usage and pricing."""
        if pricing is None:
            pricing = PROVIDER_PRICING.get(
                provider, 
                {"prompt": 0.01, "completion": 0.03}  # Default pricing
            ).get(model, {"prompt": 0.01, "completion": 0.03})
        
        prompt_cost = (token_usage.prompt_tokens / 1000) * pricing.get("prompt", 0.01)
        completion_cost = (token_usage.completion_tokens / 1000) * pricing.get("completion", 0.03)
        total_cost = prompt_cost + completion_cost
        
        return cls(
            provider=provider,
            model=model,
            token_usage=token_usage,
            cost_usd=total_cost,
            cost_per_1k_prompt=pricing.get("prompt", 0.01),
            cost_per_1k_completion=pricing.get("completion", 0.03)
        )


# Feature #342: Cost estimation - Provider pricing per 1000 tokens (USD)
PROVIDER_PRICING = {
    "bayer_mga": {
        "gpt-4.1": {"prompt": 0.01, "completion": 0.03},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
    },
    "openai": {
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    },
    "gemini": {
        "gemini-pro": {"prompt": 0.0005, "completion": 0.0015},
        "gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
    }
}


@dataclass
class QualityMetrics:
    """Quality metrics for generated diagram."""
    quality_score: float  # 0-100
    has_overlaps: bool
    min_spacing: float
    alignment_score: float
    readability_score: float
    generation_time: float  # seconds
    retry_count: int
    
    @property
    def is_high_quality(self) -> bool:
        """Check if diagram meets high quality threshold."""
        return self.quality_score >= 80.0


@dataclass
class GenerationRecord:
    """Record of a single AI generation."""
    # Identification
    generation_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    
    # Request details
    prompt: str
    diagram_type: str
    provider: str
    model: str
    
    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Results
    mermaid_code: str = ""
    success: bool = False
    error: Optional[str] = None
    
    # Metrics
    token_usage: Optional[TokenUsage] = None
    cost_estimate: Optional[CostEstimate] = None
    quality_metrics: Optional[QualityMetrics] = None
    
    # Timing
    generation_time: float = 0.0  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        result = {
            "generation_id": self.generation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "prompt": self.prompt,
            "diagram_type": self.diagram_type,
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "mermaid_code": self.mermaid_code,
            "success": self.success,
            "error": self.error,
            "generation_time": self.generation_time,
        }
        
        if self.token_usage:
            result["token_usage"] = {
                "prompt_tokens": self.token_usage.prompt_tokens,
                "completion_tokens": self.token_usage.completion_tokens,
                "total_tokens": self.token_usage.total_tokens,
            }
        
        if self.cost_estimate:
            result["cost_estimate"] = {
                "cost_usd": self.cost_estimate.cost_usd,
                "cost_per_1k_prompt": self.cost_estimate.cost_per_1k_prompt,
                "cost_per_1k_completion": self.cost_estimate.cost_per_1k_completion,
            }
        
        if self.quality_metrics:
            result["quality_metrics"] = {
                "quality_score": self.quality_metrics.quality_score,
                "has_overlaps": self.quality_metrics.has_overlaps,
                "min_spacing": self.quality_metrics.min_spacing,
                "alignment_score": self.quality_metrics.alignment_score,
                "readability_score": self.quality_metrics.readability_score,
                "retry_count": self.quality_metrics.retry_count,
            }
        
        return result


@dataclass
class ProviderStats:
    """Statistics for a specific provider."""
    provider: str
    total_generations: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_quality: float = 0.0
    average_generation_time: float = 0.0
    models_used: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_generations == 0:
            return 0.0
        return (self.successful_generations / self.total_generations) * 100
    
    @property
    def cost_per_generation(self) -> float:
        """Average cost per generation."""
        if self.total_generations == 0:
            return 0.0
        return self.total_cost / self.total_generations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "total_generations": self.total_generations,
            "successful_generations": self.successful_generations,
            "failed_generations": self.failed_generations,
            "success_rate": self.success_rate,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "cost_per_generation": self.cost_per_generation,
            "average_quality": self.average_quality,
            "average_generation_time": self.average_generation_time,
            "models_used": self.models_used,
        }


class GenerationAnalytics:
    """
    Feature #341-347: Analytics and tracking for AI diagram generation.
    
    Tracks:
    - Token usage per generation
    - Cost estimates
    - Provider performance
    - Quality metrics
    - Generation history
    """
    
    def __init__(self):
        self.generations: List[GenerationRecord] = []
        self.provider_stats: Dict[str, ProviderStats] = {}
        self._generation_id_counter = 0
    
    def create_generation_id(self) -> str:
        """Create unique generation ID."""
        self._generation_id_counter += 1
        timestamp = int(time.time() * 1000)
        return f"gen_{timestamp}_{self._generation_id_counter}"
    
    def start_generation(
        self,
        prompt: str,
        diagram_type: str,
        provider: str,
        model: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> GenerationRecord:
        """
        Feature #341-346: Start tracking a new generation.
        
        Returns a GenerationRecord that should be updated with results.
        """
        record = GenerationRecord(
            generation_id=self.create_generation_id(),
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            prompt=prompt,
            diagram_type=diagram_type,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        logger.info(
            f"Started generation {record.generation_id}: "
            f"provider={provider}, model={model}, type={diagram_type}"
        )
        
        return record
    
    def complete_generation(
        self,
        record: GenerationRecord,
        mermaid_code: str,
        tokens_used: int,
        generation_time: float,
        quality_score: Optional[float] = None,
        quality_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Feature #341-343: Complete a generation with results and metrics.
        """
        # Update record
        record.mermaid_code = mermaid_code
        record.success = True
        record.generation_time = generation_time
        
        # Calculate token usage (estimate prompt/completion split)
        # In reality, providers return this breakdown
        prompt_tokens = int(tokens_used * 0.3)  # Rough estimate
        completion_tokens = tokens_used - prompt_tokens
        
        record.token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=tokens_used,
        )
        
        # Calculate cost
        record.cost_estimate = CostEstimate.calculate(
            provider=record.provider,
            model=record.model,
            token_usage=record.token_usage,
        )
        
        # Add quality metrics if available
        if quality_score is not None:
            record.quality_metrics = QualityMetrics(
                quality_score=quality_score,
                has_overlaps=quality_details.get("has_overlaps", False) if quality_details else False,
                min_spacing=quality_details.get("min_spacing", 50.0) if quality_details else 50.0,
                alignment_score=quality_details.get("alignment_score", 1.0) if quality_details else 1.0,
                readability_score=quality_details.get("readability_score", 80.0) if quality_details else 80.0,
                generation_time=generation_time,
                retry_count=quality_details.get("retry_count", 0) if quality_details else 0,
            )
        
        # Store record
        self.generations.append(record)
        
        # Update provider stats
        self._update_provider_stats(record)
        
        logger.info(
            f"Completed generation {record.generation_id}: "
            f"tokens={tokens_used}, cost=${record.cost_estimate.cost_usd:.4f}, "
            f"time={generation_time:.2f}s"
        )
    
    def fail_generation(
        self,
        record: GenerationRecord,
        error: str,
        generation_time: float,
    ) -> None:
        """Mark a generation as failed."""
        record.success = False
        record.error = error
        record.generation_time = generation_time
        
        # Store record
        self.generations.append(record)
        
        # Update provider stats
        self._update_provider_stats(record)
        
        logger.error(
            f"Failed generation {record.generation_id}: "
            f"error={error}, time={generation_time:.2f}s"
        )
    
    def _update_provider_stats(self, record: GenerationRecord) -> None:
        """Update provider statistics."""
        provider = record.provider
        
        if provider not in self.provider_stats:
            self.provider_stats[provider] = ProviderStats(provider=provider)
        
        stats = self.provider_stats[provider]
        stats.total_generations += 1
        
        if record.success:
            stats.successful_generations += 1
            
            if record.token_usage:
                stats.total_tokens += record.token_usage.total_tokens
            
            if record.cost_estimate:
                stats.total_cost += record.cost_estimate.cost_usd
            
            if record.quality_metrics:
                # Update rolling average
                n = stats.successful_generations
                stats.average_quality = (
                    stats.average_quality * (n - 1) + record.quality_metrics.quality_score
                ) / n
            
            # Update average generation time
            n = stats.successful_generations
            stats.average_generation_time = (
                stats.average_generation_time * (n - 1) + record.generation_time
            ) / n
        else:
            stats.failed_generations += 1
        
        # Track model usage
        model = record.model
        stats.models_used[model] = stats.models_used.get(model, 0) + 1
    
    def get_generation_history(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Feature #346: Get generation history with optional filtering.
        """
        filtered = self.generations
        
        if user_id:
            filtered = [g for g in filtered if g.user_id == user_id]
        
        if session_id:
            filtered = [g for g in filtered if g.session_id == session_id]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda g: g.timestamp, reverse=True)
        
        # Apply pagination
        paginated = filtered[offset:offset + limit]
        
        return [g.to_dict() for g in paginated]
    
    def get_generation_by_id(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Get specific generation by ID."""
        for gen in self.generations:
            if gen.generation_id == generation_id:
                return gen.to_dict()
        return None
    
    def get_provider_comparison(self) -> List[Dict[str, Any]]:
        """
        Feature #343: Compare providers by quality, cost, and performance.
        """
        return [stats.to_dict() for stats in self.provider_stats.values()]
    
    def suggest_best_provider(
        self,
        prompt: str,
        diagram_type: str,
        optimize_for: str = "balance",  # balance, cost, quality, speed
    ) -> Tuple[str, str, str]:
        """
        Feature #344-345: Suggest best provider/model based on optimization criteria.
        
        Returns: (provider, model, reason)
        """
        if not self.provider_stats:
            # No history, use defaults
            return "bayer_mga", "gpt-4.1", "Default provider (no history)"
        
        # Simple diagram detection (for cost optimization)
        is_simple = len(prompt.split()) < 20 and diagram_type in ["flowchart", "sequence"]
        
        if optimize_for == "cost":
            # Prefer cheaper models for simple diagrams
            if is_simple:
                return "gemini", "gemini-pro", "Cost-optimized for simple diagram"
            return "anthropic", "claude-3-haiku", "Cost-optimized model"
        
        elif optimize_for == "quality":
            # Find provider with highest quality
            best_provider = max(
                self.provider_stats.values(),
                key=lambda s: s.average_quality if s.successful_generations > 0 else 0
            )
            model = list(best_provider.models_used.keys())[0] if best_provider.models_used else "gpt-4.1"
            return best_provider.provider, model, f"Highest quality (avg {best_provider.average_quality:.1f})"
        
        elif optimize_for == "speed":
            # Find provider with fastest generation
            best_provider = min(
                self.provider_stats.values(),
                key=lambda s: s.average_generation_time if s.successful_generations > 0 else float('inf')
            )
            model = list(best_provider.models_used.keys())[0] if best_provider.models_used else "gpt-4.1"
            return best_provider.provider, model, f"Fastest (avg {best_provider.average_generation_time:.1f}s)"
        
        else:  # balance
            # Balance cost, quality, and speed
            # Prefer Enterprise MGA as primary
            if "bayer_mga" in self.provider_stats:
                stats = self.provider_stats["bayer_mga"]
                if stats.success_rate >= 80:
                    return "bayer_mga", "gpt-4.1", "Primary provider with good performance"
            
            # Fall back to best performing alternative
            best_provider = max(
                self.provider_stats.values(),
                key=lambda s: s.success_rate if s.total_generations >= 3 else 0
            )
            model = list(best_provider.models_used.keys())[0] if best_provider.models_used else "gpt-4-turbo"
            return best_provider.provider, model, f"Best success rate ({best_provider.success_rate:.1f}%)"
    
    def get_usage_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Feature #341-342: Get usage summary with token and cost totals.
        """
        filtered = self.generations
        
        if start_date:
            filtered = [g for g in filtered if g.timestamp >= start_date]
        
        if end_date:
            filtered = [g for g in filtered if g.timestamp <= end_date]
        
        total_tokens = sum(
            g.token_usage.total_tokens
            for g in filtered
            if g.token_usage and g.success
        )
        
        total_cost = sum(
            g.cost_estimate.cost_usd
            for g in filtered
            if g.cost_estimate and g.success
        )
        
        total_generations = len(filtered)
        successful = sum(1 for g in filtered if g.success)
        failed = sum(1 for g in filtered if not g.success)
        
        avg_quality = 0.0
        quality_count = 0
        for g in filtered:
            if g.success and g.quality_metrics:
                avg_quality += g.quality_metrics.quality_score
                quality_count += 1
        
        if quality_count > 0:
            avg_quality /= quality_count
        
        return {
            "total_generations": total_generations,
            "successful_generations": successful,
            "failed_generations": failed,
            "success_rate": (successful / total_generations * 100) if total_generations > 0 else 0,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "average_cost_per_generation": total_cost / successful if successful > 0 else 0,
            "average_quality_score": avg_quality,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    
    def cleanup_old_generations(self, days: int = 30) -> int:
        """Remove generations older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(self.generations)
        
        self.generations = [
            g for g in self.generations
            if g.timestamp >= cutoff
        ]
        
        removed = original_count - len(self.generations)
        logger.info(f"Cleaned up {removed} old generations (older than {days} days)")
        return removed


# Feature #348: Generation settings presets
GENERATION_PRESETS = {
    "creative": {
        "temperature": 0.9,
        "max_tokens": 2500,
        "description": "More creative and varied outputs",
    },
    "balanced": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "description": "Balance between creativity and consistency",
    },
    "precise": {
        "temperature": 0.3,
        "max_tokens": 2000,
        "description": "More consistent and predictable outputs",
    },
    "concise": {
        "temperature": 0.5,
        "max_tokens": 1000,
        "description": "Shorter, more focused diagrams",
    },
    "detailed": {
        "temperature": 0.7,
        "max_tokens": 3000,
        "description": "More comprehensive and detailed diagrams",
    },
}


# Feature #350: Prompt templates
PROMPT_TEMPLATES = {
    "architecture": {
        "microservices": "Create a microservices architecture diagram showing {components}. Include API gateway, service mesh, and load balancers.",
        "three_tier": "Create a 3-tier architecture diagram with frontend ({frontend}), backend ({backend}), and database ({database}).",
        "cloud_native": "Design a cloud-native architecture on {cloud_provider} using {services}. Include auto-scaling and high availability.",
        "event_driven": "Create an event-driven architecture using {message_broker} with producers, consumers, and event store.",
        # Feature #351: AWS 3-tier architecture template
        "aws_3tier": "Create a 3-tier architecture on AWS with the following layers: 1) Presentation tier with CloudFront CDN and S3 for static content, 2) Application tier with Application Load Balancer, Auto Scaling Group of EC2 instances running the application in private subnets across multiple availability zones, 3) Data tier with RDS PostgreSQL in Multi-AZ configuration. Include VPC with public and private subnets, NAT Gateway for outbound traffic, Security Groups, and Route 53 for DNS.",
        # Feature #352: Kubernetes deployment template
        "kubernetes": "Create a Kubernetes deployment diagram showing: 1) Ingress controller for external traffic routing, 2) Multiple deployments with pods running containerized applications, 3) Services (ClusterIP, NodePort, LoadBalancer) for service discovery, 4) ConfigMaps and Secrets for configuration, 5) Persistent Volumes for stateful applications, 6) Horizontal Pod Autoscaler for scaling, 7) Network policies for security. Show the relationship between namespaces, pods, services, and ingress.",
    },
    "sequence": {
        "api_flow": "Create a sequence diagram showing the flow for {api_name}. Include {participants} and show authentication, validation, and data flow.",
        "user_journey": "Create a sequence diagram showing user journey for {feature}. Include frontend, backend, database, and external services.",
        "authentication": "Create a sequence diagram for {auth_type} authentication flow. Show all security checks and token exchanges.",
        # Feature #353: OAuth 2.0 flow template
        "oauth2": "Create a detailed sequence diagram for OAuth 2.0 Authorization Code Flow with PKCE showing the complete interaction between: 1) User/Resource Owner, 2) Client Application (web or mobile), 3) Authorization Server, and 4) Resource Server. Include all steps: initial request with code_challenge, user authentication, authorization consent, authorization code generation, token exchange with code_verifier, access token issuance, refresh token usage, and API calls with bearer token. Show all security validations and redirects.",
    },
    "erd": {
        "database": "Create an ERD for {domain} showing entities, relationships, and key fields. Include {entities}.",
        "ecommerce": "Create an ecommerce ERD with products, users, orders, payments, and shipping tables.",
        "saas": "Create a SaaS ERD with tenants, users, subscriptions, features, and usage tracking.",
    },
    "flowchart": {
        "process": "Create a flowchart for the {process_name} process. Include decision points, error handling, and success/failure paths.",
        "algorithm": "Create a flowchart for the {algorithm_name} algorithm showing all steps and conditions.",
        "workflow": "Create a workflow diagram for {workflow_name} with parallel tasks, approvals, and notifications.",
    },
}


def get_prompt_template(category: str, template_name: str, **kwargs) -> Optional[str]:
    """
    Feature #350: Get and format a prompt template.
    
    Args:
        category: Template category (architecture, sequence, erd, flowchart)
        template_name: Specific template name
        **kwargs: Variables to substitute in template
    
    Returns:
        Formatted prompt or None if template not found
    """
    templates = PROMPT_TEMPLATES.get(category, {})
    template = templates.get(template_name)
    
    if not template:
        return None
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing template variable: {e}")
        return None


# Global analytics instance (in production, use Redis or database)
_analytics_instance: Optional[GenerationAnalytics] = None


def get_analytics() -> GenerationAnalytics:
    """Get global analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = GenerationAnalytics()
    return _analytics_instance
