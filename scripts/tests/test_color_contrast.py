#!/usr/bin/env python3
"""
Test color contrast ratios for WCAG AA compliance.

WCAG AA Requirements:
- Normal text (< 18pt): 4.5:1 contrast ratio minimum
- Large text (>= 18pt or >= 14pt bold): 3:1 contrast ratio minimum
- UI components and graphical objects: 3:1 contrast ratio minimum

This test verifies all color combinations in the AutoGraph v3 application.
"""

import re
import math
from typing import Tuple, List, Dict


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Convert HSL color to RGB."""
    s = s / 100
    l = l / 100
    
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    
    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    return (
        round((r + m) * 255),
        round((g + m) * 255),
        round((b + m) * 255)
    )


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance of an RGB color."""
    r, g, b = [x / 255 for x in rgb]
    
    # Convert to linear RGB
    def to_linear(c):
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    r_linear = to_linear(r)
    g_linear = to_linear(g)
    b_linear = to_linear(b)
    
    # Calculate luminance
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear


def contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """Calculate contrast ratio between two RGB colors."""
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def parse_hsl(hsl_str: str) -> Tuple[float, float, float]:
    """Parse HSL string from CSS variable format."""
    parts = hsl_str.strip().split()
    h = float(parts[0])
    s = float(parts[1].rstrip('%'))
    l = float(parts[2].rstrip('%'))
    return (h, s, l)


def check_wcag_aa(ratio: float, text_size: str = "normal") -> Tuple[bool, str]:
    """Check if contrast ratio meets WCAG AA standards."""
    if text_size == "large":
        threshold = 3.0
        level = "WCAG AA (Large Text)"
    else:
        threshold = 4.5
        level = "WCAG AA (Normal Text)"
    
    passes = ratio >= threshold
    return passes, level


def main():
    """Test all color combinations."""
    
    # Define color combinations from globals.css
    # Format: (name, foreground_hsl, background_hsl, text_size)
    light_mode_colors = [
        ("Body text", "222.2 84% 4.9%", "0 0% 100%", "normal"),
        ("Card text", "222.2 84% 4.9%", "0 0% 100%", "normal"),
        ("Primary button", "210 40% 98%", "222.2 47.4% 11.2%", "normal"),
        ("Secondary button", "222.2 47.4% 11.2%", "210 40% 96.1%", "normal"),
        ("Muted text", "215.4 16.3% 35%", "0 0% 100%", "normal"),  # Fixed: darkened from 46.9% to 35%
        ("Muted text on muted bg", "215.4 16.3% 35%", "210 40% 96.1%", "normal"),  # Fixed: darkened from 46.9% to 35%
        ("Link text (accessible)", "217.2 91.2% 45%", "0 0% 100%", "normal"),  # Fixed: darkened from 59.8% to 45%
        ("Success text (accessible)", "142.1 76.2% 28%", "0 0% 100%", "normal"),  # Fixed: darkened from 36.3% to 28%
        ("Error text (accessible)", "0 84.2% 48%", "0 0% 100%", "normal"),  # Fixed: darkened from 60.2% to 48%
        ("Placeholder text", "215.4 16.3% 35%", "0 0% 100%", "normal"),  # Fixed: darkened from 46.9% to 35%
    ]
    
    dark_mode_colors = [
        ("Body text", "210 40% 98%", "222.2 84% 4.9%", "normal"),
        ("Card text", "210 40% 98%", "222.2 84% 4.9%", "normal"),
        ("Primary button", "222.2 47.4% 11.2%", "210 40% 98%", "normal"),
        ("Secondary button", "210 40% 98%", "217.2 32.6% 17.5%", "normal"),
        ("Muted text", "215 20.2% 65.1%", "222.2 84% 4.9%", "normal"),
        ("Muted text on muted bg", "215 20.2% 65.1%", "217.2 32.6% 17.5%", "normal"),
        ("Link text (blue-400)", "213.1 93.9% 67.8%", "222.2 84% 4.9%", "normal"),  # Tailwind blue-400
        ("Success text", "142.1 70.6% 45.3%", "222.2 84% 4.9%", "normal"),  # Tailwind green-500
        ("Error text", "0 62.8% 30.6%", "210 40% 98%", "normal"),  # Destructive on light
    ]
    
    print("=" * 80)
    print("WCAG AA Color Contrast Test - AutoGraph v3")
    print("=" * 80)
    print()
    
    # Test light mode
    print("LIGHT MODE")
    print("-" * 80)
    failures = []
    for name, fg_hsl, bg_hsl, text_size in light_mode_colors:
        fg_rgb = hsl_to_rgb(*parse_hsl(fg_hsl))
        bg_rgb = hsl_to_rgb(*parse_hsl(bg_hsl))
        ratio = contrast_ratio(fg_rgb, bg_rgb)
        passes, level = check_wcag_aa(ratio, text_size)
        
        status = "✅ PASS" if passes else "❌ FAIL"
        print(f"{status} {name:30s} {ratio:5.2f}:1  ({level})")
        
        if not passes:
            failures.append({
                "mode": "light",
                "name": name,
                "ratio": ratio,
                "fg_hsl": fg_hsl,
                "bg_hsl": bg_hsl,
                "text_size": text_size
            })
    
    print()
    
    # Test dark mode
    print("DARK MODE")
    print("-" * 80)
    for name, fg_hsl, bg_hsl, text_size in dark_mode_colors:
        fg_rgb = hsl_to_rgb(*parse_hsl(fg_hsl))
        bg_rgb = hsl_to_rgb(*parse_hsl(bg_hsl))
        ratio = contrast_ratio(fg_rgb, bg_rgb)
        passes, level = check_wcag_aa(ratio, text_size)
        
        status = "✅ PASS" if passes else "❌ FAIL"
        print(f"{status} {name:30s} {ratio:5.2f}:1  ({level})")
        
        if not passes:
            failures.append({
                "mode": "dark",
                "name": name,
                "ratio": ratio,
                "fg_hsl": fg_hsl,
                "bg_hsl": bg_hsl,
                "text_size": text_size
            })
    
    print()
    print("=" * 80)
    
    if failures:
        print(f"FAILURES: {len(failures)} color combinations failed WCAG AA")
        print("=" * 80)
        print()
        print("RECOMMENDED FIXES:")
        print("-" * 80)
        for failure in failures:
            print(f"\n{failure['mode'].upper()} MODE - {failure['name']}")
            print(f"  Current ratio: {failure['ratio']:.2f}:1 (needs 4.5:1)")
            print(f"  Foreground: {failure['fg_hsl']}")
            print(f"  Background: {failure['bg_hsl']}")
            
            # Suggest fix
            if "muted" in failure['name'].lower():
                if failure['mode'] == "light":
                    print(f"  Suggested fix: Darken muted-foreground to 215.4 16.3% 35% (darker gray)")
                else:
                    print(f"  Suggested fix: Lighten muted-foreground to 215 20.2% 75% (lighter gray)")
    else:
        print("SUCCESS: All color combinations pass WCAG AA! ✅")
        print("=" * 80)
    
    print()
    return len(failures) == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
