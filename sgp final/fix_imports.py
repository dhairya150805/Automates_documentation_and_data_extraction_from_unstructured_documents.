"""
Fix import paths in backend files to use relative imports
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix backend imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace backend.module with relative imports
        content = re.sub(r'from backend\.', 'from ', content)
        content = re.sub(r'import backend\.', 'import ', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Fixed: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False

def main():
    backend_dir = Path("d:/sgp final/backend")
    
    # Find all Python files
    python_files = list(backend_dir.rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files to process...")
    
    fixed_count = 0
    for py_file in python_files:
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"✅ Successfully fixed {fixed_count}/{len(python_files)} files")

if __name__ == "__main__":
    main()
