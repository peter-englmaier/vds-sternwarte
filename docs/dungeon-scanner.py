#!/usr/bin/env python3
import re
import argparse
import sys
from pathlib import Path

def process_files(root_dir: Path, start_regex: str, end_regex: str) -> None:
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
    except re.error as e:
        print(f"Invalid regex pattern: {e}")
        return

    print(f"Scanning directory: {root_dir.absolute()}")
    print(f"Start Pattern: {start_regex}")
    print(f"End Pattern:   {end_regex}\n" + "="*50)

    for py_file in root_dir.rglob("*.py"):
        try:
            capturing = False
            found_any = False
            with py_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not capturing:
                        if start_pattern.search(line):
                            capturing = True
                            print(f"{py_file}:{line_num}: {line.strip()}")
                            found_any = True
                    else:
                        if end_pattern.search(line):
                            capturing = False
                            print(f"{py_file}:{line_num}: {line.strip()}")
                            print()
                            found_any = True
                        else:
                            print(f"{py_file}:{line_num}: {line.strip()}")
                            found_any = True
            
            if found_any:
                pass
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
    
    # Optional arguments for the regex patterns
    parser.add_argument(
        "-s", "--start", 
        type=str, 
        default=r"@\w+\.route\(",
        help="The regex pattern to start capturing (default: '@\\w+\\.route\\(')"
    )
    parser.add_argument(
        "-e", "--end", 
        type=str, 
        default=r"def\s+\w+\(",
        help="The regex pattern to stop capturing (default: 'def\\s+\\w+\\(')"
    )

    args = parser.parse_args()

    # Convert the string path to a Path object
    target_directory = Path(args.directory)
    
    process_files(target_directory, args.start, args.end)

if __name__ == "__main__":
    main()
