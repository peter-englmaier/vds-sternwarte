#!/usr/bin/env python3
import re
import argparse
import sys
from pathlib import Path


start_regex = r"@\w+\.route\("
end_regex   = r"def\s+\w+\("
login_regex = r"@login_required"
role_regex  = r"@role_required"

def process_files(root_dir: Path) -> None:
    """
    Traverses a directory recursively, finds all .py files, 
    and runs a regex match to start/stop capturing lines.
    """
    if not root_dir.is_dir():
        print(f"Error: The path '{root_dir}' is not a valid directory.")
        return

    try:
        start_pattern = re.compile(start_regex)
        end_pattern = re.compile(end_regex)
        login_pattern = re.compile(login_regex)
        role_pattern = re.compile(role_regex)
    except re.error as e:
        print(f"Invalid regex pattern: {e}")
        return

    for py_file in root_dir.rglob("*.py"):
        try:
            capturing = False

            with py_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if start_pattern.search(line):
                        capturing = True
                        found_login = False
                        found_role = False

                    if capturing:
                        print(f"{py_file}:{line_num}: {line.strip()}")
                        if login_pattern.search(line):
                            found_login = True
                        elif role_pattern.search(line):
                            found_role = True
                        elif end_pattern.search(line):
                            capturing = False
                            print(f"Check: login={"ok" if found_login else "public"} role={"ok" if found_role else "open"}")
                            print()
            
        except (PermissionError, UnicodeDecodeError) as e:
            print(f"Skipping {py_file} due to error: {e}")

def main() -> None:
    """
    Entry point for the script. 
    Parses command line arguments and initiates the file processing.
    """
    parser = argparse.ArgumentParser(
        description="Recursively search .py files in a directory for start/end regex patterns."
    )
    
    # Positional argument for the directory to search
    parser.add_argument(
        "directory", 
        type=str, 
        help="The root directory to start the search from"
    )
    
    args = parser.parse_args()

    # Convert the string path to a Path object
    target_directory = Path(args.directory)
    
    process_files(target_directory)

if __name__ == "__main__":
    main()
