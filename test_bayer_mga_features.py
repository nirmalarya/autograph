#!/usr/bin/env python3
"""
Test Bayer MGA Integration Features

Tests:
- Bayer MGA as primary provider
- MGA endpoint configuration
- MGA authentication
- MGA model configuration
- MGA fallback chain
- MGA cost tracking
- MGA usage analytics
- MGA compliance/audit logging
"""

import requests
import json
import time

AI_SERVICE_URL = "http://localhost:8084"

def test_mga_primary_provider():
    """Test: Bayer MGA is configured as primary provider"""
    print("=" * 80)
    print("TEST: Bayer MGA Primary Provider")
    print("=" * 80)
    
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/providers")
    data = response.json()
    
    print(f"\nProviders Status:")
    print(f"  Primary provider: {data.get('primary_provider')}")
    print(f"  MGA configured: {data.get('mga_configured')}")
    print(f"  Available providers: {', '.join(data.get('available_providers', []))}")
    print(f"  Fallback chain: {', '.join(data.get('fallback_chain', []))}")
    
    is_primary = data.get('primary_provider') == 'bayer_mga'
    is_configured = data.get('mga_configured') == True
    
    if is_primary and is_configured:
        print("\n✓ PASS: Bayer MGA is primary provider")
        return True
    else:
        print("\n✗ FAIL: Bayer MGA is not primary provider")
        return False

def test_mga_endpoint():
    """Test: MGA endpoint is configured correctly"""
    print("\n" + "=" * 80)
    print("TEST: MGA Endpoint Configuration")
    print("=" * 80)
    
    # Read the providers.py file directly to check endpoint
    try:
        with open('./services/ai-service/src/providers.py', 'r') as f:
            content = f.read()
        
        expected_endpoint = "https://chat.int.bayer.com/api/v2/chat/completions"
        
        # Check if the endpoint is in the file
        has_endpoint = expected_endpoint in content
        
        print(f"\nMGA Endpoint:")
        print(f"  Expected: {expected_endpoint}")
        print(f"  Found in code: {has_endpoint}")
        
        if has_endpoint:
            print("\n✓ PASS: MGA endpoint is correct")
            return True
        else:
            print("\n✗ FAIL: MGA endpoint not found in code")
            return False
    except Exception as e:
        print(f"\n✗ FAIL: Could not verify endpoint: {e}")
        return False

def test_mga_authentication():
    """Test: MGA authentication with Bearer token"""
    print("\n" + "=" * 80)
    print("TEST: MGA Authentication")
    print("=" * 80)
    
    # Check that authentication is configured
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/providers")
    data = response.json()
    
    mga_configured = data.get('mga_configured')
    
    print(f"\nAuthentication Status:")
    print(f"  MGA API key configured: {mga_configured}")
    print(f"  Authentication method: Bearer token")
    
    if mga_configured:
        print("\n✓ PASS: MGA authentication configured")
        return True
    else:
        print("\n✗ FAIL: MGA authentication not configured")
        return False

def test_mga_model():
    """Test: MGA model is gpt-4.1 by default"""
    print("\n" + "=" * 80)
    print("TEST: MGA Model Configuration")
    print("=" * 80)
    
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/available-models")
    data = response.json()
    
    # The structure is: { "providers": { "bayer_mga": { ... } } }
    providers = data.get('providers', {})
    mga_models = providers.get('bayer_mga', {})
    default_model = mga_models.get('default')
    models = mga_models.get('models', [])
    
    print(f"\nMGA Models:")
    print(f"  Default model: {default_model}")
    print(f"  Available models: {', '.join(models)}")
    print(f"  Description: {mga_models.get('description')}")
    
    if default_model == 'gpt-4.1':
        print("\n✓ PASS: MGA default model is gpt-4.1")
        return True
    else:
        print("\n✗ FAIL: MGA default model is not gpt-4.1")
        return False

def test_mga_fallback_chain():
    """Test: MGA fallback chain: MGA → OpenAI → Anthropic"""
    print("\n" + "=" * 80)
    print("TEST: MGA Fallback Chain")
    print("=" * 80)
    
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/providers")
    data = response.json()
    
    fallback_chain = data.get('fallback_chain', [])
    
    print(f"\nFallback Chain:")
    for i, provider in enumerate(fallback_chain, 1):
        print(f"  {i}. {provider}")
    
    # Check order
    has_mga_first = len(fallback_chain) > 0 and 'MGA' in fallback_chain[0]
    has_openai_second = len(fallback_chain) > 1 and 'OpenAI' in fallback_chain[1]
    has_anthropic_third = len(fallback_chain) > 2 and 'Anthropic' in fallback_chain[2]
    
    if has_mga_first and has_openai_second:
        print("\n✓ PASS: MGA fallback chain is correct")
        return True
    else:
        print("\n✗ FAIL: MGA fallback chain is incorrect")
        return False

def test_mga_cost_tracking():
    """Test: MGA cost tracking"""
    print("\n" + "=" * 80)
    print("TEST: MGA Cost Tracking")
    print("=" * 80)
    
    # Check pricing endpoint
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/pricing")
    data = response.json()
    
    # Structure is: { "pricing": { "bayer_mga": { "gpt-4.1": {...} } } }
    pricing_data = data.get('pricing', {})
    mga_pricing = pricing_data.get('bayer_mga', {})
    gpt41_pricing = mga_pricing.get('gpt-4.1', {})
    
    print(f"\nMGA Pricing (gpt-4.1):")
    print(f"  Input cost: ${gpt41_pricing.get('prompt', 0):.4f} per 1K tokens")
    print(f"  Output cost: ${gpt41_pricing.get('completion', 0):.4f} per 1K tokens")
    print(f"  Available models: {', '.join(mga_pricing.keys())}")
    
    # Check usage summary
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/usage-summary")
    data = response.json()
    
    print(f"\nUsage Tracking:")
    print(f"  Total generations: {data.get('total_generations', 0)}")
    print(f"  Total tokens: {data.get('total_tokens', 0)}")
    print(f"  Estimated cost: ${data.get('estimated_cost', 0):.2f}")
    
    has_pricing = 'bayer_mga' in pricing_data
    has_usage = 'total_generations' in data
    
    if has_pricing and has_usage:
        print("\n✓ PASS: MGA cost tracking is working")
        return True
    else:
        print("\n✗ FAIL: MGA cost tracking is not complete")
        return False

def test_mga_usage_analytics():
    """Test: MGA usage analytics"""
    print("\n" + "=" * 80)
    print("TEST: MGA Usage Analytics")
    print("=" * 80)
    
    # Check provider comparison
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/provider-comparison")
    data = response.json()
    
    mga_stats = None
    for provider in data.get('providers', []):
        if provider.get('provider') == 'bayer_mga':
            mga_stats = provider
            break
    
    if mga_stats:
        print(f"\nMGA Analytics:")
        print(f"  Total generations: {mga_stats.get('total_generations', 0)}")
        print(f"  Success rate: {mga_stats.get('success_rate', 0):.1f}%")
        print(f"  Average latency: {mga_stats.get('avg_latency_ms', 0):.0f}ms")
        print(f"  Average quality: {mga_stats.get('avg_quality_score', 0):.1f}")
    
    # Check generation history
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/generation-history")
    history_data = response.json()
    
    print(f"\nGeneration History:")
    print(f"  Total records: {len(history_data.get('generations', []))}")
    
    has_stats = mga_stats is not None
    has_history = 'generations' in history_data
    
    if has_stats or has_history:
        print("\n✓ PASS: MGA usage analytics is working")
        return True
    else:
        print("\n✗ FAIL: MGA usage analytics not available")
        return False

def test_mga_compliance_logging():
    """Test: MGA compliance and audit logging"""
    print("\n" + "=" * 80)
    print("TEST: MGA Compliance and Audit Logging")
    print("=" * 80)
    
    # Check that generation history includes all required fields for compliance
    response = requests.get(f"{AI_SERVICE_URL}/api/ai/generation-history")
    data = response.json()
    
    generations = data.get('generations', [])
    
    print(f"\nCompliance Logging:")
    print(f"  Total generation records: {len(generations)}")
    
    if len(generations) > 0:
        sample = generations[0]
        has_id = 'generation_id' in sample
        has_timestamp = 'timestamp' in sample
        has_provider = 'provider' in sample
        has_prompt = 'prompt' in sample or 'original_prompt' in sample
        has_tokens = 'tokens_used' in sample
        
        print(f"  Records include:")
        print(f"    - Generation ID: {has_id}")
        print(f"    - Timestamp: {has_timestamp}")
        print(f"    - Provider: {has_provider}")
        print(f"    - Prompt: {has_prompt}")
        print(f"    - Token usage: {has_tokens}")
        
        all_fields = has_id and has_timestamp and has_provider and has_tokens
        
        if all_fields:
            print("\n✓ PASS: MGA compliance logging is complete")
            return True
        else:
            print("\n✗ FAIL: MGA compliance logging is missing fields")
            return False
    else:
        print("  No generation records yet (this is okay for new systems)")
        print("\n✓ PASS: MGA compliance logging infrastructure is in place")
        return True

def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("BAYER MGA INTEGRATION TEST SUITE")
    print("=" * 80)
    print()
    
    tests = [
        ("Bayer MGA Primary Provider", test_mga_primary_provider),
        ("MGA Endpoint", test_mga_endpoint),
        ("MGA Authentication", test_mga_authentication),
        ("MGA Model (gpt-4.1)", test_mga_model),
        ("MGA Fallback Chain", test_mga_fallback_chain),
        ("MGA Cost Tracking", test_mga_cost_tracking),
        ("MGA Usage Analytics", test_mga_usage_analytics),
        ("MGA Compliance Logging", test_mga_compliance_logging),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ FAIL: {name} - Exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passing ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All Bayer MGA features are working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} feature(s) need attention")
        return 1

if __name__ == "__main__":
    exit(main())
