#!/usr/bin/env python3
"""
Fix connection pool leaks in route files
Replaces 'conn = get_db_connection()' with 'with get_db_connection() as conn:'
"""

import re
import os
import glob

def fix_connection_leak(filepath):
    """Fix connection pool leaks in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern 1: Simple assignment outside try block
    # conn = get_db_connection()
    # cursor = conn.cursor()
    # try:
    #     ...
    # finally:
    #     cursor.close()

    # This is tricky to fix with regex, need to:
    # 1. Find 'conn = get_db_connection()' NOT inside a with block
    # 2. Find the matching try/finally block
    # 3. Wrap in with statement
    # 4. Indent the block

    # For now, let's do a simpler replacement that catches most cases
    # Replace standalone 'conn = get_db_connection()' with 'with get_db_connection() as conn:'

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line has 'conn = get_db_connection()' pattern
        if re.search(r'^\s*conn = get_db_connection\(\)\s*$', line):
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent

            # Replace with 'with get_db_connection() as conn:'
            new_lines.append(f"{indent_str}with get_db_connection() as conn:")

            # Next lines need to be indented by 4 more spaces
            # Find the extent of the block (until we hit a line at same/lower indent)
            i += 1
            block_indent = indent + 4

            while i < len(lines):
                curr_line = lines[i]

                # Empty line - keep as is
                if not curr_line.strip():
                    new_lines.append(curr_line)
                    i += 1
                    continue

                curr_indent = len(curr_line) - len(curr_line.lstrip())

                # If we hit a line at same or lower indent than original, we're done with block
                if curr_indent <= indent and curr_line.strip():
                    # Unless it's a cursor.close() in finally, which we need to include
                    if 'cursor.close()' in curr_line or 'cur.close()' in curr_line:
                        new_lines.append(' ' * block_indent + curr_line.lstrip())
                        i += 1
                        continue
                    else:
                        break

                # Indent the line by 4 more spaces
                new_lines.append(' ' * block_indent + curr_line.lstrip())
                i += 1
        else:
            new_lines.append(line)
            i += 1

    new_content = '\n'.join(new_lines)

    # Only write if changed
    if new_content != original_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False


def main():
    """Fix all route files"""
    route_files = glob.glob('routes/*.py')

    fixed_count = 0
    for filepath in sorted(route_files):
        # Skip __init__.py
        if filepath.endswith('__init__.py'):
            continue

        # Skip auth.py since we already fixed it manually
        if filepath.endswith('auth.py'):
            print(f"⏭️  Skipped {filepath} (already fixed manually)")
            continue

        try:
            if fix_connection_leak(filepath):
                print(f"✅ Fixed {filepath}")
                fixed_count += 1
            else:
                print(f"⏭️  No changes needed in {filepath}")
        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")

    print(f"\n✅ Fixed {fixed_count} files")


if __name__ == '__main__':
    main()
