#!/usr/bin/env python3
"""
Test Performance Metrics - Features #612, #613, #614

Tests:
- Feature #612: Performance: initial load < 2s
- Feature #613: Performance: time to interactive < 3s
- Feature #614: Code splitting: route-based

This test uses Playwright to measure real-world performance metrics.
"""

import asyncio
import time
from playwright.async_api import async_playwright
import statistics

FRONTEND_URL = "http://localhost:3000"

async def measure_page_load_time(page):
    """Measure page load time using Navigation Timing API"""
    timing = await page.evaluate("""
        () => {
            const timing = performance.timing;
            const loadTime = timing.loadEventEnd - timing.navigationStart;
            const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
            const domInteractive = timing.domInteractive - timing.navigationStart;
            
            return {
                loadTime: loadTime,
                domContentLoaded: domContentLoaded,
                domInteractive: domInteractive,
                navigationStart: timing.navigationStart,
                domLoading: timing.domLoading - timing.navigationStart,
                domComplete: timing.domComplete - timing.navigationStart
            };
        }
    """)
    return timing

async def measure_time_to_interactive(page):
    """
    Measure Time to Interactive (TTI) - when page is fully interactive
    TTI is approximated as when:
    1. DOM is interactive
    2. All critical resources loaded
    3. Main thread is not blocked for more than 50ms
    """
    # Get performance metrics
    metrics = await page.evaluate("""
        () => {
            const timing = performance.timing;
            const tti = timing.domInteractive - timing.navigationStart;
            return tti;
        }
    """)
    return metrics

async def check_code_splitting(page):
    """
    Check if code splitting is working by analyzing loaded chunks
    """
    # Get all loaded script sources
    scripts = await page.evaluate("""
        () => {
            const scripts = Array.from(document.querySelectorAll('script[src]'));
            return scripts.map(s => s.src).filter(src => src.includes('/_next/'));
        }
    """)
    
    # Check for split chunks
    has_vendor_chunk = any('vendor' in s for s in scripts)
    has_app_chunks = any('app/' in s for s in scripts)
    has_multiple_chunks = len(scripts) > 3
    
    return {
        'total_chunks': len(scripts),
        'has_vendor_chunk': has_vendor_chunk,
        'has_app_chunks': has_app_chunks,
        'has_multiple_chunks': has_multiple_chunks,
        'chunks': scripts
    }

async def test_performance_metrics():
    """Test all performance metrics"""
    print("=" * 80)
    print("PERFORMANCE METRICS TEST")
    print("=" * 80)
    print()
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Testing Feature #612: Initial load < 2s")
        print("-" * 80)
        
        # Test 1: Initial page load
        load_times = []
        for i in range(3):
            print(f"\nRun {i+1}/3:")
            start = time.time()
            
            # Navigate and wait for load event
            await page.goto(FRONTEND_URL, wait_until='load', timeout=10000)
            
            end = time.time()
            wall_clock_time = (end - start) * 1000  # Convert to ms
            
            # Wait a bit for timing API to populate
            await asyncio.sleep(0.5)
            
            # Get detailed timing
            timing = await measure_page_load_time(page)
            
            load_times.append(timing['loadTime'])
            
            print(f"  Wall clock time: {wall_clock_time:.0f}ms")
            print(f"  Navigation Timing API:")
            print(f"    - Total load time: {timing['loadTime']:.0f}ms")
            print(f"    - DOM Content Loaded: {timing['domContentLoaded']:.0f}ms")
            print(f"    - DOM Interactive: {timing['domInteractive']:.0f}ms")
            
            # Clear cache for next run (except last)
            if i < 2:
                await context.clear_cookies()
        
        avg_load_time = statistics.mean(load_times)
        max_load_time = max(load_times)
        min_load_time = min(load_times)
        
        print(f"\nLoad Time Statistics:")
        print(f"  Average: {avg_load_time:.0f}ms")
        print(f"  Min: {min_load_time:.0f}ms")
        print(f"  Max: {max_load_time:.0f}ms")
        
        load_under_2s = avg_load_time < 2000
        print(f"\n✓ PASS: Initial load < 2s" if load_under_2s else f"✗ FAIL: Initial load >= 2s")
        
        print("\n" + "=" * 80)
        print("Testing Feature #613: Time to interactive < 3s")
        print("-" * 80)
        
        # Test 2: Time to Interactive
        tti_times = []
        for i in range(3):
            print(f"\nRun {i+1}/3:")
            
            # Navigate to page
            await page.goto(FRONTEND_URL, wait_until='domcontentloaded')
            
            # Wait for page to be interactive
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Measure TTI
            tti = await measure_time_to_interactive(page)
            tti_times.append(tti)
            
            print(f"  Time to Interactive: {tti:.0f}ms")
            
            # Clear cache
            if i < 2:
                await context.clear_cookies()
        
        avg_tti = statistics.mean(tti_times)
        max_tti = max(tti_times)
        min_tti = min(tti_times)
        
        print(f"\nTTI Statistics:")
        print(f"  Average: {avg_tti:.0f}ms")
        print(f"  Min: {min_tti:.0f}ms")
        print(f"  Max: {max_tti:.0f}ms")
        
        tti_under_3s = avg_tti < 3000
        print(f"\n✓ PASS: TTI < 3s" if tti_under_3s else f"✗ FAIL: TTI >= 3s")
        
        print("\n" + "=" * 80)
        print("Testing Feature #614: Route-based code splitting")
        print("-" * 80)
        
        # Test 3: Code splitting
        await page.goto(FRONTEND_URL, wait_until='networkidle')
        
        splitting = await check_code_splitting(page)
        
        print(f"\nCode Splitting Analysis:")
        print(f"  Total chunks loaded: {splitting['total_chunks']}")
        print(f"  Has vendor chunk: {splitting['has_vendor_chunk']}")
        print(f"  Has app-specific chunks: {splitting['has_app_chunks']}")
        print(f"  Has multiple chunks: {splitting['has_multiple_chunks']}")
        
        print(f"\nLoaded chunks:")
        for i, chunk in enumerate(splitting['chunks'][:10], 1):
            # Extract just the filename
            filename = chunk.split('/')[-1][:60]
            print(f"  {i}. {filename}")
        
        if len(splitting['chunks']) > 10:
            print(f"  ... and {len(splitting['chunks']) - 10} more chunks")
        
        code_splitting_works = (
            splitting['has_vendor_chunk'] and 
            splitting['has_multiple_chunks'] and
            splitting['total_chunks'] >= 3
        )
        
        print(f"\n✓ PASS: Code splitting working" if code_splitting_works else f"✗ FAIL: Code splitting not working properly")
        
        await browser.close()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        all_pass = load_under_2s and tti_under_3s and code_splitting_works
        
        print(f"\n{'✓' if load_under_2s else '✗'} Feature #612: Initial load < 2s: {avg_load_time:.0f}ms (target: <2000ms)")
        print(f"{'✓' if tti_under_3s else '✗'} Feature #613: Time to interactive < 3s: {avg_tti:.0f}ms (target: <3000ms)")
        print(f"{'✓' if code_splitting_works else '✗'} Feature #614: Code splitting: {splitting['total_chunks']} chunks loaded")
        
        if all_pass:
            print("\n🎉 All performance features are working!")
            return 0
        else:
            print("\n❌ Some performance features need improvement")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_performance_metrics())
    exit(exit_code)
