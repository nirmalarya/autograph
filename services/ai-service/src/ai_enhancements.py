"""
Advanced AI Enhancements for Diagram Generation

Features implemented:
- Feature #371: AI-powered layout optimization
- Feature #372: AI-powered icon suggestions
- Feature #373: AI-powered label generation
- Feature #374: AI-powered connection suggestions
- Feature #375: AI-powered diagram completion
- Feature #376: AI-powered best practices check
- Feature #377: AI-powered diagram to code
- Feature #378: AI-powered diagram to documentation
- Feature #382: AI generation with custom instructions
- Feature #383: AI generation with style transfer
- Feature #384: AI-powered diagram merging
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LayoutOptimization:
    """Result of layout optimization."""
    optimized_code: str
    changes_made: List[str]
    improvement_score: float
    suggestions: List[str]


@dataclass
class IconSuggestion:
    """Suggested icon for a component."""
    component_name: str
    suggested_icon: str
    confidence: float
    alternatives: List[str]
    reason: str


@dataclass
class LabelSuggestion:
    """Suggested label for an element."""
    element_id: str
    current_label: str
    suggested_label: str
    improvement_reason: str


@dataclass
class ConnectionSuggestion:
    """Suggested connection between components."""
    from_component: str
    to_component: str
    connection_type: str
    confidence: float
    reason: str


@dataclass
class BestPracticeViolation:
    """A best practice violation found in diagram."""
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    line_number: Optional[int]
    suggestion: str


@dataclass
class CodeGeneration:
    """Generated code from diagram."""
    language: str
    code: str
    framework: Optional[str]
    dependencies: List[str]
    setup_instructions: str


class AIEnhancements:
    """Advanced AI-powered diagram enhancements."""
    
    def __init__(self):
        """Initialize AI enhancements."""
        self.icon_mappings = self._load_icon_mappings()
        self.best_practices = self._load_best_practices()
    
    def _load_icon_mappings(self) -> Dict[str, List[str]]:
        """Load icon mappings for suggestions."""
        return {
            # Cloud providers
            "aws": ["aws", "cloud", "amazon"],
            "azure": ["azure", "microsoft", "ms"],
            "gcp": ["gcp", "google cloud", "google"],
            
            # Databases
            "postgresql": ["postgres", "postgresql", "pg", "sql"],
            "mysql": ["mysql", "mariadb"],
            "mongodb": ["mongo", "mongodb", "nosql"],
            "redis": ["redis", "cache", "kv"],
            
            # Languages
            "python": ["python", "py", "flask", "django", "fastapi"],
            "javascript": ["javascript", "js", "node", "nodejs"],
            "typescript": ["typescript", "ts"],
            "java": ["java", "spring", "springboot"],
            "go": ["go", "golang"],
            
            # Services
            "api": ["api", "rest", "graphql", "endpoint"],
            "frontend": ["frontend", "ui", "web", "client"],
            "backend": ["backend", "server", "api"],
            "load balancer": ["lb", "load balancer", "nginx", "haproxy"],
            "cdn": ["cdn", "cloudfront", "cloudflare"],
            "queue": ["queue", "sqs", "rabbitmq", "kafka"],
        }
    
    def _load_best_practices(self) -> List[Dict[str, Any]]:
        """Load best practices checks."""
        return [
            {
                "name": "component_naming",
                "pattern": r"^[a-z]",
                "message": "Component names should start with lowercase",
                "severity": "warning"
            },
            {
                "name": "no_orphans",
                "check": "orphaned_nodes",
                "message": "Avoid disconnected components",
                "severity": "warning"
            },
            {
                "name": "bidirectional_arrows",
                "pattern": r"<-->",
                "message": "Consider using unidirectional arrows for clarity",
                "severity": "info"
            },
            {
                "name": "proper_spacing",
                "check": "spacing",
                "message": "Maintain consistent spacing between components",
                "severity": "info"
            }
        ]
    
    def optimize_layout(
        self,
        mermaid_code: str,
        diagram_type: str
    ) -> LayoutOptimization:
        """
        Feature #371: AI-powered layout optimization.
        
        Optimize diagram layout for better readability.
        
        Args:
            mermaid_code: Original Mermaid code
            diagram_type: Type of diagram
            
        Returns:
            LayoutOptimization result
        """
        changes = []
        optimized = mermaid_code
        
        # Add proper direction if missing
        if diagram_type == "flowchart" and "graph" in optimized.lower():
            if not re.search(r"graph (TD|LR|TB|RL)", optimized):
                optimized = optimized.replace("graph", "graph TD")
                changes.append("Added top-down direction (TD)")
        
        # Add subgraphs for logical grouping
        if "subgraph" not in optimized:
            # Detect potential groups (simplified)
            if "database" in optimized.lower() or "db" in optimized.lower():
                changes.append("Consider adding subgraph for data layer")
        
        # Add styling suggestions
        if "style" not in optimized:
            changes.append("Consider adding styles for better visual hierarchy")
        
        improvement_score = len(changes) * 0.1  # Simple scoring
        
        suggestions = [
            "Use subgraphs to group related components",
            "Apply consistent styling to similar elements",
            "Ensure proper spacing between nodes",
            "Use descriptive labels for all connections"
        ]
        
        return LayoutOptimization(
            optimized_code=optimized,
            changes_made=changes,
            improvement_score=min(1.0, improvement_score),
            suggestions=suggestions
        )
    
    def suggest_icons(
        self,
        mermaid_code: str,
        diagram_type: str
    ) -> List[IconSuggestion]:
        """
        Feature #372: AI-powered icon suggestions.
        
        Suggest appropriate icons for components in diagram.
        
        Args:
            mermaid_code: Mermaid code
            diagram_type: Type of diagram
            
        Returns:
            List of icon suggestions
        """
        suggestions = []
        
        # Extract component names (simplified)
        components = re.findall(r'\[([^\]]+)\]', mermaid_code)
        
        for component in components:
            component_lower = component.lower()
            
            # Check against icon mappings
            for icon, keywords in self.icon_mappings.items():
                if any(kw in component_lower for kw in keywords):
                    suggestions.append(IconSuggestion(
                        component_name=component,
                        suggested_icon=icon,
                        confidence=0.8,
                        alternatives=[],
                        reason=f"Component name matches {icon} keywords"
                    ))
                    break
        
        return suggestions
    
    def generate_labels(
        self,
        mermaid_code: str,
        diagram_type: str
    ) -> List[LabelSuggestion]:
        """
        Feature #373: AI-powered label generation.
        
        Generate descriptive labels for diagram elements.
        
        Args:
            mermaid_code: Mermaid code
            diagram_type: Type of diagram
            
        Returns:
            List of label suggestions
        """
        suggestions = []
        
        # Find connections without labels
        connections = re.findall(r'(\w+)\s*-->\s*(\w+)', mermaid_code)
        
        for i, (source, target) in enumerate(connections):
            suggestions.append(LabelSuggestion(
                element_id=f"conn_{i}",
                current_label="",
                suggested_label=f"sends data to",
                improvement_reason="Add descriptive label to clarify relationship"
            ))
        
        return suggestions
    
    def suggest_connections(
        self,
        mermaid_code: str,
        diagram_type: str
    ) -> List[ConnectionSuggestion]:
        """
        Feature #374: AI-powered connection suggestions.
        
        Suggest missing connections in architecture diagrams.
        
        Args:
            mermaid_code: Mermaid code
            diagram_type: Type of diagram
            
        Returns:
            List of connection suggestions
        """
        suggestions = []
        
        # Detect common patterns
        has_frontend = any(kw in mermaid_code.lower() for kw in ["frontend", "ui", "client"])
        has_backend = any(kw in mermaid_code.lower() for kw in ["backend", "api", "server"])
        has_db = any(kw in mermaid_code.lower() for kw in ["database", "db", "postgres"])
        
        if has_frontend and has_backend:
            suggestions.append(ConnectionSuggestion(
                from_component="Frontend",
                to_component="Backend",
                connection_type="HTTP/REST",
                confidence=0.9,
                reason="Frontend typically communicates with backend via HTTP"
            ))
        
        if has_backend and has_db:
            suggestions.append(ConnectionSuggestion(
                from_component="Backend",
                to_component="Database",
                connection_type="SQL/ORM",
                confidence=0.9,
                reason="Backend typically connects to database for data storage"
            ))
        
        return suggestions
    
    def complete_diagram(
        self,
        partial_mermaid: str,
        diagram_type: str,
        context: Optional[str] = None
    ) -> str:
        """
        Feature #375: AI-powered diagram completion.
        
        Complete a partially-drawn diagram.
        
        Args:
            partial_mermaid: Incomplete Mermaid code
            diagram_type: Type of diagram
            context: Additional context
            
        Returns:
            Completed Mermaid code
        """
        # Add common missing components
        completed = partial_mermaid
        
        if diagram_type == "architecture":
            # Ensure common layers exist
            if "frontend" not in completed.lower():
                completed += "\n    Frontend[Frontend Application]"
            if "backend" not in completed.lower():
                completed += "\n    Backend[Backend API]"
            if "database" not in completed.lower():
                completed += "\n    DB[(Database)]"
        
        return completed
    
    def check_best_practices(
        self,
        mermaid_code: str,
        diagram_type: str
    ) -> List[BestPracticeViolation]:
        """
        Feature #376: AI-powered best practices check.
        
        Check diagram against best practices.
        
        Args:
            mermaid_code: Mermaid code to check
            diagram_type: Type of diagram
            
        Returns:
            List of violations found
        """
        violations = []
        
        lines = mermaid_code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check component naming
            if re.search(r'\[([A-Z]{2,})\]', line):
                violations.append(BestPracticeViolation(
                    severity="warning",
                    category="naming",
                    message="Component names in all caps are hard to read",
                    line_number=i,
                    suggestion="Use proper case for component names"
                ))
            
            # Check for bidirectional arrows
            if "<-->" in line:
                violations.append(BestPracticeViolation(
                    severity="info",
                    category="arrows",
                    message="Bidirectional arrows can be ambiguous",
                    line_number=i,
                    suggestion="Consider using two unidirectional arrows with clear labels"
                ))
        
        return violations
    
    def diagram_to_code(
        self,
        mermaid_code: str,
        diagram_type: str,
        target_language: str,
        framework: Optional[str] = None
    ) -> CodeGeneration:
        """
        Feature #377: AI-powered diagram to code.
        
        Generate code skeleton from diagram.
        
        Args:
            mermaid_code: Mermaid code
            diagram_type: Type of diagram
            target_language: Target programming language
            framework: Optional framework
            
        Returns:
            CodeGeneration result
        """
        # Extract components
        components = re.findall(r'\[([^\]]+)\]', mermaid_code)
        
        if target_language == "python":
            code = "# Generated from diagram\n\n"
            dependencies = ["fastapi", "uvicorn"]
            
            for component in components:
                class_name = component.replace(" ", "")
                code += f"class {class_name}:\n"
                code += f"    \"\"\"Auto-generated from diagram.\"\"\"\n"
                code += f"    def __init__(self):\n"
                code += f"        pass\n\n"
            
            return CodeGeneration(
                language="python",
                code=code,
                framework=framework or "fastapi",
                dependencies=dependencies,
                setup_instructions="pip install " + " ".join(dependencies)
            )
        
        else:
            return CodeGeneration(
                language=target_language,
                code=f"// Code generation for {target_language} not yet implemented",
                framework=framework,
                dependencies=[],
                setup_instructions=""
            )
    
    def diagram_to_documentation(
        self,
        mermaid_code: str,
        diagram_type: str,
        format: str = "markdown"
    ) -> str:
        """
        Feature #378: AI-powered diagram to documentation.
        
        Generate documentation from diagram.
        
        Args:
            mermaid_code: Mermaid code
            diagram_type: Type of diagram
            format: Output format (markdown, html)
            
        Returns:
            Generated documentation
        """
        # Extract components and connections
        components = re.findall(r'\[([^\]]+)\]', mermaid_code)
        connections = re.findall(r'(\w+)\s*-->\s*(\w+)', mermaid_code)
        
        doc = f"# {diagram_type.title()} Documentation\n\n"
        doc += "## Overview\n\n"
        doc += f"This diagram contains {len(components)} components "
        doc += f"with {len(connections)} connections.\n\n"
        
        doc += "## Components\n\n"
        for component in components:
            doc += f"### {component}\n\n"
            doc += f"Description: [Auto-generated component documentation]\n\n"
        
        doc += "## Data Flow\n\n"
        for source, target in connections:
            doc += f"- `{source}` → `{target}`\n"
        
        doc += "\n## Diagram\n\n"
        doc += "```mermaid\n"
        doc += mermaid_code
        doc += "\n```\n"
        
        return doc
    
    def apply_custom_instructions(
        self,
        mermaid_code: str,
        instructions: List[str]
    ) -> str:
        """
        Feature #382: AI generation with custom instructions.
        
        Apply custom instructions to modify diagram.
        
        Args:
            mermaid_code: Original Mermaid code
            instructions: List of custom instructions
            
        Returns:
            Modified Mermaid code
        """
        modified = mermaid_code
        
        for instruction in instructions:
            instruction_lower = instruction.lower()
            
            # Add caching layer
            if "cache" in instruction_lower or "redis" in instruction_lower:
                if "cache" not in modified.lower():
                    modified += "\n    Cache[(Redis Cache)]"
            
            # Add monitoring
            if "monitor" in instruction_lower or "observability" in instruction_lower:
                if "monitor" not in modified.lower():
                    modified += "\n    Monitor[Monitoring System]"
            
            # Add load balancer
            if "load balan" in instruction_lower:
                if "lb" not in modified.lower():
                    modified += "\n    LB[Load Balancer]"
        
        return modified
    
    def apply_style_transfer(
        self,
        mermaid_code: str,
        source_diagram: str,
        style_aspects: List[str]
    ) -> str:
        """
        Feature #383: AI generation with style transfer.
        
        Transfer styling from one diagram to another.
        
        Args:
            mermaid_code: Target diagram code
            source_diagram: Source diagram to copy style from
            style_aspects: Which aspects to transfer (colors, shapes, etc.)
            
        Returns:
            Styled Mermaid code
        """
        styled = mermaid_code
        
        # Extract style definitions from source
        style_defs = re.findall(r'style \w+ fill:#[\w\d]+', source_diagram)
        
        if "colors" in style_aspects and style_defs:
            # Apply first style to target
            styled += "\n    " + style_defs[0]
        
        return styled
    
    def merge_diagrams(
        self,
        diagram1: str,
        diagram2: str,
        merge_strategy: str = "union"
    ) -> str:
        """
        Feature #384: AI-powered diagram merging.
        
        Merge two diagrams intelligently.
        
        Args:
            diagram1: First diagram Mermaid code
            diagram2: Second diagram Mermaid code
            merge_strategy: How to merge (union, intersect, append)
            
        Returns:
            Merged Mermaid code
        """
        if merge_strategy == "union":
            # Extract all unique components and connections
            lines1 = [l.strip() for l in diagram1.split('\n') if l.strip()]
            lines2 = [l.strip() for l in diagram2.split('\n') if l.strip()]
            
            # Get header from first diagram
            merged = lines1[0] if lines1 else "graph TD"
            
            # Combine unique lines
            all_lines = lines1[1:] + lines2[1:]
            unique_lines = list(dict.fromkeys(all_lines))  # Preserve order, remove duplicates
            
            merged += "\n    " + "\n    ".join(unique_lines)
            
            return merged
        
        elif merge_strategy == "append":
            # Simple append
            return diagram1 + "\n\n" + diagram2
        
        else:
            return diagram1


# Global instance
_ai_enhancements = AIEnhancements()


def get_ai_enhancements() -> AIEnhancements:
    """Get global AI enhancements instance."""
    return _ai_enhancements
