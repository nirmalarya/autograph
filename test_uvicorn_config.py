#!/usr/bin/env python3
"""Test uvicorn Config with SSL context"""
import uvicorn.config
import inspect

# Check Config __init__ parameters
sig = inspect.signature(uvicorn.config.Config.__init__)
print("uvicorn.Config.__init__ parameters related to SSL:")
for param_name, param in sig.parameters.items():
    if 'ssl' in param_name.lower() or param_name == 'ssl':
        print(f"  {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'} = {param.default}")

print("\n" + "="*80)

# Check if Config has an ssl attribute
config_attrs = [attr for attr in dir(uvicorn.config.Config) if 'ssl' in attr.lower()]
print(f"Config attributes with 'ssl': {config_attrs}")
