#!/usr/bin/env python3
"""
Automated script to migrate all route files to use connection pooling
Converts old pattern:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        ...
    finally:
        cur.close()
        conn.close()

To new pattern:
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            ...
        finally:
            cur.close()
"""

import re
import os
from pathlib import Path

def migrate_file(filepath):
    """Migrate a single file to use connection pool"""
    print(f"Processing: {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = False

    # Step 1: Add/update import statement
    if 'from db_pool import get_db_connection' not in content:
        # Check if file has a local get_db_connection definition
        if 'def get_db_connection():' in content:
            # Add import before imports section
            import_pattern = r'(from logger import setup_logger.*?\n)'
            replacement = r'\1from db_pool import get_db_connection  # Use connection pool\n'
            content = re.sub(import_pattern, replacement, content)

            # Remove local get_db_connection definition
            local_def_pattern = r'\ndef get_db_connection\(\):.*?(?=\n(?:def |class |@|\Z))'
            content = re.sub(local_def_pattern, '\n', content, flags=re.DOTALL)

            # Remove DATABASE_URL if it's only used for get_db_connection
            if content.count('DATABASE_URL') <= 2:  # Import + removed function
                content = re.sub(r'DATABASE_URL = os\.getenv\("DATABASE_URL"\)\n', '', content)

            changes_made = True
            print(f"  ✅ Added pool import and removed local get_db_connection()")

    # Step 2: Convert connection usage pattern
    # Pattern: conn = get_db_connection()
    #          cur = conn.cursor()
    #          try:
    #              ...
    #          finally:
    #              cur.close()
    #              conn.close()

    # Find all occurrences of the old pattern
    old_pattern = re.compile(
        r'(\s+)conn = get_db_connection\(\)\n'
        r'\1cur = conn\.cursor\(\)\n'
        r'\n'
        r'\1try:',
        re.MULTILINE
    )

    def replace_connection(match):
        indent = match.group(1)
        return f'{indent}with get_db_connection() as conn:\n{indent}    cur = conn.cursor()\n{indent}    try:'

    new_content = old_pattern.sub(replace_connection, content)

    if new_content != content:
        content = new_content
        changes_made = True
        print(f"  ✅ Converted to with statement pattern")

    # Step 3: Remove conn.close() calls (pool handles this)
    close_pattern = r'\s+conn\.close\(\)\n'
    new_content = re.sub(close_pattern, '\n', content)

    if new_content != content:
        content = new_content
        changes_made = True
        print(f"  ✅ Removed conn.close() calls")

    # Write back if changes were made
    if changes_made and content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  💾 File updated\n")
        return True
    else:
        print(f"  ⏭️  No changes needed\n")
        return False

def main():
    """Migrate all route files"""
    routes_dir = Path(__file__).parent / 'routes'
    utils_dir = Path(__file__).parent / 'utils'

    files_to_migrate = []

    # Find all Python files in routes/
    if routes_dir.exists():
        files_to_migrate.extend(routes_dir.glob('*.py'))

    # Find specific utils files
    if utils_dir.exists():
        files_to_migrate.extend(utils_dir.glob('*auth*.py'))

    # Also migrate root-level files that use connections
    root_files = ['check_user_data.py']
    for filename in root_files:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            files_to_migrate.append(filepath)

    print(f"🔄 Found {len(files_to_migrate)} files to check\n")
    print("=" * 60)

    updated_count = 0
    for filepath in sorted(files_to_migrate):
        if filepath.name == '__init__.py':
            continue

        try:
            if migrate_file(filepath):
                updated_count += 1
        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    print("=" * 60)
    print(f"\n✅ Migration complete!")
    print(f"   Files updated: {updated_count}/{len(files_to_migrate)}")
    print(f"\n📝 Next steps:")
    print(f"   1. Review changes: git diff")
    print(f"   2. Test locally: python main.py")
    print(f"   3. Commit changes: git add . && git commit")

if __name__ == '__main__':
    main()
