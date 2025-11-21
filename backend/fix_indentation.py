#!/usr/bin/env python3
"""
Fix indentation errors in route files caused by migrate_to_pool.py
Pattern: Code after 'try:' statement needs to be indented by 4 spaces
"""

import re
import os

# Files with known indentation errors
FILES_TO_FIX = [
    ('routes/admin_pricing.py', 29),
    ('routes/auth.py', 172),
    ('routes/cloud_storage_oauth.py', 105),
    ('routes/collaboration.py', 69),
    ('routes/draft_campaign.py', 45),
    ('routes/oauth.py', 36),
    ('routes/organization.py', 46),
    ('routes/social_auth.py', 177),
]

def fix_try_block_indentation(filepath, try_line_num):
    """Fix indentation after a 'try:' statement"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the try statement
    try_line_idx = try_line_num - 1

    if try_line_idx >= len(lines):
        print(f"❌ Line {try_line_num} doesn't exist in {filepath}")
        return False

    # Detect indentation of the try statement
    try_line = lines[try_line_idx]
    try_indent = len(try_line) - len(try_line.lstrip())

    # Find the block after try: that needs indentation
    # Continue until we hit except/finally/dedent
    i = try_line_idx + 1
    block_end = i

    while i < len(lines):
        line = lines[i]
        if line.strip() == '':
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())

        # If we hit except/finally at the same level as try, we're done
        if current_indent == try_indent and (line.strip().startswith('except') or line.strip().startswith('finally')):
            block_end = i
            break

        # If we dedent below try level, we're done
        if current_indent < try_indent and line.strip():
            block_end = i
            break

        i += 1

    # Fix indentation for lines between try and except/finally
    fixed_lines = lines[:try_line_idx + 1]

    for i in range(try_line_idx + 1, block_end):
        line = lines[i]
        if line.strip():  # Non-empty line
            current_indent = len(line) - len(line.lstrip())
            # If line is at try indent level or less, indent it by 4
            if current_indent <= try_indent:
                fixed_lines.append(' ' * 4 + line.lstrip())
            else:
                # Already indented, add 4 more spaces
                fixed_lines.append(' ' * 4 + line)
        else:
            fixed_lines.append(line)

    # Add remaining lines
    fixed_lines.extend(lines[block_end:])

    # Write back
    with open(filepath, 'w') as f:
        f.writelines(fixed_lines)

    print(f"✅ Fixed {filepath}:{try_line_num}")
    return True

def main():
    print("🔧 Fixing indentation errors in route files...\n")

    fixed_count = 0
    for filepath, try_line in FILES_TO_FIX:
        if fix_try_block_indentation(filepath, try_line):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count}/{len(FILES_TO_FIX)} files")

    # Verify all files now pass
    print("\n🔍 Verifying syntax...")
    import py_compile
    import sys

    failed = []
    for filepath, _ in FILES_TO_FIX:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✅ {filepath}")
        except py_compile.PyCompileError as e:
            print(f"❌ {filepath} - {e.exc_value.msg}")
            failed.append(filepath)

    if failed:
        print(f"\n❌ Still have errors in {len(failed)} files")
        sys.exit(1)
    else:
        print(f"\n🎉 All {len(FILES_TO_FIX)} files now pass syntax validation!")

if __name__ == '__main__':
    main()
