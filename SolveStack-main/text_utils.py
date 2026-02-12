
import re
import html
import unicodedata

def clean_text(text: str) -> str:
    """
    Robustly clean text by:
    1. Decoding HTML entities (e.g., &#x27; -> ', &amp; -> &)
    2. Normalizing unicode characters (e.g., full-width punctuation to standard)
    3. Removing URLs
    4. Removing HTML tags
    5. Normalizing whitespace
    6. Stripping leading/trailing spaces
    """
    if not text:
        return ""

    # 1. Decode HTML entities multiple times (in case of double encoding)
    # Using html.unescape which is robust
    text = html.unescape(text)
    
    # 2. Normalize Unicode characters (NFKC handles full-width characters)
    # This converts things like the full-width colon "：" to standard ":"
    text = unicodedata.normalize('NFKC', text)

    # 3. Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # 4. Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 5. Normalize whitespace (including tabs, newlines, and non-breaking spaces)
    # Replace \xa0 (non-breaking space) and other variants with standard space
    text = re.sub(r'\s+', ' ', text)
    
    # 6. Final strip
    return text.strip()

def is_mostly_english(text: str, threshold: float = 0.8) -> bool:
    """
    Heuristic to check if a string is mostly English based on Latin characters and common English punctuation.
    Useful for filtering out purely Chinese/Russian/etc. content if desired.
    """
    if not text:
        return True
    
    # Count Latin characters, numbers, and basic punctuation
    total_chars = len(text)
    latin_chars = len(re.findall(r'[a-zA-Z0-9\s.,!?;:\'\"()\[\]\-]', text))
    
    return (latin_chars / total_chars) >= threshold if total_chars > 0 else True

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Safely truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
