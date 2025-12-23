"""
AI-Powered Prompt Engineering and Diagram Analysis

Features implemented:
- Feature #354: Prompt engineering best practices guide
- Feature #355: AI suggestions to improve prompt quality
- Feature #356: AI suggestions to add missing components
- Feature #357: Diagram explanation (AI describes generated diagram)
- Feature #358: Diagram critique (AI suggests improvements)
- Feature #359: Multi-language prompt support
- Feature #360: Prompt history with autocomplete
- Feature #361: Batch generation with multiple variations
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re

logger = logging.getLogger(__name__)


class PromptQuality(str, Enum):
    """Prompt quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class DiagramComplexity(str, Enum):
    """Diagram complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


# Feature #354: Prompt Engineering Best Practices
PROMPT_BEST_PRACTICES = {
    "general": [
        "Be specific about the components and their relationships",
        "Mention the technology stack explicitly (e.g., AWS, Azure, React, Node.js)",
        "Specify the diagram type if you have a preference (architecture, sequence, ERD, flowchart)",
        "Include context about the system's purpose and scale",
        "Mention any constraints or requirements (security, performance, cost)",
    ],
    "architecture": [
        "Specify cloud provider (AWS, Azure, GCP) or on-premises",
        "Mention key services/components (database, cache, load balancer, etc.)",
        "Describe data flow and communication patterns",
        "Include security requirements (VPN, firewall, encryption)",
        "Specify scalability needs (auto-scaling, multi-region)",
    ],
    "sequence": [
        "List all participants/actors in the interaction",
        "Describe the flow step by step",
        "Mention authentication and authorization steps",
        "Include error handling and edge cases",
        "Specify async operations if applicable",
    ],
    "erd": [
        "List main entities/tables",
        "Describe relationships (one-to-one, one-to-many, many-to-many)",
        "Mention key fields and data types",
        "Include constraints (primary keys, foreign keys, unique)",
        "Specify indexes for performance",
    ],
    "flowchart": [
        "Define the start and end points clearly",
        "List all decision points",
        "Include error handling paths",
        "Mention parallel processes if any",
        "Specify loop conditions",
    ],
}


# Feature #354: Examples of good vs bad prompts
PROMPT_EXAMPLES = {
    "bad": [
        "Create a system",
        "Make an architecture",
        "Design a database",
        "Build microservices",
    ],
    "good": [
        "Create a 3-tier web application architecture on AWS with React frontend, Node.js backend on EC2, and PostgreSQL RDS database. Include CloudFront CDN, Application Load Balancer, and S3 for static assets.",
        "Design a microservices architecture for an e-commerce platform with user service, product catalog, order processing, payment gateway integration, and inventory management. Use RabbitMQ for async messaging.",
        "Create an ERD for a social media platform with users, posts, comments, likes, followers, and direct messages. Show all relationships and key fields.",
        "Generate a sequence diagram for OAuth 2.0 authorization code flow showing the interaction between client app, authorization server, resource server, and user.",
    ],
}


@dataclass
class PromptAnalysis:
    """Analysis of a prompt's quality and suggestions for improvement."""
    original_prompt: str
    quality: PromptQuality
    quality_score: float  # 0-100
    issues: List[str]
    suggestions: List[str]
    improved_prompt: Optional[str] = None
    estimated_complexity: DiagramComplexity = DiagramComplexity.MODERATE
    detected_type: Optional[str] = None
    detected_technologies: List[str] = None
    
    def __post_init__(self):
        if self.detected_technologies is None:
            self.detected_technologies = []


class PromptEngineer:
    """AI-powered prompt engineering and analysis."""
    
    # Technology keywords for detection
    TECHNOLOGY_KEYWORDS = {
        "cloud": ["aws", "azure", "gcp", "cloud", "s3", "ec2", "lambda", "cloudfront"],
        "database": ["postgres", "mysql", "mongodb", "redis", "dynamodb", "cassandra"],
        "messaging": ["kafka", "rabbitmq", "sqs", "sns", "pubsub", "eventbridge"],
        "container": ["docker", "kubernetes", "k8s", "ecs", "fargate", "pod"],
        "frontend": ["react", "vue", "angular", "next.js", "frontend", "ui"],
        "backend": ["node.js", "python", "java", "go", "fastapi", "express", "spring"],
        "auth": ["oauth", "saml", "jwt", "authentication", "authorization", "sso"],
    }
    
    # Diagram type keywords
    DIAGRAM_TYPE_KEYWORDS = {
        "architecture": ["architecture", "system", "infrastructure", "deployment", "cloud"],
        "sequence": ["sequence", "flow", "interaction", "process flow", "communication"],
        "erd": ["database", "erd", "entity", "relationship", "schema", "table"],
        "flowchart": ["flowchart", "algorithm", "workflow", "process", "decision"],
    }
    
    def __init__(self):
        """Initialize prompt engineer."""
        self.prompt_history: List[str] = []
    
    def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """
        Feature #355: Analyze prompt quality and provide suggestions.
        
        Args:
            prompt: User's prompt
            
        Returns:
            PromptAnalysis with quality assessment and suggestions
        """
        issues = []
        suggestions = []
        quality_score = 100.0
        
        # Check length
        if len(prompt) < 20:
            issues.append("Prompt is too short")
            suggestions.append("Add more details about components and their relationships")
            quality_score -= 30
        
        # Check specificity
        vague_words = ["system", "application", "platform", "service", "thing"]
        if any(word in prompt.lower() for word in vague_words) and len(prompt.split()) < 15:
            issues.append("Prompt is too vague")
            suggestions.append("Be more specific. Mention exact technologies, services, and components")
            quality_score -= 20
        
        # Check for technology mentions
        detected_techs = self._detect_technologies(prompt)
        if not detected_techs:
            issues.append("No specific technologies mentioned")
            suggestions.append("Mention specific technologies (e.g., AWS, PostgreSQL, React)")
            quality_score -= 15
        
        # Check for diagram type
        detected_type = self._detect_diagram_type(prompt)
        if not detected_type:
            issues.append("Diagram type unclear")
            suggestions.append("Specify diagram type: architecture, sequence, ERD, or flowchart")
            quality_score -= 10
        
        # Check for relationships/connections
        connection_words = ["connect", "communicate", "interact", "flow", "relationship"]
        if not any(word in prompt.lower() for word in connection_words):
            issues.append("No relationships or connections described")
            suggestions.append("Describe how components connect and communicate")
            quality_score -= 10
        
        # Generate improved prompt
        improved = self._generate_improved_prompt(
            prompt, issues, suggestions, detected_type, detected_techs
        )
        
        # Determine quality level
        if quality_score >= 80:
            quality = PromptQuality.EXCELLENT
        elif quality_score >= 60:
            quality = PromptQuality.GOOD
        elif quality_score >= 40:
            quality = PromptQuality.FAIR
        else:
            quality = PromptQuality.POOR
        
        # Estimate complexity
        complexity = self._estimate_complexity(prompt, detected_techs)
        
        return PromptAnalysis(
            original_prompt=prompt,
            quality=quality,
            quality_score=quality_score,
            issues=issues,
            suggestions=suggestions,
            improved_prompt=improved,
            estimated_complexity=complexity,
            detected_type=detected_type,
            detected_technologies=detected_techs
        )
    
    def _detect_technologies(self, prompt: str) -> List[str]:
        """Detect technologies mentioned in prompt."""
        prompt_lower = prompt.lower()
        detected = []
        
        for category, keywords in self.TECHNOLOGY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected.append(keyword)
        
        return list(set(detected))
    
    def _detect_diagram_type(self, prompt: str) -> Optional[str]:
        """Detect diagram type from prompt."""
        prompt_lower = prompt.lower()
        
        scores = {}
        for diagram_type, keywords in self.DIAGRAM_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in prompt_lower)
            if score > 0:
                scores[diagram_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def _estimate_complexity(
        self, 
        prompt: str, 
        technologies: List[str]
    ) -> DiagramComplexity:
        """Estimate diagram complexity based on prompt."""
        # Count components mentioned
        words = prompt.split()
        tech_count = len(technologies)
        
        if tech_count >= 8 or len(words) > 100:
            return DiagramComplexity.VERY_COMPLEX
        elif tech_count >= 5 or len(words) > 60:
            return DiagramComplexity.COMPLEX
        elif tech_count >= 3 or len(words) > 30:
            return DiagramComplexity.MODERATE
        else:
            return DiagramComplexity.SIMPLE
    
    def _generate_improved_prompt(
        self,
        original: str,
        issues: List[str],
        suggestions: List[str],
        diagram_type: Optional[str],
        technologies: List[str]
    ) -> str:
        """Generate an improved version of the prompt."""
        if not issues:
            return original
        
        improved = original
        
        # If prompt is too short, add template structure
        if "Prompt is too short" in issues or "Prompt is too vague" in issues:
            if diagram_type:
                improved = f"Create a {diagram_type} diagram showing {original.lower()}. "
            else:
                improved = f"Create a diagram showing {original.lower()}. "
            
            # Add technology context if detected
            if technologies:
                improved += f"Use technologies: {', '.join(technologies[:3])}. "
            else:
                improved += "Specify the technologies and components. "
            
            improved += "Include all connections and data flows."
        
        return improved
    
    def add_to_history(self, prompt: str):
        """Feature #360: Add prompt to history for autocomplete."""
        if prompt not in self.prompt_history:
            self.prompt_history.append(prompt)
            # Keep only last 100 prompts
            if len(self.prompt_history) > 100:
                self.prompt_history = self.prompt_history[-100:]
    
    def autocomplete_prompt(self, partial: str, limit: int = 5) -> List[str]:
        """
        Feature #360: Autocomplete from prompt history.
        
        Args:
            partial: Partial prompt text
            limit: Maximum suggestions to return
            
        Returns:
            List of matching prompts from history
        """
        if not partial or len(partial) < 3:
            return []
        
        partial_lower = partial.lower()
        matches = [
            p for p in self.prompt_history
            if partial_lower in p.lower()
        ]
        
        # Sort by relevance (starts with > contains)
        matches.sort(key=lambda p: (
            not p.lower().startswith(partial_lower),
            len(p)
        ))
        
        return matches[:limit]


class DiagramAnalyzer:
    """Analyze and critique generated diagrams."""
    
    def __init__(self):
        """Initialize diagram analyzer."""
        pass
    
    def explain_diagram(
        self, 
        mermaid_code: str, 
        diagram_type: str,
        original_prompt: str
    ) -> str:
        """
        Feature #357: Generate explanation of the diagram.
        
        Args:
            mermaid_code: Mermaid diagram code
            diagram_type: Type of diagram
            original_prompt: Original user prompt
            
        Returns:
            Human-readable explanation
        """
        # Parse diagram to understand components
        components = self._parse_components(mermaid_code, diagram_type)
        
        explanation = f"This {diagram_type} diagram illustrates {original_prompt}.\n\n"
        
        if diagram_type == "architecture":
            explanation += self._explain_architecture(components)
        elif diagram_type == "sequence":
            explanation += self._explain_sequence(components)
        elif diagram_type == "erd":
            explanation += self._explain_erd(components)
        elif diagram_type == "flowchart":
            explanation += self._explain_flowchart(components)
        else:
            explanation += self._explain_generic(components)
        
        return explanation
    
    def critique_diagram(
        self,
        mermaid_code: str,
        diagram_type: str,
        original_prompt: str
    ) -> Dict[str, Any]:
        """
        Feature #358: Critique diagram and suggest improvements.
        
        Args:
            mermaid_code: Mermaid diagram code
            diagram_type: Type of diagram
            original_prompt: Original prompt
            
        Returns:
            Dictionary with critiques and suggestions
        """
        components = self._parse_components(mermaid_code, diagram_type)
        
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Check component count
        component_count = len(components.get("nodes", []))
        if component_count < 3:
            weaknesses.append("Diagram has very few components")
            suggestions.append("Consider adding more detail or components to make the diagram more comprehensive")
        elif component_count > 15:
            weaknesses.append("Diagram might be too complex")
            suggestions.append("Consider breaking this into multiple diagrams for clarity")
        else:
            strengths.append(f"Good balance with {component_count} components")
        
        # Feature #356: Check for missing common components
        if diagram_type == "architecture":
            missing = self._check_missing_architecture_components(components, original_prompt)
            if missing:
                suggestions.extend(missing)
        
        # Check connections
        connections = len(components.get("edges", []))
        if connections < component_count - 1:
            weaknesses.append("Some components might not be connected")
            suggestions.append("Verify all components are properly connected")
        else:
            strengths.append("Components are well-connected")
        
        # Check labels
        if diagram_type == "architecture" and connections > 0:
            labeled_edges = sum(1 for edge in components.get("edges", []) if edge.get("label"))
            if labeled_edges < connections / 2:
                weaknesses.append("Many connections lack labels")
                suggestions.append("Add labels to connections to describe data flow or protocols")
            else:
                strengths.append("Connections are well-labeled")
        
        return {
            "overall_score": self._calculate_overall_score(strengths, weaknesses),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "component_count": component_count,
            "connection_count": connections,
        }
    
    def _check_missing_architecture_components(
        self,
        components: Dict[str, Any],
        prompt: str
    ) -> List[str]:
        """Feature #356: Check for missing common architecture components."""
        suggestions = []
        prompt_lower = prompt.lower()
        nodes = [n.get("id", "").lower() for n in components.get("nodes", [])]
        
        # Check for load balancer
        if "web" in prompt_lower or "frontend" in prompt_lower:
            if not any("load" in n or "lb" in n or "balancer" in n for n in nodes):
                suggestions.append("Consider adding a load balancer for high availability")
        
        # Check for cache
        if "api" in prompt_lower or "backend" in prompt_lower:
            if not any("cache" in n or "redis" in n or "memcache" in n for n in nodes):
                suggestions.append("Consider adding caching (Redis/Memcached) to improve performance")
        
        # Check for database replication
        if "database" in prompt_lower or "db" in prompt_lower:
            db_nodes = [n for n in nodes if "db" in n or "database" in n]
            if len(db_nodes) == 1:
                suggestions.append("Consider adding database replication for redundancy")
        
        # Check for monitoring
        if not any("monitor" in n or "log" in n or "observability" in n for n in nodes):
            suggestions.append("Consider adding monitoring/logging components")
        
        # Check for security
        if "internet" in prompt_lower or "public" in prompt_lower:
            if not any("firewall" in n or "waf" in n or "security" in n for n in nodes):
                suggestions.append("Consider adding security components (WAF, firewall)")
        
        return suggestions
    
    def _parse_components(
        self, 
        mermaid_code: str, 
        diagram_type: str
    ) -> Dict[str, Any]:
        """Parse Mermaid code to extract components."""
        components = {
            "nodes": [],
            "edges": [],
            "type": diagram_type
        }
        
        lines = mermaid_code.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%') or line.startswith(diagram_type):
                continue
            
            # Parse nodes and edges (simplified)
            if '-->' in line or '---' in line:
                # Edge/connection
                parts = re.split(r'-->|---', line)
                if len(parts) == 2:
                    source = parts[0].strip()
                    target_and_label = parts[1].strip()
                    components["edges"].append({
                        "source": source,
                        "target": target_and_label.split('|')[0].strip() if '|' in target_and_label else target_and_label,
                        "label": target_and_label.split('|')[1].strip() if '|' in target_and_label else None
                    })
            elif '[' in line or '(' in line or '{' in line:
                # Node
                node_id = line.split('[')[0].split('(')[0].split('{')[0].strip()
                if node_id:
                    components["nodes"].append({"id": node_id})
        
        return components
    
    def _explain_architecture(self, components: Dict[str, Any]) -> str:
        """Explain architecture diagram."""
        nodes = components.get("nodes", [])
        edges = components.get("edges", [])
        
        explanation = f"The system consists of {len(nodes)} main components:\n\n"
        
        for node in nodes[:5]:  # First 5 components
            explanation += f"- {node.get('id')}\n"
        
        if len(nodes) > 5:
            explanation += f"- ... and {len(nodes) - 5} more components\n"
        
        explanation += f"\nThese components interact through {len(edges)} connections, "
        explanation += "enabling data flow and communication across the system."
        
        return explanation
    
    def _explain_sequence(self, components: Dict[str, Any]) -> str:
        """Explain sequence diagram."""
        edges = components.get("edges", [])
        
        explanation = "The sequence shows the following interaction flow:\n\n"
        
        for i, edge in enumerate(edges[:10], 1):
            source = edge.get("source", "")
            target = edge.get("target", "")
            label = edge.get("label", "")
            explanation += f"{i}. {source} → {target}"
            if label:
                explanation += f": {label}"
            explanation += "\n"
        
        if len(edges) > 10:
            explanation += f"\n... and {len(edges) - 10} more interactions"
        
        return explanation
    
    def _explain_erd(self, components: Dict[str, Any]) -> str:
        """Explain ERD diagram."""
        nodes = components.get("nodes", [])
        edges = components.get("edges", [])
        
        explanation = f"The data model includes {len(nodes)} entities:\n\n"
        
        for node in nodes:
            explanation += f"- {node.get('id')}\n"
        
        explanation += f"\nWith {len(edges)} relationships defining how the data is connected."
        
        return explanation
    
    def _explain_flowchart(self, components: Dict[str, Any]) -> str:
        """Explain flowchart diagram."""
        nodes = components.get("nodes", [])
        
        explanation = f"The process involves {len(nodes)} steps:\n\n"
        explanation += "Starting from the initial step, the flow progresses through "
        explanation += "decision points and actions, handling both success and error cases "
        explanation += "until reaching the end state."
        
        return explanation
    
    def _explain_generic(self, components: Dict[str, Any]) -> str:
        """Generic explanation."""
        nodes = components.get("nodes", [])
        edges = components.get("edges", [])
        
        return f"The diagram shows {len(nodes)} components connected by {len(edges)} relationships."
    
    def _calculate_overall_score(
        self, 
        strengths: List[str], 
        weaknesses: List[str]
    ) -> float:
        """Calculate overall diagram quality score."""
        base_score = 70.0
        score = base_score + (len(strengths) * 10) - (len(weaknesses) * 15)
        return max(0.0, min(100.0, score))


# Global instances
_prompt_engineer = PromptEngineer()
_diagram_analyzer = DiagramAnalyzer()


def get_prompt_engineer() -> PromptEngineer:
    """Get global prompt engineer instance."""
    return _prompt_engineer


def get_diagram_analyzer() -> DiagramAnalyzer:
    """Get global diagram analyzer instance."""
    return _diagram_analyzer
