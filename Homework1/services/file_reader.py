"""
File Reader Service - Convert files to Markdown using MarkItDown.
"""

import os
from markitdown import MarkItDown

MAX_CHARS = 15000

_converter = MarkItDown()


def read_file(file_path: str) -> dict:
    """Read a local file and convert its content to Markdown using MarkItDown."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: '{file_path}'")

    result = _converter.convert(file_path)
    content = result.text_content or ""

    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + f"\n\n... [truncated at {MAX_CHARS} chars]"

    return {
        "file_name": os.path.basename(file_path),
        "content": content,
    }
