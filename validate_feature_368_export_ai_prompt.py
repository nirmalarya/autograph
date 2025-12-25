#!/usr/bin/env python3
"""
Feature #368: Export AI prompt with diagram

Test that when exporting an AI-generated diagram, the export includes:
1. Original prompt used for generation
2. Generation settings (temperature, tokens, etc.)
3. Provider and model information
4. Quality metrics
5. Layout algorithm used
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8080"
AI_SERVICE_URL = "http://localhost:8084"
EXPORT_SERVICE_URL = "http://localhost:8097"

def test_export_ai_prompt():
    """Test that AI generation metadata is included in exports."""
    print("=" * 70)
    print("Feature #368: Export AI prompt with diagram")
    print("=" * 70)

    try:
        # Step 1: Generate an AI diagram
        print("\n[Step 1] Generating AI diagram...")
        prompt = "Create a simple flowchart for user login process"

        generate_response = requests.post(
            f"{AI_SERVICE_URL}/api/ai/generate",
            json={
                "prompt": prompt,
                "diagram_type": "flowchart",
                "provider": "mock",
                "model": "gpt-4",
                "enable_quality_validation": True
            },
            timeout=10
        )

        if generate_response.status_code != 200:
            print(f"✗ AI generation failed: {generate_response.status_code}")
            print(f"  Response: {generate_response.text}")
            return False

        gen_data = generate_response.json()
        print(f"✓ AI diagram generated successfully")
        print(f"  Provider: {gen_data.get('provider')}")
        print(f"  Model: {gen_data.get('model')}")
        print(f"  Tokens used: {gen_data.get('tokens_used')}")
        print(f"  Quality score: {gen_data.get('quality_score')}")
        print(f"  Layout algorithm: {gen_data.get('layout_algorithm')}")

        # Store generation metadata
        generation_metadata = {
            "prompt": prompt,
            "provider": gen_data.get("provider"),
            "model": gen_data.get("model"),
            "tokens_used": gen_data.get("tokens_used"),
            "quality_score": gen_data.get("quality_score"),
            "layout_algorithm": gen_data.get("layout_algorithm"),
            "diagram_type": gen_data.get("diagram_type"),
            "timestamp": gen_data.get("timestamp")
        }

        # Step 2: Export as JSON (most likely to include metadata)
        print("\n[Step 2] Exporting diagram as JSON...")

        export_response = requests.post(
            f"{EXPORT_SERVICE_URL}/export/json",
            json={
                "diagram_id": "test-ai-diagram-001",
                "canvas_data": {
                    "mermaid_code": gen_data.get("mermaid_code"),
                    "ai_metadata": generation_metadata  # Try to pass metadata
                },
                "width": 1024,
                "height": 768,
                "scale": 1.0,
                "quality": "high",
                "background": "white",
                "format": "json"
            },
            timeout=10
        )

        if export_response.status_code != 200:
            print(f"✗ Export failed: {export_response.status_code}")
            print(f"  Response: {export_response.text}")
            return False

        # Step 3: Verify AI metadata in export
        print("\n[Step 3] Verifying AI metadata in export...")

        export_data = export_response.json()
        print(f"✓ Export completed successfully")

        # Check if AI metadata is present
        checks = []

        # Check for prompt in metadata
        has_prompt = False
        has_provider = False
        has_model = False
        has_tokens = False
        has_quality = False

        # Look for AI metadata in various places
        if "ai_metadata" in export_data:
            ai_meta = export_data["ai_metadata"]
            has_prompt = "prompt" in ai_meta or "original_prompt" in ai_meta
            has_provider = "provider" in ai_meta
            has_model = "model" in ai_meta
            has_tokens = "tokens_used" in ai_meta
            has_quality = "quality_score" in ai_meta
        elif "metadata" in export_data and "ai_generation" in export_data["metadata"]:
            ai_meta = export_data["metadata"]["ai_generation"]
            has_prompt = "prompt" in ai_meta or "original_prompt" in ai_meta
            has_provider = "provider" in ai_meta
            has_model = "model" in ai_meta
            has_tokens = "tokens_used" in ai_meta
            has_quality = "quality_score" in ai_meta
        elif "canvas_data" in export_data and "ai_metadata" in export_data["canvas_data"]:
            ai_meta = export_data["canvas_data"]["ai_metadata"]
            has_prompt = "prompt" in ai_meta
            has_provider = "provider" in ai_meta
            has_model = "model" in ai_meta
            has_tokens = "tokens_used" in ai_meta
            has_quality = "quality_score" in ai_meta

        # Print current state
        print(f"\n  Current export structure:")
        print(f"  - Has AI metadata section: {bool(has_prompt or has_provider)}")
        print(f"  - Has original prompt: {has_prompt}")
        print(f"  - Has provider info: {has_provider}")
        print(f"  - Has model info: {has_model}")
        print(f"  - Has token usage: {has_tokens}")
        print(f"  - Has quality score: {has_quality}")

        # Feature passes if ALL metadata is included
        if all([has_prompt, has_provider, has_model, has_tokens, has_quality]):
            print(f"\n✓ Feature #368: PASS")
            print(f"  All AI generation metadata is included in export")
            return True
        else:
            print(f"\n✗ Feature #368: FAIL")
            print(f"  Missing AI generation metadata in export")
            print(f"\n  Expected metadata to include:")
            print(f"    - Original prompt: {prompt}")
            print(f"    - Provider: {generation_metadata['provider']}")
            print(f"    - Model: {generation_metadata['model']}")
            print(f"    - Tokens used: {generation_metadata['tokens_used']}")
            print(f"    - Quality score: {generation_metadata['quality_score']}")
            print(f"\n  Actual export structure (keys):")
            print(f"    {json.dumps(list(export_data.keys()), indent=4)}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {e}")
        print(f"  Make sure services are running:")
        print(f"    - AI service on port 8084")
        print(f"    - Export service on port 8097")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_export_ai_prompt()
    sys.exit(0 if success else 1)
