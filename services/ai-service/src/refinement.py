"""
Iterative refinement and context awareness for AI diagram generation.

Features:
- #332: Iterative refinement: 'Add caching layer'
- #333: Iterative refinement: 'Make database bigger'
- #334: Iterative refinement: 'Change colors to blue'
- #335: Context awareness: remember previous diagrams in session
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class DiagramContext:
    """Context for a diagram generation session."""
    diagram_id: str
    mermaid_code: str
    prompt: str
    timestamp: datetime
    diagram_type: str
    provider: str
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionContext:
    """
    Manages context across multiple diagram generations in a session.
    
    Feature #335: Context awareness - remember previous diagrams
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.diagrams: List[DiagramContext] = []
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
    
    def add_diagram(
        self,
        diagram_id: str,
        mermaid_code: str,
        prompt: str,
        diagram_type: str,
        provider: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a diagram to session context."""
        context = DiagramContext(
            diagram_id=diagram_id,
            mermaid_code=mermaid_code,
            prompt=prompt,
            timestamp=datetime.utcnow(),
            diagram_type=diagram_type,
            provider=provider,
            model=model,
            metadata=metadata or {}
        )
        self.diagrams.append(context)
        self.last_accessed = datetime.utcnow()
        
        logger.info(
            f"Added diagram {diagram_id} to session {self.session_id}. "
            f"Total diagrams: {len(self.diagrams)}"
        )
    
    def get_recent_diagrams(self, limit: int = 5) -> List[DiagramContext]:
        """Get most recent diagrams from session."""
        return self.diagrams[-limit:] if self.diagrams else []
    
    def get_diagram_by_id(self, diagram_id: str) -> Optional[DiagramContext]:
        """Get specific diagram from session."""
        for diagram in self.diagrams:
            if diagram.diagram_id == diagram_id:
                return diagram
        return None
    
    def get_context_summary(self) -> str:
        """Get a summary of session context for AI prompt enhancement."""
        if not self.diagrams:
            return ""
        
        recent = self.get_recent_diagrams(3)
        summary_parts = [
            f"Session context: {len(self.diagrams)} diagrams created."
        ]
        
        for i, diagram in enumerate(recent, 1):
            summary_parts.append(
                f"{i}. {diagram.diagram_type} diagram: {diagram.prompt[:50]}..."
            )
        
        return "\n".join(summary_parts)


class SessionContextManager:
    """
    Global session context manager.
    
    Manages multiple user sessions with context.
    """
    
    _instance = None
    _sessions: Dict[str, SessionContext] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_session(cls, session_id: str) -> SessionContext:
        """Get or create session context."""
        if session_id not in cls._sessions:
            cls._sessions[session_id] = SessionContext(session_id)
            logger.info(f"Created new session context: {session_id}")
        else:
            cls._sessions[session_id].last_accessed = datetime.utcnow()
        
        return cls._sessions[session_id]
    
    @classmethod
    def cleanup_old_sessions(cls, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours."""
        now = datetime.utcnow()
        to_remove = []
        
        for session_id, session in cls._sessions.items():
            age = (now - session.last_accessed).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del cls._sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")


class IterativeRefinement:
    """
    Iterative refinement system for diagrams.
    
    Features:
    - #332: 'Add caching layer'
    - #333: 'Make database bigger'
    - #334: 'Change colors to blue'
    """
    
    # Refinement patterns and instructions
    REFINEMENT_PATTERNS = {
        # Adding components
        r"add\s+(\w+)": {
            "type": "add_component",
            "instruction": "Add a new {component} to the diagram with appropriate connections"
        },
        r"include\s+(\w+)": {
            "type": "add_component",
            "instruction": "Include a {component} component in the diagram"
        },
        
        # Modifying size/emphasis
        r"make\s+(\w+)\s+(bigger|larger|smaller)": {
            "type": "modify_size",
            "instruction": "Modify the {component} to appear {size} in the diagram"
        },
        r"emphasize\s+(\w+)": {
            "type": "modify_emphasis",
            "instruction": "Emphasize the {component} in the diagram"
        },
        
        # Changing style/appearance
        r"change\s+color[s]?\s+to\s+(\w+)": {
            "type": "change_color",
            "instruction": "Change the color scheme to {color}"
        },
        r"use\s+(\w+)\s+style": {
            "type": "change_style",
            "instruction": "Use {style} visual style"
        },
        
        # Removing components
        r"remove\s+(\w+)": {
            "type": "remove_component",
            "instruction": "Remove the {component} from the diagram"
        },
        r"delete\s+(\w+)": {
            "type": "remove_component",
            "instruction": "Delete the {component} from the diagram"
        },
        
        # Reorganizing
        r"reorganize|restructure": {
            "type": "reorganize",
            "instruction": "Reorganize the diagram structure for better clarity"
        },
        r"simplify": {
            "type": "simplify",
            "instruction": "Simplify the diagram by removing unnecessary complexity"
        }
    }
    
    @staticmethod
    def detect_refinement_type(refinement_prompt: str) -> Dict[str, Any]:
        """
        Detect the type of refinement requested.
        
        Returns dict with type, component, and instruction.
        """
        prompt_lower = refinement_prompt.lower()
        
        for pattern, info in IterativeRefinement.REFINEMENT_PATTERNS.items():
            match = re.search(pattern, prompt_lower)
            if match:
                result = {
                    "type": info["type"],
                    "instruction": info["instruction"]
                }
                
                # Fill in placeholders from regex groups
                if match.groups():
                    groups = match.groups()
                    if "{component}" in result["instruction"]:
                        result["instruction"] = result["instruction"].replace(
                            "{component}", groups[0]
                        )
                        result["component"] = groups[0]
                    
                    if len(groups) > 1 and "{size}" in result["instruction"]:
                        result["instruction"] = result["instruction"].replace(
                            "{size}", groups[1]
                        )
                        result["modifier"] = groups[1]
                    
                    if "{color}" in result["instruction"]:
                        result["instruction"] = result["instruction"].replace(
                            "{color}", groups[0] if groups else "default"
                        )
                        result["color"] = groups[0] if groups else "default"
                    
                    if "{style}" in result["instruction"]:
                        result["instruction"] = result["instruction"].replace(
                            "{style}", groups[0] if groups else "default"
                        )
                        result["style"] = groups[0] if groups else "default"
                
                logger.info(f"Detected refinement type: {result['type']}")
                return result
        
        # Default: general modification
        return {
            "type": "general_modification",
            "instruction": "Make the requested modification to the diagram"
        }
    
    @staticmethod
    def build_refinement_prompt(
        current_code: str,
        refinement_request: str,
        context: Optional[SessionContext] = None
    ) -> str:
        """
        Build enhanced prompt for iterative refinement.
        
        Features #332-334: Handle various refinement types
        """
        # Detect refinement type
        refinement_info = IterativeRefinement.detect_refinement_type(refinement_request)
        
        # Build base prompt
        prompt_parts = [
            "You are refining an existing Mermaid diagram.",
            "",
            "Current diagram:",
            "```",
            current_code,
            "```",
            "",
            f"Refinement request: {refinement_request}",
            f"Instruction: {refinement_info['instruction']}",
            "",
            "Requirements:",
            "1. Keep the same diagram type and overall structure",
            "2. Preserve existing nodes unless explicitly asked to remove",
            "3. Maintain proper Mermaid syntax",
            "4. Make ONLY the requested changes",
            "5. Output valid Mermaid code without markdown fences",
        ]
        
        # Add specific instructions based on refinement type
        if refinement_info["type"] == "add_component":
            prompt_parts.extend([
                "",
                "Adding component instructions:",
                "- Add the new component with a clear label",
                "- Connect it appropriately to existing components",
                "- Maintain diagram flow and readability"
            ])
        
        elif refinement_info["type"] == "modify_size":
            prompt_parts.extend([
                "",
                "Size modification instructions:",
                "- Adjust node size/emphasis using Mermaid styling",
                "- Use double brackets [[ ]] for emphasis if appropriate",
                "- Maintain visual hierarchy"
            ])
        
        elif refinement_info["type"] == "change_color":
            color = refinement_info.get("color", "default")
            prompt_parts.extend([
                "",
                "Color change instructions:",
                f"- Apply {color} color scheme using Mermaid styling",
                "- Use style or classDef if needed",
                "- Ensure good contrast and readability"
            ])
        
        elif refinement_info["type"] == "remove_component":
            component = refinement_info.get("component", "")
            prompt_parts.extend([
                "",
                "Component removal instructions:",
                f"- Remove {component} and all its connections",
                "- Adjust remaining connections if needed",
                "- Maintain diagram coherence"
            ])
        
        # Add context if available (Feature #335)
        if context and context.diagrams:
            context_summary = context.get_context_summary()
            prompt_parts.extend([
                "",
                "Session context:",
                context_summary
            ])
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def apply_refinement_heuristics(
        original_code: str,
        refined_code: str,
        refinement_request: str
    ) -> str:
        """
        Apply heuristics to ensure refinement was applied correctly.
        
        Validates that the refinement actually changed the diagram.
        """
        # Check if anything changed
        if original_code.strip() == refined_code.strip():
            logger.warning("Refinement produced identical output")
            return refined_code
        
        # Check if it's still valid Mermaid
        if not any(keyword in refined_code.lower() for keyword in 
                  ["graph", "flowchart", "sequencediagram", "erdiagram"]):
            logger.warning("Refined code may not be valid Mermaid")
        
        # Count nodes before and after
        original_nodes = len(re.findall(r'(\w+)\[', original_code))
        refined_nodes = len(re.findall(r'(\w+)\[', refined_code))
        
        refinement_info = IterativeRefinement.detect_refinement_type(refinement_request)
        
        if refinement_info["type"] == "add_component":
            if refined_nodes <= original_nodes:
                logger.warning(
                    f"Expected more nodes after adding component: "
                    f"{original_nodes} → {refined_nodes}"
                )
        elif refinement_info["type"] == "remove_component":
            if refined_nodes >= original_nodes:
                logger.warning(
                    f"Expected fewer nodes after removing component: "
                    f"{original_nodes} → {refined_nodes}"
                )
        
        logger.info(
            f"Refinement applied: {original_nodes} → {refined_nodes} nodes"
        )
        
        return refined_code


class RefinementHistory:
    """Track history of refinements for a diagram."""
    
    def __init__(self, original_code: str, original_prompt: str):
        self.original_code = original_code
        self.original_prompt = original_prompt
        self.refinements: List[Dict[str, Any]] = []
        self.current_code = original_code
    
    def add_refinement(
        self,
        refinement_prompt: str,
        refined_code: str,
        provider: str,
        model: str
    ):
        """Add a refinement to history."""
        refinement = {
            "step": len(self.refinements) + 1,
            "refinement_prompt": refinement_prompt,
            "previous_code": self.current_code,
            "refined_code": refined_code,
            "provider": provider,
            "model": model,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.refinements.append(refinement)
        self.current_code = refined_code
        
        logger.info(
            f"Added refinement step {refinement['step']}: "
            f"{refinement_prompt[:50]}..."
        )
    
    def get_all_prompts(self) -> List[str]:
        """Get all prompts in order."""
        prompts = [self.original_prompt]
        prompts.extend(r["refinement_prompt"] for r in self.refinements)
        return prompts
    
    def get_refinement_summary(self) -> str:
        """Get human-readable summary of refinements."""
        if not self.refinements:
            return "No refinements yet."
        
        lines = [
            f"Refinement history ({len(self.refinements)} steps):",
            ""
        ]
        
        for refinement in self.refinements:
            lines.append(
                f"Step {refinement['step']}: {refinement['refinement_prompt']}"
            )
        
        return "\n".join(lines)
