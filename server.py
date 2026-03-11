"""
Test server for PA1: HTTP Client & Web Crawler.

Run this server locally, then point your crawler at http://localhost:8080.
It serves a small static site with pages, redirects, chunked responses,
and various edge cases so you can test your implementation offline.

Usage:
    python server.py [port]
    default port: 8080
"""

import socket
import sys
import threading

HOST = "0.0.0.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------

PAGES = {
    "/": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>Home</title></head>\n"
            "<body>\n"
            "<h1>Welcome to the Test Server</h1>\n"
            "<p>This is the home page.</p>\n"
            "<ul>\n"
            '  <li><a href="/about">About</a></li>\n'
            '  <li><a href="/links">Links Page</a></li>\n'
            '  <li><a href="/redirect">Redirect Test</a></li>\n'
            '  <li><a href="/chunked">Chunked Response</a></li>\n'
            '  <li><a href="/deep/page1">Deep Page 1</a></li>\n'
            "</ul>\n"
            "</body></html>\n"
        ),
    },
    "/about": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>About</title></head>\n"
            "<body>\n"
            "<h1>About Page</h1>\n"
            "<p>This page tests basic GET requests.</p>\n"
            '<p><a href="/">Back to Home</a></p>\n'
            '<p><a href="/contact">Contact Us</a></p>\n'
            "</body></html>\n"
        ),
    },
    "/contact": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>Contact</title></head>\n"
            "<body>\n"
            "<h1>Contact Page</h1>\n"
            "<p>Email: test@example.com</p>\n"
            '<p><a href="/">Home</a></p>\n'
            "</body></html>\n"
        ),
    },
    "/links": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>Links</title></head>\n"
            "<body>\n"
            "<h1>Many Links</h1>\n"
            "<ul>\n"
            '  <li><a href="/">Home</a></li>\n'
            '  <li><a href="/about">About</a></li>\n'
            '  <li><a href="/contact">Contact</a></li>\n'
            '  <li><a href="/deep/page1">Deep 1</a></li>\n'
            '  <li><a href="/deep/page2">Deep 2</a></li>\n'
            '  <li><a href="/deep/page3">Deep 3</a></li>\n'
            '  <li><a href="mailto:nope@example.com">Email (skip)</a></li>\n'
            '  <li><a href="javascript:void(0)">JS link (skip)</a></li>\n'
            "</ul>\n"
            "</body></html>\n"
        ),
    },
    "/deep/page1": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>Deep 1</title></head>\n"
            "<body>\n"
            "<h1>Deep Page 1</h1>\n"
            '<p><a href="/deep/page2">Next</a></p>\n'
            '<p><a href="/">Home</a></p>\n'
            "</body></html>\n"
        ),
    },
    "/deep/page2": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>Deep 2</title></head>\n"
            "<body>\n"
            "<h1>Deep Page 2</h1>\n"
            '<p><a href="/deep/page3">Next</a></p>\n'
            '<p><a href="/deep/page1">Previous</a></p>\n'
            "</body></html>\n"
        ),
    },
    "/deep/page3": {
        "status": "200 OK",
        "content_type": "text/html; charset=UTF-8",
        "body": (
            "<!DOCTYPE html>\n"
            "<html><head><title>Deep 3</title></head>\n"
            "<body>\n"
            "<h1>Deep Page 3 (last)</h1>\n"
            '<p><a href="/">Back to Home</a></p>\n'
            "</body></html>\n"
        ),
    },
    "/nothtml": {
        "status": "200 OK",
        "content_type": "application/json",
        "body": '{"message": "This is JSON, not HTML. Your crawler should skip it."}',
    },
}

REDIRECTS = {
    "/redirect": ("301 Moved Permanently", "/about"),
    "/old-home": ("302 Found", "/"),
    "/chain1": ("301 Moved Permanently", "/chain2"),
    "/chain2": ("302 Found", "/chain3"),
    "/chain3": ("301 Moved Permanently", "/about"),
}


def build_response(status, headers_dict, body_bytes):
    """Build a raw HTTP/1.1 response."""
    lines = [f"HTTP/1.1 {status}"]
    for key, value in headers_dict.items():
        lines.append(f"{key}: {value}")
    header_block = "\r\n".join(lines) + "\r\n\r\n"
    return header_block.encode("utf-8") + body_bytes


def build_chunked_body(text):
    """Encode text as chunked transfer encoding."""
    data = text.encode("utf-8")
    chunk_size = 64
    result = b""
    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        result += f"{len(chunk):x}\r\n".encode("utf-8")
        result += chunk + b"\r\n"
    result += b"0\r\n\r\n"
    return result


def handle_client(conn, addr):
    """Handle a single HTTP request."""
    try:
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = conn.recv(4096)
            if not chunk:
                return
            raw += chunk

        request_line = raw.split(b"\r\n")[0].decode("utf-8", errors="replace")
        parts = request_line.split(" ")
        if len(parts) < 2:
            return

        method = parts[0]
        path = parts[1]

        print(f"[{addr[0]}:{addr[1]}] {method} {path}")

        # Redirects
        if path in REDIRECTS:
            status, location = REDIRECTS[path]
            headers = {
                "Location": location,
                "Content-Length": "0",
                "Connection": "close",
            }
            conn.sendall(build_response(status, headers, b""))
            return

        # Chunked response test
        if path == "/chunked":
            body_text = (
                "<!DOCTYPE html>\n"
                "<html><head><title>Chunked</title></head>\n"
                "<body>\n"
                "<h1>Chunked Transfer Encoding Test</h1>\n"
                "<p>If you can read this, you decoded the chunks correctly.</p>\n"
                '<p><a href="/">Home</a></p>\n'
                "</body></html>\n"
            )
            chunked_body = build_chunked_body(body_text)
            headers = {
                "Content-Type": "text/html; charset=UTF-8",
                "Transfer-Encoding": "chunked",
                "Connection": "close",
            }
            conn.sendall(build_response("200 OK", headers, chunked_body))
            return

        # 404
        if path not in PAGES:
            body = b"<html><body><h1>404 Not Found</h1></body></html>"
            headers = {
                "Content-Type": "text/html; charset=UTF-8",
                "Content-Length": str(len(body)),
                "Connection": "close",
            }
            conn.sendall(build_response("404 Not Found", headers, body))
            return

        # Normal page
        page = PAGES[path]
        body = page["body"].encode("utf-8")
        headers = {
            "Content-Type": page["content_type"],
            "Content-Length": str(len(body)),
            "Connection": "close",
        }
        conn.sendall(build_response(page["status"], headers, body))

    except Exception as e:
        print(f"Error handling {addr}: {e}")
    finally:
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Test server running on http://localhost:{PORT}")
    print("Pages:")
    for path in PAGES:
        print(f"  http://localhost:{PORT}{path}")
    print("Redirects:")
    for path, (status, target) in REDIRECTS.items():
        print(f"  http://localhost:{PORT}{path} -> {status} -> {target}")
    print(f"  http://localhost:{PORT}/chunked -> chunked transfer encoding")
    print()

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
