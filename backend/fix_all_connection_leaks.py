#!/usr/bin/env python3
"""
Systematically fix all connection pool leaks in route files
Converts 'conn = get_db_connection()' to 'with get_db_connection() as conn:'
"""

import re
import os
import glob
from typing import List, Tuple

def find_function_containing_line(lines: List[str], target_line_num: int) -> Tuple[int, int]:
    """
    Find the start and end of the function containing the target line.
    Returns (function_start_line, function_end_line)
    """
    # Find function start by going backwards
    func_start = target_line_num
    for i in range(target_line_num - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('def ') or line.startswith('async def '):
            func_start = i
            break

    # Find function end by looking for next function or end of file
    func_end = len(lines)
    base_indent = len(lines[func_start]) - len(lines[func_start].lstrip())

    for i in range(func_start + 1, len(lines)):
        line = lines[i]
        if not line.strip():  # Skip empty lines
            continue

        current_indent = len(line) - len(line.lstrip())

        # If we hit another function at same/lower indent, we're done
        if current_indent <= base_indent and (line.strip().startswith('def ') or line.strip().startswith('async def ') or line.strip().startswith('@')):
            func_end = i
            break

    return func_start, func_end


def fix_connection_in_function(lines: List[str], conn_line_num: int) -> List[str]:
    """
    Fix a single connection leak by wrapping the relevant code in 'with' statement
    """
    # Find the function boundaries
    func_start, func_end = find_function_containing_line(lines, conn_line_num)

    # Get the line with conn = get_db_connection()
    conn_line = lines[conn_line_num]
    conn_indent = len(conn_line) - len(conn_line.lstrip())
    conn_indent_str = ' ' * conn_indent

    # Check if it's already inside a 'with' statement
    for i in range(conn_line_num - 1, func_start, -1):
        line = lines[i]
        if line.strip() and (len(line) - len(line.lstrip())) < conn_indent:
            if 'with get_db_connection()' in line:
                # Already fixed
                return lines
            break

    # Find where to end the with block (look for cur.close() or function end)
    with_block_end = func_end
    cur_close_line = None

    for i in range(conn_line_num + 1, func_end):
        line = lines[i]
        if 'cur.close()' in line or 'cursor.close()' in line:
            cur_close_line = i
            with_block_end = i + 1
            break

    # Build new function
    new_lines = []

    # Add lines before conn = get_db_connection()
    new_lines.extend(lines[func_start:conn_line_num])

    # Replace conn = get_db_connection() with with statement
    new_lines.append(f"{conn_indent_str}with get_db_connection() as conn:\n")

    # Find the try statement after conn = get_db_connection()
    try_line = None
    for i in range(conn_line_num + 1, min(conn_line_num + 10, func_end)):
        if lines[i].strip().startswith('try:'):
            try_line = i
            break

    if try_line:
        # There's a try block - indent everything after with
        indent_start = conn_line_num + 1
        indent_end = with_block_end

        for i in range(indent_start, indent_end):
            line = lines[i]
            if not line.strip():
                new_lines.append(line)
            else:
                # Indent by 4 spaces
                new_lines.append('    ' + line)
    else:
        # No try block - just indent the code
        indent_start = conn_line_num + 1

        # Find cur = conn.cursor()
        cur_line = None
        for i in range(conn_line_num + 1, min(conn_line_num + 5, func_end)):
            if 'cur = conn.cursor()' in lines[i] or 'cursor = conn.cursor()' in lines[i]:
                cur_line = i
                break

        if cur_line:
            # Add cursor line indented
            for i in range(conn_line_num + 1, with_block_end):
                line = lines[i]
                if not line.strip():
                    new_lines.append(line)
                elif 'cur.close()' in line or 'cursor.close()' in line:
                    # Skip cur.close() - with handles it
                    continue
                else:
                    new_lines.append('    ' + line)

    # Add remaining lines
    new_lines.extend(lines[with_block_end:])

    return new_lines


def fix_file(filepath: str) -> bool:
    """
    Fix all connection leaks in a file
    Returns True if file was modified
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    original_content = ''.join(lines)

    # Find all instances of conn = get_db_connection()
    leak_lines = []
    for i, line in enumerate(lines):
        if re.search(r'^\s*conn = get_db_connection\(\)\s*$', line):
            leak_lines.append(i)

    if not leak_lines:
        return False

    # Fix each leak from bottom to top (to preserve line numbers)
    for line_num in reversed(leak_lines):
        lines = fix_connection_in_function(lines, line_num)

    new_content = ''.join(lines)

    if new_content != original_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True

    return False


def main():
    """Fix all route files"""
    print("🔧 Fixing connection pool leaks in all route files...\n")

    # Get all files with leaks
    result = os.popen("grep -rn 'conn = get_db_connection()' routes/ --include='*.py' | cut -d: -f1 | sort | uniq").read()
    files_with_leaks = [f.strip() for f in result.strip().split('\n') if f.strip()]

    print(f"Found {len(files_with_leaks)} files with connection leaks:\n")

    fixed_count = 0
    for filepath in files_with_leaks:
        print(f"Fixing {filepath}...")

        try:
            if fix_file(filepath):
                print(f"  ✅ Fixed")
                fixed_count += 1
            else:
                print(f"  ⏭️  No changes needed")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n✅ Fixed {fixed_count}/{len(files_with_leaks)} files")

    # Verify syntax
    print("\n🔍 Verifying syntax...")
    import py_compile

    failed = []
    for filepath in files_with_leaks:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✅ {filepath}")
        except py_compile.PyCompileError as e:
            print(f"❌ {filepath} - {e.exc_value.msg}")
            failed.append(filepath)

    if failed:
        print(f"\n❌ Syntax errors in {len(failed)} files - manual review needed")
        return 1
    else:
        print(f"\n🎉 All files pass syntax validation!")
        return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
