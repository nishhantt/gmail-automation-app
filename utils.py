import os
from datetime import datetime
import re

def log_action(text, log_file="logs/actions.log"):
    """Log actions or dry-run results to a file."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)  # make sure folder exists
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")

def extract_email_address(raw_from):
    """Extract only the email address from the 'From' header."""
    if not raw_from:
        return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+', raw_from)
    return match.group(0) if match else raw_from
