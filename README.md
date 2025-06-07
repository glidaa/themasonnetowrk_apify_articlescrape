# Iframe Compatibility Processor

An Apify Actor that scrapes HTML content from URLs and processes it to make it iframe-compatible by removing frame-busting code and restrictive meta tags.

## What it does

This Actor takes a URL, fetches its HTML content, analyzes it for iframe-blocking elements, and processes the content to make it embeddable in iframes. It returns:

- The processed HTML content
- A boolean indicating if the content is now iframe-compatible
- Information about what modifications were made
- Details about the original frame-busting patterns found

## Features

- **Frame-busting Detection**: Identifies common JavaScript patterns that prevent iframe embedding
- **Meta Tag Processing**: Removes or modifies X-Frame-Options and CSP frame-ancestors restrictions
- **JavaScript Sanitization**: Comments out or removes frame-busting JavaScript code
- **Compatibility Assessment**: Evaluates both original and processed content for iframe compatibility
- **Detailed Reporting**: Provides comprehensive information about modifications made

## Input

The Actor expects a simple input with a single URL:

```json
{
  "url": "https://example.com"
}
```

## Output

The Actor returns detailed information about the processing:

```json
{
  "url": "https://example.com",
  "html_content": "<html>...</html>",
  "iframe_compatible": true,
  "original_blocked": true,
  "modifications_made": [
    "Removed X-Frame-Options meta tag",
    "Removed frame-busting pattern: if\\s*\\(\\s*window\\s*!==?\\s*window\\.top\\s*\\)"
  ],
  "original_frame_busting_patterns": [
    "if\\s*\\(\\s*window\\s*!==?\\s*window\\.top\\s*\\)"
  ]
}
```

## Frame-busting Patterns Detected

The Actor detects and removes common frame-busting patterns including:

- `if (window !== window.top)`
- `if (self !== top)`
- `if (parent !== window)`
- `window.top.location = window.location`
- `parent.location = self.location`
- `top.location = location`
- `if (window.frameElement)`
- `top.location.replace()`
- And many more...

## Meta Tag Processing

The Actor handles:

- **X-Frame-Options**: Removes meta tags with `http-equiv="X-Frame-Options"`
- **Content Security Policy**: Removes or modifies CSP directives containing `frame-ancestors`

## Local Development and Testing

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Local Testing

Use the included test script to test the Actor locally:

```bash
# Edit test_local.py to set your target URL
python test_local.py
```

Or test directly with Python:

```python
import asyncio
from src.main import main

# Set up test environment
# ... (see test_local.py for complete example)
```

### Building and Running with Apify CLI

```bash
# Install Apify CLI
npm -g install apify-cli

# Login to Apify
apify login

# Build and run locally
apify run

# Deploy to Apify platform
apify push
```

## Use Cases

- **Web Content Integration**: Make third-party websites embeddable in your applications
- **Security Research**: Analyze frame-busting implementations
- **Content Management**: Process content for safe iframe embedding
- **Educational Tools**: Create embeddable versions of educational content

## Technical Implementation

Built with:

- **[Apify SDK](https://docs.apify.com/sdk/python/)** - For Actor framework and data handling
- **[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)** - For HTML parsing and manipulation
- **[HTTPX](https://www.python-httpx.org)** - For asynchronous HTTP requests
- **Regular Expressions** - For pattern detection and content modification

## Limitations

- Cannot bypass server-side frame restrictions (HTTP headers)
- May not handle all possible frame-busting implementations
- Processed content may have altered functionality if frame-busting was integral to the site's operation
- Cannot process content requiring authentication or complex JavaScript rendering

## Resources

- [Apify Platform documentation](https://docs.apify.com/platform)
- [Apify SDK for Python documentation](https://docs.apify.com/sdk/python)
- [X-Frame-Options Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)
- [Content Security Policy frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors)
- [Join our developer community on Discord](https://discord.com/invite/jyEM2PRvMU)

## License

This project is licensed under the Apache 2.0 License.
