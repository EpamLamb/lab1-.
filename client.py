"""
PA1: HTTP Client & Web Crawler
Course: Computer Networks — University of Athens, Spring 2026

Fill in the TODO sections to complete your implementation.
The helper code from the lab is provided — use it as a starting point.

Usage:
    python client.py <url> [max_pages] [-v]

Example:
    python client.py http://localhost:8080 10
    python client.py http://localhost:8080 10 -v
"""

import socket
import sys
import re
from urllib.parse import urlparse, urljoin
from collections import deque


# ===================================================================
# Step 1: URL Parsing (provided from lab)
# ===================================================================

def parse_url(url):
    """Parse a URL into (host, port, path)."""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return host, port, path


# ===================================================================
# Step 2: HTTP GET Request (provided from lab)
# ===================================================================

def http_get(host, port, path):
    """Send an HTTP GET request and return the raw response bytes."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: UoA-Crawler/1.0\r\n"
        f"Accept: text/html\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )
    sock.sendall(request.encode("utf-8"))

    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk

    sock.close()
    return response


# ===================================================================
# Step 3: Parse HTTP Response (provided from lab)
# ===================================================================

def parse_response(raw):
    """Parse raw HTTP response into (status_code, reason, headers, body).

    Returns:
        status_code: int (e.g. 200, 301, 404)
        reason: str (e.g. "OK", "Moved Permanently")
        headers: dict with lowercase keys
        body: bytes
    """
    header_bytes, _, body = raw.partition(b"\r\n\r\n")
    header_text = header_bytes.decode("utf-8", errors="replace")
    lines = header_text.split("\r\n")

    # Parse status line: "HTTP/1.1 200 OK"
    parts = lines[0].split(" ", 2)
    status_code = int(parts[1])
    reason = parts[2] if len(parts) > 2 else ""

    # Parse headers into a dictionary
    headers = {}
    for line in lines[1:]:
        key, _, value = line.partition(": ")
        headers[key.lower()] = value.strip()

    return status_code, reason, headers, body


# ===================================================================
# Step 4: Decode Chunked Transfer Encoding
# ===================================================================

def decode_chunked(body):
    """Decode a chunked transfer-encoded body.

    Chunked format:
        <chunk-size-in-hex>\r\n
        <chunk-data>\r\n
        ...
        0\r\n
        \r\n

    Args:
        body: bytes — the raw chunked body

    Returns:
        bytes — the decoded body
    """
    # TODO: Implement chunked decoding.
    #
    # Hints from the lab:
    #   - Each chunk starts with its size in hexadecimal, followed by \r\n
    #   - Then the chunk data, followed by \r\n
    #   - A chunk of size 0 signals the end
    #   - Use int(size_line, 16) to convert hex to int
    #
    # Example:
    #   b"1a\r\n<26 bytes of data>\r\n0\r\n\r\n"
    def decode_chunked(body):
    decoded = b""
    while body:
        size_line, _, body = body.partition(b"\r\n")
        chunk_size = int(size_line.strip(), 16)
        if chunk_size == 0:
            break
        decoded += body[:chunk_size]
        body = body[chunk_size + 2:]  # skip CRLF
    return decoded

    raise NotImplementedError("TODO: implement decode_chunked")


# ===================================================================
# Step 5: Fetch a URL (following redirects)
# ===================================================================

def fetch(url, max_redirects=5):
    """Fetch a URL, following up to max_redirects redirects.

    Args:
        url: str — the URL to fetch
        max_redirects: int — maximum number of redirects to follow

    Returns:
        (final_url, status_code, reason, headers, body)

    Raises:
        Exception if too many redirects
    """
    # TODO: Implement fetch with redirect handling.
    #
    # Hints from the lab:
    #   1. Loop up to max_redirects times
    #   2. Call parse_url() to get host, port, path
    #   3. Call http_get() to get the raw response
    #   4. Call parse_response() to parse it
    #   5. If status is 301 or 302:
    #      - Read the "location" header
    #      - Use urljoin(url, location) to handle relative redirects
    #      - Update url and continue the loop
    #   6. If status is not a redirect:
    #      - Check if Transfer-Encoding is chunked; if so, decode the body
    #      - Return the result
    #   7. If the loop ends, raise an exception
    from urllib.parse import urljoin

def fetch(url, max_redirects=5):
    for _ in range(max_redirects):
        host, port, path = parse_url(url)
        raw = http_get(host, port, path)
        status, headers, body = parse_response(raw)
        
        if status in (301, 302, 303, 307, 308):
            location = headers.get("location", "")
            url = urljoin(url, location)
            print(f"Redirect {status} -> {url}")
            continue
        
        return status, headers, body
    
    raise Exception("Too many redirects")
    

    raise NotImplementedError("TODO: implement fetch")


# ===================================================================
# Step 6: Extract Links from HTML
# ===================================================================

def extract_links(html, base_url):
    """Extract all href links from HTML and resolve them to absolute URLs.

    Args:
        html: str — the HTML content
        base_url: str — the URL of the page (for resolving relative links)

    Returns:
        list of str — absolute HTTP URLs found in the page
    """
    # TODO: Implement link extraction.
    #
    # Hints from the lab:
    #   - Use re.findall() with pattern: r'href=["\']([^"\']+)["\']'
    #   - Use urljoin(base_url, link) to convert relative to absolute
    #   - Filter: only keep links starting with "http"
    #   - Skip mailto:, javascript:, etc.
    import re

def extract_links(html, base_url):
    pattern = r'href=["\']([^"\']+)["\']'
    raw_links = re.findall(pattern, html)
    
    links = []
    for link in raw_links:
        absolute = urljoin(base_url, link)
        if absolute.startswith("http"):
            links.append(absolute)
    
    return links

    raise NotImplementedError("TODO: implement extract_links")


# ===================================================================
# Step 7: BFS Web Crawler
# ===================================================================

def crawl(start_url, max_pages=10, verbose=False):
    """Crawl starting from start_url using BFS.

    Visit up to max_pages unique pages. For each page, print:
        [N] <url> -> <status_code> <reason> (<body_size> bytes)
            Found <M> links

    If verbose is True, also print each discovered link:
            -> <link_url>

    For redirects, print:
        [N] <url> -> <status_code> -> <redirect_url>

    At the end, print:
        Crawled <N> pages, found <M> unique links.

    Args:
        start_url: str — the starting URL
        max_pages: int — maximum pages to visit
        verbose: bool — if True, print each link found
    """
    # TODO: Implement the BFS crawler.
    #
    # Hints from the lab:
    #   1. Use a set() for visited URLs
    #   2. Use collections.deque() as the BFS queue
    #   3. While the queue is not empty and len(visited) < max_pages:
    #      a. Pop a URL from the queue
    #      b. Skip if already visited
    #      c. Add to visited
    #      d. Call fetch() — handle exceptions gracefully
    #      e. Check Content-Type: skip non-HTML responses
    #      f. Decode the body and call extract_links()
    #      g. If verbose, print each link
    #      h. Add new links to the queue
    #   4. Print the summary at the end
    from collections import deque

def crawl(start_url, max_pages=10):
    visited = set()
    queue = deque([start_url])
    
    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        print(f"Crawling: {url}")
        visited.add(url)
        
        try:
            status, headers, body = fetch(url)
            if status != 200:
                continue
            content_type = headers.get("content-type", "")
            if "text/html" not in content_type:
                continue
            html = body.decode("utf-8", errors="replace")
            for link in extract_links(html, url):
                if link not in visited:
                    queue.append(link)
        except Exception as e:
            print(f"Error crawling {url}: {e}")
    
    return visited

    raise NotImplementedError("TODO: implement crawl")


# ===================================================================
# Main
# ===================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <url> [max_pages] [-v]")
        sys.exit(1)

    verbose = "-v" in sys.argv
    args = [a for a in sys.argv[1:] if a != "-v"]

    start_url = args[0]
    max_pages = int(args[1]) if len(args) > 1 else 10

    crawl(start_url, max_pages, verbose=verbose)
