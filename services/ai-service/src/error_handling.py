"""
Error Handling for AI Service

Features implemented:
- Feature #363: Generation timeout handling
- Feature #364: API failure error handling  
- Feature #365: Invalid API key detection
- Feature #359: Multi-language error messages
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Error codes for different failure types."""
    TIMEOUT = "GENERATION_TIMEOUT"
    API_FAILURE = "API_FAILURE"
    INVALID_API_KEY = "INVALID_API_KEY"
    RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    NETWORK_ERROR = "NETWORK_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AIServiceError:
    """Structured error information."""
    code: ErrorCode
    message: str
    severity: ErrorSeverity
    provider: Optional[str] = None
    model: Optional[str] = None
    retry_possible: bool = False
    suggestion: Optional[str] = None
    wait_time: Optional[int] = None  # Feature #366: Wait time for rate limiting
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "error_code": self.code.value,
            "message": self.message,
            "severity": self.severity.value,
            "provider": self.provider,
            "model": self.model,
            "retry_possible": self.retry_possible,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp,
        }

        # Feature #366: Include wait_time for rate limiting
        if self.wait_time is not None:
            result["wait_time"] = self.wait_time
            result["retry_after"] = self.wait_time  # Also include as retry_after for compatibility

        return result


# Feature #359: Multi-language error messages
ERROR_MESSAGES = {
    "en": {
        ErrorCode.TIMEOUT: "Generation timed out after {timeout} seconds",
        ErrorCode.API_FAILURE: "API request failed: {details}",
        ErrorCode.INVALID_API_KEY: "Invalid or missing API key for {provider}",
        ErrorCode.RATE_LIMIT: "Rate limit exceeded. Please try again later",
        ErrorCode.INVALID_RESPONSE: "Received invalid response from AI provider",
        ErrorCode.NETWORK_ERROR: "Network error occurred: {details}",
        ErrorCode.PROVIDER_ERROR: "Provider error: {details}",
        ErrorCode.UNKNOWN_ERROR: "An unexpected error occurred",
    },
    "de": {
        ErrorCode.TIMEOUT: "Generierung nach {timeout} Sekunden abgelaufen",
        ErrorCode.API_FAILURE: "API-Anfrage fehlgeschlagen: {details}",
        ErrorCode.INVALID_API_KEY: "Ungültiger oder fehlender API-Schlüssel für {provider}",
        ErrorCode.RATE_LIMIT: "Ratenlimit überschritten. Bitte versuchen Sie es später erneut",
        ErrorCode.INVALID_RESPONSE: "Ungültige Antwort vom AI-Anbieter erhalten",
        ErrorCode.NETWORK_ERROR: "Netzwerkfehler aufgetreten: {details}",
        ErrorCode.PROVIDER_ERROR: "Anbieterfehler: {details}",
        ErrorCode.UNKNOWN_ERROR: "Ein unerwarteter Fehler ist aufgetreten",
    },
    "es": {
        ErrorCode.TIMEOUT: "La generación expiró después de {timeout} segundos",
        ErrorCode.API_FAILURE: "Falló la solicitud de API: {details}",
        ErrorCode.INVALID_API_KEY: "Clave API inválida o faltante para {provider}",
        ErrorCode.RATE_LIMIT: "Límite de tasa excedido. Intente nuevamente más tarde",
        ErrorCode.INVALID_RESPONSE: "Se recibió respuesta inválida del proveedor de IA",
        ErrorCode.NETWORK_ERROR: "Error de red: {details}",
        ErrorCode.PROVIDER_ERROR: "Error del proveedor: {details}",
        ErrorCode.UNKNOWN_ERROR: "Ocurrió un error inesperado",
    },
    "fr": {
        ErrorCode.TIMEOUT: "La génération a expiré après {timeout} secondes",
        ErrorCode.API_FAILURE: "Échec de la requête API: {details}",
        ErrorCode.INVALID_API_KEY: "Clé API invalide ou manquante pour {provider}",
        ErrorCode.RATE_LIMIT: "Limite de taux dépassée. Réessayez plus tard",
        ErrorCode.INVALID_RESPONSE: "Réponse invalide reçue du fournisseur IA",
        ErrorCode.NETWORK_ERROR: "Erreur réseau: {details}",
        ErrorCode.PROVIDER_ERROR: "Erreur du fournisseur: {details}",
        ErrorCode.UNKNOWN_ERROR: "Une erreur inattendue s'est produite",
    },
}


ERROR_SUGGESTIONS = {
    ErrorCode.TIMEOUT: "Try reducing the complexity of your diagram or increasing the timeout setting",
    ErrorCode.API_FAILURE: "Check your internet connection and try again",
    ErrorCode.INVALID_API_KEY: "Verify your API key in the settings or contact your administrator",
    ErrorCode.RATE_LIMIT: "Wait a few minutes before making more requests",
    ErrorCode.INVALID_RESPONSE: "The AI provider returned an unexpected response. Try again or use a different provider",
    ErrorCode.NETWORK_ERROR: "Check your internet connection and firewall settings",
    ErrorCode.PROVIDER_ERROR: "The AI provider encountered an error. Try a different provider or wait a moment",
    ErrorCode.UNKNOWN_ERROR: "Please try again. If the problem persists, contact support",
}


class AIErrorHandler:
    """Handle and format AI service errors."""
    
    def __init__(self, default_language: str = "en"):
        """
        Initialize error handler.
        
        Args:
            default_language: Default language for error messages (en, de, es, fr)
        """
        self.default_language = default_language
        self.error_counts = {}
    
    def create_timeout_error(
        self,
        timeout: float,
        provider: str,
        language: str = "en"
    ) -> AIServiceError:
        """
        Feature #363: Create timeout error.
        
        Args:
            timeout: Timeout duration in seconds
            provider: AI provider name
            language: Language code for error message
            
        Returns:
            AIServiceError object
        """
        lang = language if language in ERROR_MESSAGES else self.default_language
        message = ERROR_MESSAGES[lang][ErrorCode.TIMEOUT].format(timeout=timeout)
        
        return AIServiceError(
            code=ErrorCode.TIMEOUT,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            provider=provider,
            retry_possible=True,
            suggestion=ERROR_SUGGESTIONS[ErrorCode.TIMEOUT]
        )
    
    def create_api_failure_error(
        self,
        details: str,
        provider: str,
        status_code: Optional[int] = None,
        language: str = "en"
    ) -> AIServiceError:
        """
        Feature #364: Create API failure error.
        
        Args:
            details: Error details
            provider: AI provider name
            status_code: HTTP status code if available
            language: Language code for error message
            
        Returns:
            AIServiceError object
        """
        lang = language if language in ERROR_MESSAGES else self.default_language
        message = ERROR_MESSAGES[lang][ErrorCode.API_FAILURE].format(details=details)
        
        # Determine if retry is possible based on status code
        retry_possible = status_code in [408, 429, 500, 502, 503, 504] if status_code else True
        
        return AIServiceError(
            code=ErrorCode.API_FAILURE,
            message=message,
            severity=ErrorSeverity.HIGH,
            provider=provider,
            retry_possible=retry_possible,
            suggestion=ERROR_SUGGESTIONS[ErrorCode.API_FAILURE]
        )
    
    def create_invalid_api_key_error(
        self,
        provider: str,
        language: str = "en"
    ) -> AIServiceError:
        """
        Feature #365: Create invalid API key error.
        
        Args:
            provider: AI provider name
            language: Language code for error message
            
        Returns:
            AIServiceError object
        """
        lang = language if language in ERROR_MESSAGES else self.default_language
        message = ERROR_MESSAGES[lang][ErrorCode.INVALID_API_KEY].format(provider=provider)
        
        return AIServiceError(
            code=ErrorCode.INVALID_API_KEY,
            message=message,
            severity=ErrorSeverity.CRITICAL,
            provider=provider,
            retry_possible=False,
            suggestion=ERROR_SUGGESTIONS[ErrorCode.INVALID_API_KEY]
        )
    
    def create_rate_limit_error(
        self,
        provider: str,
        wait_time: Optional[int] = None,
        language: str = "en"
    ) -> AIServiceError:
        """
        Feature #366: Create rate limit error with wait time.

        Args:
            provider: AI provider name
            wait_time: Recommended wait time in seconds
            language: Language code for error message

        Returns:
            AIServiceError object with retry information
        """
        lang = language if language in ERROR_MESSAGES else self.default_language
        message = ERROR_MESSAGES[lang][ErrorCode.RATE_LIMIT]

        # Enhance message with wait time if available
        if wait_time:
            if lang == "en":
                message += f" Please wait {wait_time} seconds before retrying."
            elif lang == "de":
                message += f" Bitte warten Sie {wait_time} Sekunden, bevor Sie es erneut versuchen."
            elif lang == "es":
                message += f" Espere {wait_time} segundos antes de volver a intentarlo."
            elif lang == "fr":
                message += f" Veuillez attendre {wait_time} secondes avant de réessayer."

        error = AIServiceError(
            code=ErrorCode.RATE_LIMIT,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            provider=provider,
            retry_possible=True,
            wait_time=wait_time,  # Feature #366: Include wait time
            suggestion=ERROR_SUGGESTIONS[ErrorCode.RATE_LIMIT]
        )

        return error
    
    def create_network_error(
        self,
        details: str,
        provider: str,
        language: str = "en"
    ) -> AIServiceError:
        """Create network error."""
        lang = language if language in ERROR_MESSAGES else self.default_language
        message = ERROR_MESSAGES[lang][ErrorCode.NETWORK_ERROR].format(details=details)
        
        return AIServiceError(
            code=ErrorCode.NETWORK_ERROR,
            message=message,
            severity=ErrorSeverity.HIGH,
            provider=provider,
            retry_possible=True,
            suggestion=ERROR_SUGGESTIONS[ErrorCode.NETWORK_ERROR]
        )
    
    def create_provider_error(
        self,
        details: str,
        provider: str,
        language: str = "en"
    ) -> AIServiceError:
        """Create provider-specific error."""
        lang = language if language in ERROR_MESSAGES else self.default_language
        message = ERROR_MESSAGES[lang][ErrorCode.PROVIDER_ERROR].format(details=details)
        
        return AIServiceError(
            code=ErrorCode.PROVIDER_ERROR,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            provider=provider,
            retry_possible=True,
            suggestion=ERROR_SUGGESTIONS[ErrorCode.PROVIDER_ERROR]
        )
    
    def handle_http_error(
        self,
        status_code: int,
        response_text: str,
        provider: str,
        language: str = "en",
        retry_after: Optional[int] = None
    ) -> AIServiceError:
        """
        Handle HTTP errors from AI providers.

        Args:
            status_code: HTTP status code
            response_text: Response body text
            provider: AI provider name
            language: Language code
            retry_after: Retry-After header value (in seconds)

        Returns:
            Appropriate AIServiceError
        """
        # Track error frequency
        key = f"{provider}_{status_code}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Feature #365: Invalid API key (401, 403)
        if status_code in [401, 403]:
            return self.create_invalid_api_key_error(provider, language)

        # Feature #366: Rate limiting (429) with retry-after
        elif status_code == 429:
            # Parse retry-after from header or response
            wait_time = retry_after
            if not wait_time:
                # Try to extract from response text
                import re
                match = re.search(r'retry.*?(\d+)\s*second', response_text, re.IGNORECASE)
                if match:
                    wait_time = int(match.group(1))
                else:
                    wait_time = 60  # Default to 60 seconds if not specified

            return self.create_rate_limit_error(provider, wait_time, language)

        # Timeout (408, 504)
        elif status_code in [408, 504]:
            return self.create_timeout_error(30.0, provider, language)

        # Server errors (500-599)
        elif 500 <= status_code < 600:
            return self.create_provider_error(
                f"Server error {status_code}: {response_text[:100]}",
                provider,
                language
            )

        # Feature #364: Generic API failure
        else:
            return self.create_api_failure_error(
                f"HTTP {status_code}: {response_text[:100]}",
                provider,
                status_code,
                language
            )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts.copy(),
            "most_common": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5] if self.error_counts else []
        }


# Global error handler instance
_error_handler = AIErrorHandler()


def get_error_handler() -> AIErrorHandler:
    """Get global error handler instance."""
    return _error_handler
