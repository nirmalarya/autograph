"""AI Provider abstraction layer for diagram generation."""
import os
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DiagramType(str, Enum):
    """Supported diagram types."""
    ARCHITECTURE = "architecture"
    SEQUENCE = "sequence"
    ERD = "erd"
    FLOWCHART = "flowchart"
    CLASS_DIAGRAM = "class_diagram"
    STATE_DIAGRAM = "state_diagram"
    GANTT = "gantt"
    GIT_GRAPH = "git_graph"


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    async def generate_diagram(
        self, 
        prompt: str, 
        diagram_type: Optional[DiagramType] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate diagram from prompt.
        
        Returns:
            {
                "mermaid_code": str,
                "diagram_type": str,
                "explanation": str,
                "provider": str,
                "model": str,
                "tokens_used": int
            }
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model for this provider."""
        pass


class BayerMGAProvider(AIProvider):
    """Bayer MGA (myGenAssist) AI provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.endpoint = "https://chat.int.bayer.com/api/v2/chat/completions"
        self.default_model = "gpt-4.1"
    
    def get_default_model(self) -> str:
        return self.default_model
    
    async def generate_diagram(
        self, 
        prompt: str, 
        diagram_type: Optional[DiagramType] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate diagram using Bayer MGA."""
        model = model or self.default_model
        
        # Build enhanced prompt with examples
        enhanced_prompt = self._build_enhanced_prompt(prompt, diagram_type)
        
        # Call MGA API (OpenAI-compatible format)
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at creating Mermaid diagram code. Generate clean, well-structured Mermaid diagrams. Only output valid Mermaid code without any markdown code fences or explanations."
                            },
                            {
                                "role": "user",
                                "content": enhanced_prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"MGA API error: {response.status_code} - {response.text}")
                
                data = response.json()
                mermaid_code = data["choices"][0]["message"]["content"].strip()
                
                # Clean up code fences if present
                mermaid_code = self._clean_mermaid_code(mermaid_code)
                
                # Detect actual diagram type
                detected_type = diagram_type or self._detect_diagram_type(mermaid_code, prompt)
                
                return {
                    "mermaid_code": mermaid_code,
                    "diagram_type": detected_type,
                    "explanation": f"Generated {detected_type} diagram using Bayer MGA",
                    "provider": "bayer_mga",
                    "model": model,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                }
                
            except Exception as e:
                logger.error(f"Bayer MGA generation failed: {str(e)}")
                raise
    
    def _build_enhanced_prompt(self, prompt: str, diagram_type: Optional[DiagramType]) -> str:
        """Build enhanced prompt with multi-shot learning examples."""
        base = f"Create a Mermaid diagram for: {prompt}\n\n"
        
        if diagram_type == DiagramType.ARCHITECTURE or "architecture" in prompt.lower():
            base += """Example format for architecture diagrams:
graph TB
    Frontend[Frontend<br/>React]
    Backend[Backend<br/>Node.js]
    DB[(Database<br/>PostgreSQL)]
    
    Frontend -->|REST API| Backend
    Backend -->|SQL| DB

Now create a similar diagram for the request."""
        
        elif diagram_type == DiagramType.SEQUENCE or any(word in prompt.lower() for word in ["flow", "sequence", "process", "login", "auth"]):
            base += """Example format for sequence diagrams:
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant DB
    
    User->>Frontend: Login request
    Frontend->>Backend: POST /auth/login
    Backend->>DB: Verify credentials
    DB-->>Backend: User data
    Backend-->>Frontend: JWT token
    Frontend-->>User: Login successful

Now create a similar diagram for the request."""
        
        elif diagram_type == DiagramType.ERD or "database" in prompt.lower() or "schema" in prompt.lower():
            base += """Example format for ER diagrams:
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
    
    USER {
        int id PK
        string email
        string name
    }
    ORDER {
        int id PK
        int user_id FK
        date created_at
    }

Now create a similar diagram for the request."""
        
        elif diagram_type == DiagramType.FLOWCHART or "flowchart" in prompt.lower():
            base += """Example format for flowcharts:
flowchart TD
    Start([Start]) --> Input[/Get user input/]
    Input --> Decision{Valid?}
    Decision -->|Yes| Process[Process data]
    Decision -->|No| Error[Show error]
    Process --> Output[/Display result/]
    Output --> End([End])
    Error --> Input

Now create a similar diagram for the request."""
        
        return base
    
    def _clean_mermaid_code(self, code: str) -> str:
        """Remove markdown code fences and extra formatting."""
        # Remove ```mermaid or ``` code fences
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped in ['```', '```mermaid', '```graph', '```flowchart', '```sequenceDiagram', '```erDiagram']:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _detect_diagram_type(self, mermaid_code: str, prompt: str) -> str:
        """Detect diagram type from Mermaid code or prompt."""
        code_lower = mermaid_code.lower()
        prompt_lower = prompt.lower()
        
        if "sequencediagram" in code_lower or any(word in prompt_lower for word in ["flow", "sequence", "process", "login"]):
            return "sequence"
        elif "erdiagram" in code_lower or any(word in prompt_lower for word in ["database", "schema", "tables", "erd"]):
            return "erd"
        elif "classdiagram" in code_lower or "class diagram" in prompt_lower:
            return "class_diagram"
        elif "statediagram" in code_lower or "state" in prompt_lower:
            return "state_diagram"
        elif "gantt" in code_lower:
            return "gantt"
        elif "gitgraph" in code_lower:
            return "git_graph"
        elif any(word in code_lower for word in ["graph td", "graph lr", "flowchart"]):
            if any(word in prompt_lower for word in ["architecture", "system", "microservice", "service"]):
                return "architecture"
            return "flowchart"
        
        return "architecture"


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 Turbo provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.default_model = "gpt-4-turbo"
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
    
    def get_default_model(self) -> str:
        return self.default_model
    
    async def generate_diagram(
        self, 
        prompt: str, 
        diagram_type: Optional[DiagramType] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate diagram using OpenAI."""
        model = model or self.default_model
        
        enhanced_prompt = self._build_prompt(prompt, diagram_type)
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating Mermaid diagram code. Generate clean, well-structured Mermaid diagrams. Only output valid Mermaid code without any markdown code fences."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            mermaid_code = response.choices[0].message.content.strip()
            mermaid_code = self._clean_code(mermaid_code)
            
            detected_type = diagram_type or self._detect_type(mermaid_code, prompt)
            
            return {
                "mermaid_code": mermaid_code,
                "diagram_type": detected_type,
                "explanation": f"Generated {detected_type} diagram using OpenAI",
                "provider": "openai",
                "model": model,
                "tokens_used": response.usage.total_tokens
            }
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise
    
    def _build_prompt(self, prompt: str, diagram_type: Optional[DiagramType]) -> str:
        return f"Create a Mermaid diagram for: {prompt}"
    
    def _clean_code(self, code: str) -> str:
        lines = [l for l in code.split('\n') if not l.strip().startswith('```')]
        return '\n'.join(lines).strip()
    
    def _detect_type(self, code: str, prompt: str) -> str:
        if "sequenceDiagram" in code:
            return "sequence"
        elif "erDiagram" in code:
            return "erd"
        elif "graph" in code or "flowchart" in code:
            return "architecture" if "architecture" in prompt.lower() else "flowchart"
        return "architecture"


class AnthropicProvider(AIProvider):
    """Anthropic Claude 3.5 Sonnet provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.default_model = "claude-3-5-sonnet-20241022"
        
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
    
    def get_default_model(self) -> str:
        return self.default_model
    
    async def generate_diagram(
        self, 
        prompt: str, 
        diagram_type: Optional[DiagramType] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate diagram using Anthropic."""
        model = model or self.default_model
        
        enhanced_prompt = f"Create a Mermaid diagram for: {prompt}"
        
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=2000,
                system="You are an expert at creating Mermaid diagram code. Generate clean, well-structured Mermaid diagrams. Only output valid Mermaid code without any markdown code fences.",
                messages=[
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ]
            )
            
            mermaid_code = response.content[0].text.strip()
            mermaid_code = self._clean_code(mermaid_code)
            
            detected_type = diagram_type or self._detect_type(mermaid_code, prompt)
            
            return {
                "mermaid_code": mermaid_code,
                "diagram_type": detected_type,
                "explanation": f"Generated {detected_type} diagram using Anthropic",
                "provider": "anthropic",
                "model": model,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }
        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise
    
    def _clean_code(self, code: str) -> str:
        lines = [l for l in code.split('\n') if not l.strip().startswith('```')]
        return '\n'.join(lines).strip()
    
    def _detect_type(self, code: str, prompt: str) -> str:
        if "sequenceDiagram" in code:
            return "sequence"
        elif "erDiagram" in code:
            return "erd"
        return "architecture"


class GeminiProvider(AIProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.default_model = "gemini-pro"
        
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.default_model)
    
    def get_default_model(self) -> str:
        return self.default_model
    
    async def generate_diagram(
        self, 
        prompt: str, 
        diagram_type: Optional[DiagramType] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate diagram using Gemini."""
        enhanced_prompt = f"Create a Mermaid diagram for: {prompt}. Output only valid Mermaid code without markdown code fences."
        
        try:
            response = self.model.generate_content(enhanced_prompt)
            mermaid_code = response.text.strip()
            mermaid_code = self._clean_code(mermaid_code)
            
            detected_type = diagram_type or self._detect_type(mermaid_code, prompt)
            
            return {
                "mermaid_code": mermaid_code,
                "diagram_type": detected_type,
                "explanation": f"Generated {detected_type} diagram using Gemini",
                "provider": "gemini",
                "model": self.default_model,
                "tokens_used": 0  # Gemini doesn't provide token counts in the same way
            }
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise
    
    def _clean_code(self, code: str) -> str:
        lines = [l for l in code.split('\n') if not l.strip().startswith('```')]
        return '\n'.join(lines).strip()
    
    def _detect_type(self, code: str, prompt: str) -> str:
        if "sequenceDiagram" in code:
            return "sequence"
        elif "erDiagram" in code:
            return "erd"
        return "architecture"


class AIProviderFactory:
    """Factory for creating AI providers with fallback chain."""
    
    @staticmethod
    def create_provider_chain() -> List[AIProvider]:
        """Create provider chain: MGA → OpenAI → Anthropic → Gemini."""
        providers = []
        
        # Primary: Bayer MGA
        mga_key = os.getenv("MGA_API_KEY")
        if mga_key:
            try:
                providers.append(BayerMGAProvider(mga_key))
                logger.info("Bayer MGA provider configured (PRIMARY)")
            except Exception as e:
                logger.warning(f"Failed to configure Bayer MGA: {e}")
        
        # Fallback 1: OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                providers.append(OpenAIProvider(openai_key))
                logger.info("OpenAI provider configured (FALLBACK 1)")
            except Exception as e:
                logger.warning(f"Failed to configure OpenAI: {e}")
        
        # Fallback 2: Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                providers.append(AnthropicProvider(anthropic_key))
                logger.info("Anthropic provider configured (FALLBACK 2)")
            except Exception as e:
                logger.warning(f"Failed to configure Anthropic: {e}")
        
        # Fallback 3: Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                providers.append(GeminiProvider(gemini_key))
                logger.info("Gemini provider configured (FALLBACK 3)")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")
        
        if not providers:
            logger.error("No AI providers configured! Set at least one API key.")
        
        return providers
    
    @staticmethod
    async def generate_with_fallback(
        prompt: str,
        diagram_type: Optional[DiagramType] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate diagram using provider chain with automatic fallback."""
        providers = AIProviderFactory.create_provider_chain()
        
        if not providers:
            raise Exception("No AI providers configured. Please set API keys in environment.")
        
        last_error = None
        
        for i, provider in enumerate(providers):
            provider_name = provider.__class__.__name__
            logger.info(f"Attempting generation with {provider_name} (attempt {i+1}/{len(providers)})")
            
            try:
                result = await provider.generate_diagram(prompt, diagram_type, model)
                logger.info(f"✓ Successfully generated diagram with {provider_name}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"✗ {provider_name} failed: {str(e)}")
                if i < len(providers) - 1:
                    logger.info(f"Falling back to next provider...")
                continue
        
        # All providers failed
        raise Exception(f"All AI providers failed. Last error: {str(last_error)}")
