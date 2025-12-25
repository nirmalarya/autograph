"""
TLS 1.3 Configuration Module for Autograph Services
Provides secure TLS configuration with TLS 1.3 enforcement
"""
import ssl
import os
from pathlib import Path


def get_ssl_context(
    cert_file: str = None,
    key_file: str = None,
    ca_file: str = None,
    require_client_cert: bool = False
) -> ssl.SSLContext:
    """
    Create an SSL context configured for TLS 1.3 only.

    Args:
        cert_file: Path to server certificate file
        key_file: Path to server private key file
        ca_file: Path to CA certificate file (for mutual TLS)
        require_client_cert: Whether to require client certificates (mutual TLS)

    Returns:
        ssl.SSLContext configured for TLS 1.3
    """
    # Default certificate paths
    if cert_file is None:
        cert_dir = Path(__file__).parent.parent / "certs"
        cert_file = str(cert_dir / "server-cert.pem")

    if key_file is None:
        cert_dir = Path(__file__).parent.parent / "certs"
        key_file = str(cert_dir / "server-key.pem")

    if ca_file is None:
        cert_dir = Path(__file__).parent.parent / "certs"
        ca_file = str(cert_dir / "ca-cert.pem")

    # Create SSL context with TLS 1.3 minimum
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Set minimum TLS version to 1.3
    context.minimum_version = ssl.TLSVersion.TLSv1_3

    # Set maximum TLS version to 1.3 (enforce TLS 1.3 only)
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    # Load server certificate and private key
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    # Configure cipher suites for TLS 1.3
    # TLS 1.3 cipher suites (only these are valid for TLS 1.3)
    context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256')

    # Security options
    context.options |= ssl.OP_NO_TLSv1    # Disable TLS 1.0
    context.options |= ssl.OP_NO_TLSv1_1  # Disable TLS 1.1
    context.options |= ssl.OP_NO_TLSv1_2  # Disable TLS 1.2
    context.options |= ssl.OP_SINGLE_DH_USE
    context.options |= ssl.OP_SINGLE_ECDH_USE
    context.options |= ssl.OP_NO_COMPRESSION

    # Enable certificate verification for mutual TLS if requested
    if require_client_cert:
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=ca_file)
    else:
        context.verify_mode = ssl.CERT_NONE

    # Check hostname (server-side doesn't check, but good to set)
    context.check_hostname = False

    return context


def get_client_ssl_context(
    ca_file: str = None,
    cert_file: str = None,
    key_file: str = None,
    verify_server: bool = True
) -> ssl.SSLContext:
    """
    Create an SSL context for client connections (service-to-service).

    Args:
        ca_file: Path to CA certificate for server verification
        cert_file: Path to client certificate (for mutual TLS)
        key_file: Path to client private key (for mutual TLS)
        verify_server: Whether to verify server certificate

    Returns:
        ssl.SSLContext configured for TLS 1.3 client connections
    """
    # Default certificate paths
    if ca_file is None:
        cert_dir = Path(__file__).parent.parent / "certs"
        ca_file = str(cert_dir / "ca-cert.pem")

    # Create SSL context for client
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Set minimum TLS version to 1.3
    context.minimum_version = ssl.TLSVersion.TLSv1_3

    # Set maximum TLS version to 1.3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    # Configure cipher suites for TLS 1.3
    context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256')

    # Security options
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    context.options |= ssl.OP_NO_TLSv1_2
    context.options |= ssl.OP_NO_COMPRESSION

    # Load CA certificate for server verification
    if verify_server:
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_verify_locations(cafile=ca_file)
    else:
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False

    # Load client certificate for mutual TLS if provided
    if cert_file and key_file:
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    return context


def get_uvicorn_ssl_config(
    cert_file: str = None,
    key_file: str = None,
    ca_file: str = None,
    require_client_cert: bool = False
) -> dict:
    """
    Get SSL configuration for Uvicorn server.

    Args:
        cert_file: Path to server certificate file
        key_file: Path to server private key file
        ca_file: Path to CA certificate file
        require_client_cert: Whether to require client certificates

    Returns:
        Dictionary with Uvicorn SSL configuration
    """
    # Default certificate paths
    if cert_file is None:
        cert_dir = Path(__file__).parent.parent / "certs"
        cert_file = str(cert_dir / "server-cert.pem")

    if key_file is None:
        cert_dir = Path(__file__).parent.parent / "certs"
        key_file = str(cert_dir / "server-key.pem")

    ssl_context = get_ssl_context(cert_file, key_file, ca_file, require_client_cert)

    return {
        "ssl": ssl_context,
        "ssl_keyfile": key_file,
        "ssl_certfile": cert_file,
        "ssl_version": ssl.PROTOCOL_TLS_SERVER,
        "ssl_cert_reqs": ssl.CERT_REQUIRED if require_client_cert else ssl.CERT_NONE,
        "ssl_ca_certs": ca_file if require_client_cert else None,
    }


# Environment variable to enable/disable TLS
def is_tls_enabled() -> bool:
    """Check if TLS is enabled via environment variable."""
    return os.getenv("TLS_ENABLED", "true").lower() in ("true", "1", "yes")


def get_protocol_scheme() -> str:
    """Get the protocol scheme (http or https) based on TLS configuration."""
    return "https" if is_tls_enabled() else "http"
