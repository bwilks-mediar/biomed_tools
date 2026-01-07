# /utils.py

import os
import re
import sys
import json
from loguru import logger
from playwright.async_api import Request, Response
from . import config

def setup_logging(debug: bool):
    """Configures Loguru to log to console and a rotating file."""
    logger.remove()
    
    # Use the 'debug' parameter to determine the log level
    log_level = "DEBUG" if debug else "INFO"
    
    logger.add(
        sys.stderr, level=log_level, colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    logger.add(
        config.MAIN_LOG_FILE, rotation="5 MB", retention="7 days", level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    logger.info("Logging configured.")
    
    # Use the 'debug' parameter here as well
    if debug:
        logger.warning("DEBUG mode is ON. Verbose logging and network tracing are active.")
        if os.path.exists(config.NETWORK_TRACE_FILE):
            os.remove(config.NETWORK_TRACE_FILE)


def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be a valid filename."""
    if not name: return "untitled_article"
    name = name.replace(' ', '_')
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:150]

# --- Network Logging Handlers (for DEBUG_MODE) ---
async def log_request(request: Request):
    post_data_str = ""
    if request.method.upper() == "POST":
        try:
            # Try to access post_data safely
            body = request.post_data
            if body:
                try:
                    # First, try to parse the post data as JSON
                    post_data_json = request.post_data_json
                    post_data_str = f"\n  POST DATA (JSON): {json.dumps(post_data_json, indent=2)}"
                except Exception:
                    # If it fails, it's likely form-data or something else. Log as raw text.
                    post_data_str = f"\n  POST DATA (TEXT): {body}"
        except Exception:
            # Accessing request.post_data can fail if it's binary/gzip
            post_data_str = "\n  POST DATA: (Binary/Compressed or could not decode)"

    log_message = (
        f"-> REQ: {request.method} {request.url}\n"
        f"   HEADERS: {json.dumps(await request.all_headers(), indent=2)}{post_data_str}\n"
        f"------------------------------------------------------------------"
    )
    # Use a try-except block here as well for file I/O safety
    try:
        with open(config.NETWORK_TRACE_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    except Exception as e:
        logger.error(f"Failed to write to network trace file: {e}")


async def log_response(response: Response):
    # It's good practice to also wrap the response logger in a try-except
    try:
        log_message = (
            f"<- RES: {response.status} {response.status_text} FOR {response.request.method} {response.url}\n"
            f"   HEADERS: {json.dumps(await response.all_headers(), indent=2)}\n"
            f"=================================================================="
        )
        with open(config.NETWORK_TRACE_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    except Exception as e:
        logger.error(f"Failed to write to network trace file: {e}")
