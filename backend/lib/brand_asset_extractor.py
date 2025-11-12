"""
Brand Asset Extractor
Extracts colors, fonts, and visual elements from brand guidelines
"""
import re
from typing import List, Dict, Optional
from pathlib import Path

def extract_hex_colors(text: str) -> List[str]:
    """
    Extract hex color codes from text.
    Returns list of unique hex codes.
    """
    # Match hex colors with # prefix (3 or 6 digits)
    hex_pattern = r'#(?:[0-9a-fA-F]{3}){1,2}\b'
    colors = re.findall(hex_pattern, text, re.IGNORECASE)

    # Normalize to 6-digit format and uppercase
    normalized = []
    for color in colors:
        if len(color) == 4:  # #RGB -> #RRGGBB
            color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
        normalized.append(color.upper())

    # Return unique colors, preserving order
    seen = set()
    unique_colors = []
    for color in normalized:
        if color not in seen:
            seen.add(color)
            unique_colors.append(color)

    return unique_colors

def extract_rgb_colors(text: str) -> List[str]:
    """
    Extract RGB color codes and convert to hex.
    Matches patterns like: rgb(255, 0, 0) or RGB: 255, 0, 0
    """
    # Match RGB patterns
    rgb_pattern = r'rgb\s*\(?\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)?'
    matches = re.findall(rgb_pattern, text, re.IGNORECASE)

    hex_colors = []
    for r, g, b in matches:
        r, g, b = int(r), int(g), int(b)
        if all(0 <= val <= 255 for val in [r, g, b]):
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            hex_colors.append(hex_color)

    return hex_colors

def extract_fonts(text: str) -> List[str]:
    """
    Extract font family names from text.
    Looks for common patterns in brand guidelines.
    """
    # Common font-related keywords
    font_keywords = [
        r'font[:\s-]*([A-Z][a-zA-Z\s]+)',
        r'typeface[:\s-]*([A-Z][a-zA-Z\s]+)',
        r'typography[:\s-]*([A-Z][a-zA-Z\s]+)',
        r'font[- ]family[:\s]*([A-Z][a-zA-Z\s]+)',
    ]

    fonts = []
    for pattern in font_keywords:
        matches = re.findall(pattern, text, re.IGNORECASE)
        fonts.extend(matches)

    # Clean up font names
    cleaned_fonts = []
    for font in fonts:
        # Remove trailing words that aren't part of font name
        font = font.strip()
        # Remove common suffixes
        font = re.sub(r'\s+(bold|italic|regular|light|medium|thin|black|heavy)$', '', font, flags=re.IGNORECASE)
        # Remove trailing punctuation
        font = font.rstrip('.,;:')
        if len(font) > 2:  # Minimum length check
            cleaned_fonts.append(font.title())

    # Return unique fonts
    seen = set()
    unique_fonts = []
    for font in cleaned_fonts:
        if font not in seen and font.lower() not in ['font', 'typeface', 'the', 'and']:
            seen.add(font)
            unique_fonts.append(font)

    return unique_fonts

def extract_brand_assets(text: str) -> Dict[str, any]:
    """
    Extract all brand assets from text content.

    Args:
        text: Text content from brand guidelines (PDF, doc, etc.)

    Returns:
        Dict with colors, fonts, primary_color, secondary_color
    """
    # Extract colors
    hex_colors = extract_hex_colors(text)
    rgb_colors = extract_rgb_colors(text)
    all_colors = hex_colors + rgb_colors

    # Remove duplicates while preserving order
    seen = set()
    unique_colors = []
    for color in all_colors:
        if color not in seen:
            seen.add(color)
            unique_colors.append(color)

    # Extract fonts
    fonts = extract_fonts(text)

    # Determine primary and secondary colors
    # Primary is usually the first prominent color mentioned
    primary_color = unique_colors[0] if unique_colors else None
    secondary_color = unique_colors[1] if len(unique_colors) > 1 else None

    return {
        'brand_colors': unique_colors,
        'brand_fonts': fonts,
        'primary_color': primary_color,
        'secondary_color': secondary_color
    }

def find_logo_file(directory: Path, category: str = 'logos') -> Optional[str]:
    """
    Find the first logo file in the brand assets directory (local or GCS).

    NOTE: This function is now primarily for backwards compatibility.
    New uploads store logos directly as GCS URLs in the database.

    Args:
        directory: Path to brand_voice_assets directory
        category: Subdirectory to search (default: 'logos')

    Returns:
        Relative path to logo file, or None if not found
    """
    logo_dir = directory / category
    if not logo_dir.exists():
        return None

    # Common logo file extensions
    logo_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.pdf']

    for ext in logo_extensions:
        logo_files = list(logo_dir.glob(f'*{ext}'))
        if logo_files:
            # Return path relative to backend directory
            return f"brand_voice_assets/{category}/{logo_files[0].name}"

    return None


def find_logo_from_database(conn) -> Optional[str]:
    """
    Find logo URL from brand_voice_assets database.
    Checks for GCS URLs first (persistent), then local paths (legacy).

    Args:
        conn: Database connection

    Returns:
        Logo URL (GCS or local path), or None if not found
    """
    try:
        cur = conn.cursor()

        # Look for logo files in database (GCS URLs preferred)
        cur.execute("""
            SELECT file_path FROM brand_voice_assets
            WHERE category IN ('logos', 'guidelines')
            AND (
                file_type IN ('png', 'jpg', 'jpeg', 'svg')
                OR filename ILIKE '%.png'
                OR filename ILIKE '%.jpg'
                OR filename ILIKE '%.jpeg'
                OR filename ILIKE '%.svg'
            )
            ORDER BY
                CASE WHEN file_path LIKE 'https://storage.googleapis.com%' THEN 0 ELSE 1 END,
                uploaded_at DESC
            LIMIT 1
        """)

        result = cur.fetchone()
        cur.close()

        if result:
            return result['file_path']

        return None

    except Exception as e:
        print(f"Error finding logo from database: {e}")
        return None
