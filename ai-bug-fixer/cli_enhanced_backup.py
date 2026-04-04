#!/usr/bin/env python3
"""
CLI interface for AI Bug Fixer
Analyze code without running the web interface
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.bug_fixer import BugFixerService


def print_analysis(result: dict):
    """Pretty print the analysis results."""
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    
    # Print bugs
    bugs = result.get("bugs", [])
    if bugs:
        print(f"\n🐛 Found {len(bugs)} bug(s):\n")
        for i, bug in enumerate(bugs, 1):
            print(f"{i}. [{bug.get('severity', 'unknown').upper()}] {bug.get('type', 'Unknown')}")
            print(f"   Description: {bug.get('description', 'N/A')}")
            if bug.get('line_start'):
                print(f"   Location: Line {bug.get('line_start')}", end="")
                if bug.get('line_end') and bug.get('line_end') != bug.get('line_start'):
                    print(f" - {bug.get('line_end')}")
                else:
                    print()
            print(f"   Explanation: {bug.get('simple_explanation', 'N/A')}")
            print()
    else:
        print("\n✅ No bugs detected!\n")
    
    # Print explanation
    explanation = result.get("explanation", "")
    if explanation:
        print("📝 Overall Explanation:")
        print(f"   {explanation}\n")
    
    # Print suggestions
    suggestions = result.get("suggestions", [])
    if suggestions:
        print(f"💡 Suggestions ({len(suggestions)}):")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        print()
    
    # Print fixed code
    fixed_code = result.get("fixed_code", "")
    if fixed_code:
        print("🔧 Fixed Code:")
        print("-" * 70)
        print(fixed_code)
        print("-" * 70)
    
    print()


def analyze_file(bug_fixer: BugFixerService, filepath: str, use_rag: bool = True):
    """Analyze a single file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ Error: File not found: {filepath}")
        return
    
    if not path.is_file():
        print(f"❌ Error: Not a file: {filepath}")
        return
    
    print(f"🔍 Analyzing: {filepath}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        result = bug_fixer.analyze_code(code, path.name, use_rag)
        print_analysis(result)
        
    except UnicodeDecodeError:
        print(f"❌ Error: File must be text-based")
    except Exception as e:
        print(f"❌ Error analyzing file: {str(e)}")
        import traceback
        traceback.print_exc()


def analyze_directory(bug_fixer: BugFixerService, dirpath: str, extensions: list = None, use_rag: bool = True):
    """Analyze all code files in a directory."""
    path = Path(dirpath)
    
    if not path.exists():
        print(f"❌ Error: Directory not found: {dirpath}")
        return
    
    if not path.is_dir():
        print(f"❌ Error: Not a directory: {dirpath}")
        return
    
    # Default extensions if not provided
    if extensions is None:
        extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
    
    # Find all matching files
    files = {}
    for ext in extensions:
        for file_path in path.rglob(f'*{ext}'):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[str(file_path.relative_to(path))] = f.read()
                except Exception as e:
                    print(f"⚠️  Skipping {file_path}: {str(e)}")
    
    if not files:
        print(f"❌ No code files found with extensions: {extensions}")
        return
    
    print(f"🔍 Analyzing {len(files)} file(s) in: {dirpath}")
    
    try:
        result = bug_fixer.analyze_files_dict(files)
        print_analysis(result)
        
        # Print fixed files
        fixed_files = result.get("fixed_code", {})
        if fixed_files and isinstance(fixed_files, dict):
            print(f"\n🔧 Fixed {len(fixed_files)} file(s)")
            for filename in fixed_files.keys():
                print(f"   - {filename}")
        
    except Exception as e:
        print(f"❌ Error analyzing directory: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Bug Fixer - Analyze code for bugs without the web interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  python cli.py file path/to/code.py
  
  # Analyze a directory
  python cli.py dir path/to/project
  
  # Analyze directory with specific extensions
  python cli.py dir path/to/project -e .py .js .ts
  
  # Disable RAG (faster but less context)
  python cli.py file code.py --no-rag
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['file', 'dir'],
        help='Analysis mode: file or directory'
    )
    
    parser.add_argument(
        'path',
        help='Path to file or directory to analyze'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        nargs='+',
        help='File extensions to analyze (only for dir mode)',
        default=None
    )
    
    parser.add_argument(
        '--no-rag',
        action='store_true',
        help='Disable RAG (Retrieval Augmented Generation)'
    )
    
    args = parser.parse_args()
    
    # Initialize service
    print("🚀 Initializing AI Bug Fixer...")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_model = os.getenv("LLM_MODEL")
    
    if not llm_api_key:
        print("⚠️  Warning: LLM_API_KEY not set in environment")
    
    bug_fixer = BugFixerService(
        api_key=llm_api_key,
        base_url=llm_base_url,
        model=llm_model
    )
    
    use_rag = not args.no_rag
    
    # Run analysis based on mode
    if args.mode == 'file':
        analyze_file(bug_fixer, args.path, use_rag)
    elif args.mode == 'dir':
        analyze_directory(bug_fixer, args.path, args.extensions, use_rag)


if __name__ == "__main__":
    main()
