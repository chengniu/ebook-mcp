import hashlib
import os
import tempfile
import urllib.request
from urllib.parse import urlparse

def get_pdf_local_path(url: str) -> str:
    """
    Given a PDF URL, deterministically derive a local filename from the URL,
    check the system temp directory, download if missing, and return the full path.

    Returns:
        str: Full path to the local PDF file in the system temp directory.

    Raises:
        ValueError: If the URL is invalid or not HTTP/HTTPS.
        URLError/HTTPError/OSError: If download or file operations fail.
    """
    # Basic URL validation
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")

    # Deterministic filename from URL (SHA-256 hex) with .pdf extension
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    filename = f"{digest}.pdf"

    # System temp directory
    tmpdir = tempfile.gettempdir()
    fullpath = os.path.join(tmpdir, filename)

    if os.path.exists(fullpath):
        return fullpath

    # Download to a temporary file first, then atomically move
    tmppath = fullpath + ".part"
    try:
        with urllib.request.urlopen(url) as resp, open(tmppath, "wb") as out:
            # Optionally, you could verify Content-Type is 'application/pdf'
            # ctype = resp.headers.get_content_type()
            # if ctype != "application/pdf":
            #     raise ValueError(f"Unexpected Content-Type: {ctype!r}")
            chunk = resp.read(8192)
            while chunk:
                out.write(chunk)
                chunk = resp.read(8192)
        os.replace(tmppath, fullpath)  # atomic on most platforms
    finally:
        # Clean up a stray .part file if something went wrong
        if os.path.exists(tmppath) and not os.path.exists(fullpath):
            try:
                os.remove(tmppath)
            except OSError:
                pass

    return fullpath
