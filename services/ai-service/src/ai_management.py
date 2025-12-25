"""
AI Generation Analytics and Management

Features implemented:
- Feature #369: Export AI prompt with diagram
- Feature #370: Import diagram with AI regeneration
- Feature #379: AI provider usage analytics
- Feature #380: AI generation quality feedback
- Feature #381: AI model comparison tool
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class DiagramExport:
    """Exported diagram with AI metadata."""
    mermaid_code: str
    diagram_type: str
    original_prompt: str
    provider: str
    model: str
    tokens_used: int
    quality_score: Optional[float]
    generation_timestamp: str
    export_timestamp: str
    metadata: Dict[str, Any]


@dataclass
class DiagramImport:
    """Imported diagram with regeneration capability."""
    mermaid_code: str
    original_prompt: str
    can_regenerate: bool
    provider_used: str
    model_used: str
    import_timestamp: str


@dataclass
class ProviderUsage:
    """Usage statistics for an AI provider - Feature #379."""
    provider: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    average_latency: float
    success_rate: float
    last_used: Optional[float]
    total_cost: float = 0.0
    average_quality: float = 0.0


@dataclass
class QualityFeedback:
    """User feedback on generation quality."""
    generation_id: str
    rating: int  # 1-5
    feedback_text: Optional[str]
    issues: List[str]
    timestamp: float


@dataclass
class ModelComparison:
    """Comparison between different models."""
    prompt: str
    results: List[Dict[str, Any]]
    winner: Optional[str]
    comparison_metrics: Dict[str, Any]


class AIManagement:
    """Management and analytics for AI generation."""
    
    def __init__(self):
        """Initialize AI management."""
        self.provider_stats: Dict[str, Dict[str, Any]] = {}
        self.quality_feedback: List[QualityFeedback] = []
        self.generation_history: List[Dict[str, Any]] = []
    
    def export_diagram_with_prompt(
        self,
        mermaid_code: str,
        diagram_type: str,
        original_prompt: str,
        provider: str,
        model: str,
        tokens_used: int,
        quality_score: Optional[float] = None,
        generation_timestamp: Optional[str] = None
    ) -> DiagramExport:
        """
        Feature #369: Export diagram with AI prompt and metadata.
        
        Args:
            mermaid_code: Generated Mermaid code
            diagram_type: Type of diagram
            original_prompt: Original user prompt
            provider: AI provider used
            model: AI model used
            tokens_used: Token count
            quality_score: Quality score if available
            generation_timestamp: When it was generated
            
        Returns:
            DiagramExport object
        """
        export = DiagramExport(
            mermaid_code=mermaid_code,
            diagram_type=diagram_type,
            original_prompt=original_prompt,
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            quality_score=quality_score,
            generation_timestamp=generation_timestamp or datetime.utcnow().isoformat(),
            export_timestamp=datetime.utcnow().isoformat(),
            metadata={
                "version": "1.0",
                "platform": "AutoGraph v3",
                "can_regenerate": True
            }
        )
        
        logger.info(
            f"Exported diagram with prompt: {diagram_type}, "
            f"provider={provider}, tokens={tokens_used}"
        )
        
        return export
    
    def import_diagram_with_regeneration(
        self,
        export_data: Dict[str, Any]
    ) -> DiagramImport:
        """
        Feature #370: Import diagram with regeneration capability.
        
        Args:
            export_data: Exported diagram data
            
        Returns:
            DiagramImport object
        """
        imported = DiagramImport(
            mermaid_code=export_data.get("mermaid_code", ""),
            original_prompt=export_data.get("original_prompt", ""),
            can_regenerate=export_data.get("metadata", {}).get("can_regenerate", False),
            provider_used=export_data.get("provider", "unknown"),
            model_used=export_data.get("model", "unknown"),
            import_timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Imported diagram: can_regenerate={imported.can_regenerate}, "
            f"provider={imported.provider_used}"
        )
        
        return imported
    
    def track_provider_usage(
        self,
        provider: str,
        success: bool,
        tokens: int,
        latency: float,
        cost: float = 0.0,
        quality: Optional[float] = None
    ):
        """
        Feature #379: Track provider usage for analytics.

        Args:
            provider: Provider name
            success: Whether request was successful
            tokens: Tokens used
            latency: Request latency in seconds
            cost: Estimated cost in USD
            quality: Quality score (0-100) if available
        """
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "total_latency": 0.0,
                "total_cost": 0.0,
                "total_quality": 0.0,
                "quality_count": 0,
                "last_used": None
            }

        stats = self.provider_stats[provider]
        stats["total_requests"] += 1

        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1

        stats["total_tokens"] += tokens
        stats["total_latency"] += latency
        stats["total_cost"] += cost

        if quality is not None:
            stats["total_quality"] += quality
            stats["quality_count"] += 1

        stats["last_used"] = time.time()
    
    def get_provider_usage_analytics(self) -> List[ProviderUsage]:
        """
        Feature #379: Get provider usage analytics.
        
        Returns:
            List of ProviderUsage objects
        """
        analytics = []
        
        for provider, stats in self.provider_stats.items():
            total = stats["total_requests"]
            if total == 0:
                continue
            
            avg_quality = 0.0
            if stats["quality_count"] > 0:
                avg_quality = stats["total_quality"] / stats["quality_count"]

            analytics.append(ProviderUsage(
                provider=provider,
                total_requests=total,
                successful_requests=stats["successful_requests"],
                failed_requests=stats["failed_requests"],
                total_tokens=stats["total_tokens"],
                average_latency=stats["total_latency"] / total,
                success_rate=stats["successful_requests"] / total,
                last_used=stats["last_used"],
                total_cost=stats["total_cost"],
                average_quality=avg_quality
            ))
        
        return sorted(analytics, key=lambda x: x.total_requests, reverse=True)
    
    def submit_quality_feedback(
        self,
        generation_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        issues: Optional[List[str]] = None
    ) -> QualityFeedback:
        """
        Feature #380: Submit quality feedback for generation.
        
        Args:
            generation_id: ID of the generation
            rating: Rating from 1-5
            feedback_text: Optional feedback text
            issues: List of issues found
            
        Returns:
            QualityFeedback object
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        feedback = QualityFeedback(
            generation_id=generation_id,
            rating=rating,
            feedback_text=feedback_text,
            issues=issues or [],
            timestamp=time.time()
        )
        
        self.quality_feedback.append(feedback)
        
        logger.info(
            f"Quality feedback submitted: generation={generation_id}, "
            f"rating={rating}/5"
        )
        
        return feedback
    
    def get_quality_feedback_summary(self) -> Dict[str, Any]:
        """
        Feature #380: Get summary of quality feedback.
        
        Returns:
            Summary statistics
        """
        if not self.quality_feedback:
            return {
                "total_feedback": 0,
                "average_rating": 0.0,
                "rating_distribution": {},
                "common_issues": []
            }
        
        ratings = [f.rating for f in self.quality_feedback]
        all_issues = [issue for f in self.quality_feedback for issue in f.issues]
        
        # Count issue frequency
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return {
            "total_feedback": len(self.quality_feedback),
            "average_rating": sum(ratings) / len(ratings),
            "rating_distribution": {
                rating: ratings.count(rating)
                for rating in range(1, 6)
            },
            "common_issues": sorted(
                issue_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def compare_models(
        self,
        prompt: str,
        provider_models: List[Dict[str, str]],
        results: List[Dict[str, Any]]
    ) -> ModelComparison:
        """
        Feature #381: Compare different AI models.
        
        Args:
            prompt: The prompt used
            provider_models: List of provider/model combinations
            results: Results from each model
            
        Returns:
            ModelComparison object
        """
        # Calculate comparison metrics
        metrics = {
            "quality_scores": {},
            "token_usage": {},
            "latency": {},
            "complexity": {}
        }
        
        for i, result in enumerate(results):
            model_key = f"{provider_models[i]['provider']}:{provider_models[i]['model']}"
            
            metrics["quality_scores"][model_key] = result.get("quality_score", 0)
            metrics["token_usage"][model_key] = result.get("tokens_used", 0)
            metrics["latency"][model_key] = result.get("latency", 0)
            
            # Calculate complexity (number of components + connections)
            code = result.get("mermaid_code", "")
            complexity = code.count("[") + code.count("-->")
            metrics["complexity"][model_key] = complexity
        
        # Determine winner (highest quality score)
        winner = None
        if metrics["quality_scores"]:
            winner = max(metrics["quality_scores"], key=metrics["quality_scores"].get)
        
        comparison = ModelComparison(
            prompt=prompt,
            results=results,
            winner=winner,
            comparison_metrics=metrics
        )
        
        logger.info(
            f"Model comparison complete: {len(results)} models, "
            f"winner={winner}"
        )
        
        return comparison
    
    def get_comparison_recommendations(
        self,
        comparison: ModelComparison
    ) -> Dict[str, Any]:
        """
        Get recommendations based on model comparison.
        
        Args:
            comparison: ModelComparison object
            
        Returns:
            Recommendations dictionary
        """
        recommendations = {
            "best_quality": None,
            "most_efficient": None,
            "fastest": None,
            "most_detailed": None
        }
        
        metrics = comparison.comparison_metrics
        
        if metrics["quality_scores"]:
            recommendations["best_quality"] = max(
                metrics["quality_scores"],
                key=metrics["quality_scores"].get
            )
        
        if metrics["token_usage"]:
            recommendations["most_efficient"] = min(
                metrics["token_usage"],
                key=metrics["token_usage"].get
            )
        
        if metrics["latency"]:
            recommendations["fastest"] = min(
                metrics["latency"],
                key=metrics["latency"].get
            )
        
        if metrics["complexity"]:
            recommendations["most_detailed"] = max(
                metrics["complexity"],
                key=metrics["complexity"].get
            )
        
        return recommendations
    
    def export_to_json(self, export: DiagramExport) -> str:
        """
        Export diagram to JSON format.
        
        Args:
            export: DiagramExport object
            
        Returns:
            JSON string
        """
        return json.dumps(asdict(export), indent=2)
    
    def import_from_json(self, json_str: str) -> DiagramImport:
        """
        Import diagram from JSON format.
        
        Args:
            json_str: JSON string
            
        Returns:
            DiagramImport object
        """
        data = json.loads(json_str)
        return self.import_diagram_with_regeneration(data)
    
    def get_generation_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent generation history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of generation records
        """
        return self.generation_history[-limit:]
    
    def add_to_history(
        self,
        prompt: str,
        provider: str,
        model: str,
        diagram_type: str,
        success: bool,
        tokens: int
    ):
        """
        Add generation to history.
        
        Args:
            prompt: User prompt
            provider: AI provider
            model: AI model
            diagram_type: Type of diagram
            success: Whether generation succeeded
            tokens: Tokens used
        """
        self.generation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt[:100],  # Truncate for storage
            "provider": provider,
            "model": model,
            "diagram_type": diagram_type,
            "success": success,
            "tokens": tokens
        })
        
        # Keep only last 1000 entries
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-1000:]


# Global instance
_ai_management = AIManagement()


def get_ai_management() -> AIManagement:
    """Get global AI management instance."""
    return _ai_management
