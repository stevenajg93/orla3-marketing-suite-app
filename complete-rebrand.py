#!/usr/bin/env python3
"""
Complete ORLA³ Rebranding Script
Removes ALL emojis and applies cobalt/royal/gold brand colors across entire app
"""

import os
import re
from pathlib import Path

# Comprehensive color replacements
COLOR_REPLACEMENTS = [
    # Background gradients
    ('via-purple-900', 'via-royal-800'),
    ('via-purple-800', 'via-royal-700'),
    ('from-slate-900 via-purple-900 to-slate-900', 'from-slate-900 via-royal-800 to-black'),
    ('from-slate-900 via-purple-800 to-slate-900', 'from-slate-900 via-royal-700 to-black'),

    # Text gradients
    ('from-blue-400 to-purple-400', 'from-cobalt to-gold'),
    ('from-purple-400 to-pink-400', 'from-cobalt to-gold-intense'),
    ('from-pink-500 to-purple-500', 'from-gold-intense to-cobalt'),

    # Button gradients
    ('from-blue-600 to-purple-600', 'from-cobalt to-royal'),
    ('from-blue-700 to-purple-700', 'from-cobalt-600 to-royal-600'),
    ('from-purple-600 to-pink-600', 'from-cobalt to-gold-intense'),
    ('from-purple-700 to-pink-700', 'from-cobalt-700 to-gold-700'),
    ('from-purple-500 to-pink-500', 'from-cobalt to-gold-intense'),

    # Background with opacity
    ('from-blue-600/20 to-purple-600/20', 'from-cobalt/20 to-royal/20'),
    ('from-blue-600/10 to-purple-600/10', 'from-cobalt/10 to-royal/10'),
    ('from-purple-600/20 to-pink-600/20', 'from-royal/20 to-cobalt/20'),
    ('from-blue-500/10 to-purple-500/10', 'from-cobalt/10 to-royal/10'),

    # Specific gradients
    ('from-indigo-500 to-purple-500', 'from-cobalt to-royal'),
    ('from-pink-500 to-purple-600', 'from-gold-intense to-cobalt'),

    # Borders
    ('border-blue-400', 'border-cobalt-400'),
    ('border-purple-400', 'border-cobalt-400'),
    ('border-purple-500', 'border-cobalt'),
    ('border-pink-500', 'border-gold-intense'),
    ('border-blue-500', 'border-cobalt'),
    ('border-indigo-500', 'border-cobalt'),

    # Backgrounds
    ('bg-purple-600', 'bg-cobalt'),
    ('bg-purple-500', 'bg-cobalt'),
    ('bg-pink-500', 'bg-gold-intense'),
    ('bg-blue-500', 'bg-cobalt'),
    ('bg-blue-600', 'bg-cobalt'),
    ('bg-indigo-600', 'bg-cobalt'),

    # Text colors
    ('text-purple-300', 'text-cobalt-300'),
    ('text-purple-400', 'text-gold'),
    ('text-purple-500', 'text-cobalt'),
    ('text-pink-500', 'text-gold-intense'),
    ('text-blue-400', 'text-cobalt-300'),
    ('text-blue-500', 'text-cobalt'),
    ('text-indigo-400', 'text-cobalt-300'),

    # Hover states
    ('hover:bg-purple-700', 'hover:bg-cobalt-700'),
    ('hover:bg-blue-700', 'hover:bg-cobalt-700'),
    ('hover:border-purple-500', 'hover:border-cobalt'),

    # Additional patterns for complete coverage
    ('hover:from-blue-700 hover:to-purple-700', 'hover:from-cobalt-600 hover:to-royal-600'),
    ('hover:from-purple-600 hover:to-pink-600', 'hover:from-cobalt-600 hover:to-gold-600'),
    ('hover:from-purple-700 hover:to-pink-700', 'hover:from-cobalt-700 hover:to-gold-700'),
    ('hover:from-purple-600/30 hover:to-pink-600/30', 'hover:from-cobalt/30 hover:to-gold/30'),
    ('from-slate-900 to-purple-900', 'from-slate-900 to-royal-800'),
    ('from-black to-pink-500', 'from-royal-900 to-cobalt'),
    ('from-blue-500 to-purple-500', 'from-cobalt to-royal'),
    ('from-rose-500 to-pink-500', 'from-gold-intense to-gold'),
    ('from-rose-600 to-pink-600', 'from-gold-700 to-gold-600'),
    ('from-rose-400 to-pink-400', 'from-gold-400 to-gold-intense'),
    ('from-purple-500 to-indigo-500', 'from-cobalt to-royal'),
    ('from-purple-600 to-indigo-600', 'from-cobalt-600 to-royal-600'),
    ('from-purple-500 to-purple-600', 'from-cobalt to-cobalt-600'),
    ('from-indigo-500 to-indigo-600', 'from-royal to-royal-600'),
    ('from-rose-500 to-rose-600', 'from-gold-intense to-gold-600'),
    ('hover:from-purple-600 hover:to-indigo-600', 'hover:from-cobalt-600 hover:to-royal-600'),
    ('from-purple-900/50 to-indigo-900/50', 'from-royal-900/50 to-cobalt-900/50'),
    ('from-pink-500/20 to-purple-500/20', 'from-gold/20 to-cobalt/20'),
    ('hover:from-rose-600 hover:to-pink-600', 'hover:from-gold-700 hover:to-gold-600'),
    ('from-blue-600 to-indigo-600', 'from-cobalt to-royal'),
    ('from-indigo-500 to-blue-600', 'from-cobalt to-royal'),
    ('from-blue-900/40 to-purple-900/40', 'from-royal-900/40 to-cobalt-900/40'),
    ('from-purple-900 to-slate-900', 'from-royal-900 to-slate-900'),
    ('from-red-900 to-pink-900', 'from-red-900 to-gold-900'),
    ('from-red-900/30 to-pink-900/30', 'from-red-900/30 to-gold-900/30'),
    ('bg-purple-900/30', 'bg-royal-900/30'),
    ('bg-purple-900/40', 'bg-royal-900/40'),
    ('hover:bg-purple-900/40', 'hover:bg-royal-900/40'),
    ('bg-pink-900/20', 'bg-gold-900/20'),
    ('from-purple-900/30 to-pink-900/30', 'from-royal-900/30 to-gold-900/30'),
    ('from-indigo-400 to-purple-400', 'from-cobalt to-gold'),
    ('from-violet-400 to-purple-400', 'from-cobalt to-royal'),
    ('from-violet-500 to-purple-500', 'from-cobalt to-royal'),
    ('from-violet-500 to-violet-600', 'from-cobalt to-cobalt-600'),
    ('hover:from-violet-600 hover:to-purple-600', 'hover:from-cobalt-600 hover:to-royal-600'),
    ('from-violet-900/40 to-purple-900/40', 'from-royal-900/40 to-cobalt-900/40'),
    ('bg-violet-900/40', 'bg-royal-900/40'),
    ('bg-violet-500/20', 'bg-cobalt/20'),
    ('from-purple-700 to-purple-900', 'from-cobalt-700 to-royal-900'),
    ('hover:from-blue-600/30 hover:to-purple-600/30', 'hover:from-cobalt/30 hover:to-royal/30'),
    ('from-red-900/40 to-rose-900/40', 'from-red-900/40 to-gold-900/40'),
    ('from-rose-900/40 to-pink-900/40', 'from-gold-900/40 to-gold-800/40'),
    ('from-pink-900/40 to-rose-900/40', 'from-gold-900/40 to-gold-800/40'),
    ('bg-rose-900/40', 'bg-gold-900/40'),
    ('from-red-500 to-pink-500', 'from-red-500 to-red-600'),
    ('from-red-600 to-pink-600', 'from-red-600 to-red-700'),
    ('hover:from-red-600 hover:to-pink-600', 'hover:from-red-600 hover:to-red-700'),
    ('from-red-700 to-pink-700', 'from-red-700 to-red-800'),
    ('from-purple-600 to-purple-700', 'from-cobalt-600 to-cobalt-700'),
    ('text-pink-300', 'text-gold-300'),
    ('text-pink-400', 'text-gold-400'),
    ('text-purple-200', 'text-cobalt-200'),
    ('text-purple-600', 'text-cobalt'),
    ('text-rose-400', 'text-gold-400'),
    ('text-violet-400', 'text-cobalt-400'),
    ('text-violet-300', 'text-cobalt-300'),
    ('border-rose-500', 'border-gold-intense'),
    ('border-rose-400/30', 'border-gold-400/30'),
    ('border-pink-400/30', 'border-gold-400/30'),
    ('border-violet-400/30', 'border-cobalt-400/30'),
    ('border-violet-500', 'border-cobalt'),
    ('border-pink-400', 'border-gold-400'),
    ('hover:border-pink-400', 'hover:border-gold-400'),
    ('focus:border-rose-500', 'focus:border-gold-intense'),
    ('focus:ring-purple-500', 'focus:ring-cobalt'),
]

# Comprehensive emoji list
EMOJI_PATTERNS = [
    # Common UI emojis
    r'🚀', r'✨', r'🎯', r'💡', r'🔒', r'✅', r'✓', r'❌', r'⚠️', r'⏰',
    r'📊', r'📈', r'📉', r'💼', r'🎬', r'🖼️', r'📝', r'✍️', r'📄', r'📋',
    r'📷', r'📸', r'🎵', r'▶️', r'🤖', r'🔷', r'👤', r'💳', r'🎨', r'🔥',
    r'👥', r'🔑', r'☁️', r'📁', r'📦', r'🔗', r'👍', r'🎉', r'🌟', r'⭐',
    r'📞', r'✉️', r'💎', r'🏆', r'🎪', r'🏢', r'🔍', r'📅', r'🎥', r'💻',
    # Numbers
    r'1️⃣', r'2️⃣', r'3️⃣', r'4️⃣', r'5️⃣', r'6️⃣', r'7️⃣', r'8️⃣', r'9️⃣', r'🔟',
    # Checkmarks and symbols
    r'☑️', r'✔️', r'❎', r'✖️', r'➕', r'➖', r'✏️', r'📌', r'🔔', r'🔕',
    # Social/communication
    r'💬', r'💭', r'🗨️', r'🗯️', r'💥', r'💫', r'⚡', r'🌈', r'🎁', r'🛠️',
]

def remove_emojis(text):
    """Remove all emojis from text"""
    for emoji in EMOJI_PATTERNS:
        # Remove emoji with optional trailing space
        text = re.sub(emoji + r'\s*', '', text)
    return text

def apply_color_replacements(text):
    """Apply all color replacements"""
    for old_color, new_color in COLOR_REPLACEMENTS:
        text = text.replace(old_color, new_color)
    return text

def process_file(file_path):
    """Process a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠️  Error reading: {e}")
        return False

    original_content = content

    # Apply color replacements
    content = apply_color_replacements(content)

    # Remove emojis
    content = remove_emojis(content)

    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"  ⚠️  Error writing: {e}")
            return False
    else:
        return False

def main():
    """Main rebranding function"""
    print("=" * 60)
    print("ORLA³ COMPLETE APP REBRANDING")
    print("=" * 60)
    print()

    # Find all TSX files in app directory
    app_dir = Path('app')
    tsx_files = list(app_dir.rglob('*.tsx'))

    print(f"Found {len(tsx_files)} TSX files to process\n")

    updated_count = 0
    unchanged_count = 0

    for file_path in sorted(tsx_files):
        # Skip node_modules
        if 'node_modules' in str(file_path):
            continue

        print(f"Processing: {file_path}")
        if process_file(file_path):
            print(f"  ✓ Updated")
            updated_count += 1
        else:
            print(f"  - No changes needed")
            unchanged_count += 1

    print()
    print("=" * 60)
    print(f"COMPLETE!")
    print(f"  Updated: {updated_count} files")
    print(f"  Unchanged: {unchanged_count} files")
    print()
    print("Changes applied:")
    print("  • Removed ALL emojis from entire app")
    print("  • Purple → Cobalt blue (#2d2e83)")
    print("  • Pink → Gold (#dbb12a)")
    print("  • All gradients → Cobalt/Royal/Gold")
    print("=" * 60)

if __name__ == '__main__':
    main()
