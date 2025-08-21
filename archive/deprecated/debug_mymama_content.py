#!/usr/bin/env python3
"""
Debug script to see what's actually on the MyMama page
"""
import asyncio
import logging
from enhanced_browserbase_scraper import EnhancedBrowserBaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_mymama_content():
    """Debug what's actually on the MyMama page"""
    try:
        scraper = EnhancedBrowserBaseScraper()
        
        # Initialize browser
        await scraper.initialize_browser()
        await scraper.authenticate()
        
        # Navigate to target
        await scraper.page.goto(scraper.TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Get page content
        page_text = await scraper.page.inner_text('body')
        page_html = await scraper.page.content()
        
        print("="*50)
        print("PAGE TEXT CONTENT:")
        print("="*50)
        print(page_text[:2000])  # First 2000 chars
        print("="*50)
        
        # Save full content for analysis
        with open('debug_page_text.txt', 'w') as f:
            f.write(page_text)
        
        with open('debug_page_html.html', 'w') as f:
            f.write(page_html)
            
        print(f"Full content saved to debug_page_text.txt and debug_page_html.html")
        
        # Check for specific elements
        print("\nELEMENT ANALYSIS:")
        print("="*30)
        
        # Look for tables
        tables = await scraper.page.query_selector_all('table')
        print(f"Tables found: {len(tables)}")
        
        # Look for common content selectors
        selectors_to_check = [
            'main', '#content', '.content', '[role="main"]',
            'table', 'tr', 'td',
            '.forex', '.currency', '.alert', '.signal',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'div', 'span'
        ]
        
        for selector in selectors_to_check:
            try:
                elements = await scraper.page.query_selector_all(selector)
                if elements:
                    print(f"{selector}: {len(elements)} elements")
                    if len(elements) < 5:  # Show text for small number of elements
                        for i, elem in enumerate(elements):
                            text = await elem.inner_text()
                            if text.strip():
                                print(f"  {i+1}: {text.strip()[:100]}")
            except:
                pass
        
        await scraper.cleanup()
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_mymama_content())