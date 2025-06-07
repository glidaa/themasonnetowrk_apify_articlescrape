"""Module defines the main entry point for the Apify Actor.

This Actor scrapes HTML content from a URL, analyzes iframe compatibility,
and processes the content to make it iframe-friendly by removing frame-busting code.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

from apify import Actor
from bs4 import BeautifulSoup, Comment
from httpx import AsyncClient


def detect_frame_busting_patterns(html_content: str) -> List[str]:
    """Detect common frame-busting patterns in HTML/JavaScript content."""
    patterns = [
        r'if\s*\(\s*window\s*!==?\s*window\.top\s*\)',
        r'if\s*\(\s*self\s*!==?\s*top\s*\)',
        r'if\s*\(\s*parent\s*!==?\s*window\s*\)',
        r'window\.top\.location\s*=\s*window\.location',
        r'parent\.location\s*=\s*self\.location',
        r'top\.location\s*=\s*location',
        r'window\.top\.location\.href\s*=\s*window\.location\.href',
        r'if\s*\(\s*top\s*!==?\s*self\s*\)',
        r'if\s*\(\s*window\.frameElement\s*\)',
        r'if\s*\(\s*window\.parent\s*!==?\s*window\s*\)',
        r'top\.location\.replace\(',
        r'window\.top\.location\.replace\(',
        r'break\s*out\s*of\s*frame',
        r'framekiller',
        r'framebreaker',
    ]
    
    found_patterns = []
    for pattern in patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            found_patterns.append(pattern)
    
    return found_patterns


def sanitize_javascript(soup: BeautifulSoup) -> List[str]:
    """Remove or comment out frame-busting JavaScript code."""
    modifications = []
    
    # Find all script tags
    script_tags = soup.find_all('script')
    
    for script in script_tags:
        if script.string:
            original_content = script.string
            modified_content = original_content
            
            # Patterns to remove or neutralize
            frame_busting_patterns = [
                (r'if\s*\(\s*window\s*!==?\s*window\.top\s*\)[^}]*}', '// Frame busting code removed'),
                (r'if\s*\(\s*self\s*!==?\s*top\s*\)[^}]*}', '// Frame busting code removed'),
                (r'if\s*\(\s*parent\s*!==?\s*window\s*\)[^}]*}', '// Frame busting code removed'),
                (r'window\.top\.location\s*=\s*[^;]*;', '// Frame busting code removed'),
                (r'parent\.location\s*=\s*[^;]*;', '// Frame busting code removed'),
                (r'top\.location\s*=\s*[^;]*;', '// Frame busting code removed'),
                (r'if\s*\(\s*top\s*!==?\s*self\s*\)[^}]*}', '// Frame busting code removed'),
                (r'if\s*\(\s*window\.frameElement\s*\)[^}]*}', '// Frame busting code removed'),
                (r'if\s*\(\s*window\.parent\s*!==?\s*window\s*\)[^}]*}', '// Frame busting code removed'),
                (r'top\.location\.replace\([^)]*\);?', '// Frame busting code removed'),
                (r'window\.top\.location\.replace\([^)]*\);?', '// Frame busting code removed'),
            ]
            
            for pattern, replacement in frame_busting_patterns:
                if re.search(pattern, modified_content, re.IGNORECASE | re.DOTALL):
                    modified_content = re.sub(pattern, replacement, modified_content, flags=re.IGNORECASE | re.DOTALL)
                    modifications.append(f"Removed frame-busting pattern: {pattern}")
            
            # Update script content if modified
            if modified_content != original_content:
                script.string = modified_content
    
    return modifications


def clean_meta_tags(soup: BeautifulSoup) -> List[str]:
    """Remove or modify meta tags that prevent iframe embedding."""
    modifications = []
    
    # Find all meta tags
    meta_tags = soup.find_all('meta')
    
    for meta in meta_tags:
        # Check for X-Frame-Options
        if meta.get('http-equiv', '').lower() == 'x-frame-options':
            meta.decompose()
            modifications.append("Removed X-Frame-Options meta tag")
        
        # Check for Content Security Policy with frame-ancestors
        elif meta.get('http-equiv', '').lower() == 'content-security-policy':
            content = meta.get('content', '')
            if 'frame-ancestors' in content.lower():
                # Remove frame-ancestors directive or the entire CSP if it's the only directive
                new_content = re.sub(r'frame-ancestors[^;]*;?', '', content, flags=re.IGNORECASE)
                new_content = re.sub(r';\s*;', ';', new_content)  # Clean up double semicolons
                new_content = new_content.strip('; ')
                
                if new_content:
                    meta['content'] = new_content
                    modifications.append("Modified CSP meta tag to remove frame-ancestors")
                else:
                    meta.decompose()
                    modifications.append("Removed CSP meta tag")
    
    return modifications


def assess_iframe_compatibility(html_content: str) -> bool:
    """Assess if the HTML content is now compatible with iframe embedding."""
    # Check for remaining frame-busting patterns
    remaining_patterns = detect_frame_busting_patterns(html_content)
    
    # Check for problematic meta tags
    soup = BeautifulSoup(html_content, 'html.parser')
    meta_tags = soup.find_all('meta')
    
    for meta in meta_tags:
        if meta.get('http-equiv', '').lower() == 'x-frame-options':
            return False
        if meta.get('http-equiv', '').lower() == 'content-security-policy':
            content = meta.get('content', '')
            if 'frame-ancestors' in content.lower() and "'none'" in content.lower():
                return False
    
    # If no problematic patterns found, it should be iframe compatible
    return len(remaining_patterns) == 0


async def main() -> None:
    """Main entry point for the Apify Actor that processes URLs for iframe compatibility."""
    async with Actor:
        # Get Actor input
        actor_input = await Actor.get_input() or {}
        url = actor_input.get('url')
        
        if not url:
            Actor.log.error('No URL provided in Actor input')
            await Actor.exit()
        
        Actor.log.info(f'Processing URL for iframe compatibility: {url}')
        
        try:
            # Fetch the HTML content
            async with AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                original_html = response.text
                
                # Check original iframe compatibility
                original_blocked = not assess_iframe_compatibility(original_html)
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(original_html, 'html.parser')
                
                # Apply modifications
                all_modifications = []
                
                # Clean JavaScript
                js_modifications = sanitize_javascript(soup)
                all_modifications.extend(js_modifications)
                
                # Clean meta tags
                meta_modifications = clean_meta_tags(soup)
                all_modifications.extend(meta_modifications)
                
                # Get processed HTML
                processed_html = str(soup)
                
                # Assess final compatibility
                iframe_compatible = assess_iframe_compatibility(processed_html)
                
                # Prepare result
                result = {
                    'url': url,
                    'html_content': processed_html,
                    'iframe_compatible': iframe_compatible,
                    'original_blocked': original_blocked,
                    'modifications_made': all_modifications,
                    'original_frame_busting_patterns': detect_frame_busting_patterns(original_html)
                }
                
                Actor.log.info(f'Processing complete. Originally blocked: {original_blocked}, Now compatible: {iframe_compatible}')
                Actor.log.info(f'Modifications made: {len(all_modifications)}')
                
                # Store the result
                await Actor.push_data(result)
                
        except Exception as e:
            Actor.log.exception(f'Error processing URL {url}: {str(e)}')
            
            # Store error result
            error_result = {
                'url': url,
                'error': str(e),
                'html_content': None,
                'iframe_compatible': False,
                'original_blocked': True,
                'modifications_made': [],
                'original_frame_busting_patterns': []
            }
            
            await Actor.push_data(error_result)
