#!/usr/bin/env python3
"""
CLI interface for AI Bug Fixer
Analyze code and ask questions using RAG
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
    """Print the analysis results in a simple, clean format."""
    bugs = result.get("bugs", [])
    if bugs:
        print(f"\nBUGS FOUND: {len(bugs)}\n")
        for i, bug in enumerate(bugs, 1):
            severity = bug.get('severity', 'unknown').upper()
            bug_type = bug.get('type', 'Unknown')
            description = bug.get('description', 'N/A')
            line_start = bug.get('line_start')
            
            location = ""
            if line_start:
                location = f" at line {line_start}"
                line_end = bug.get('line_end')
                if line_end and line_end != line_start:
                    location = f" at lines {line_start}-{line_end}"
            
            print(f"{i}. [{severity}] {bug_type}")
            print(f"   {description}{location}")
            
            explanation = bug.get('simple_explanation', '')
            if explanation and explanation != 'N/A':
                print(f"   {explanation}")
            print()
    else:
        print("\nNo bugs detected.\n")
    
    fixed_code = result.get("fixed_code", "")
    if fixed_code:
        print("FIXED CODE:")
        print(fixed_code)
        print()


def print_qa_help():
    """Print help for Q&A mode."""
    print("\nQ&A Mode Commands:")
    print("  help  - Show this help message")
    print("  exit  - Exit Q&A mode")
    print("  quit  - Exit Q&A mode")
    print("  clear - Clear the screen")
    print("\nJust type your question about the code to get an answer.\n")


def interactive_qa(bug_fixer: BugFixerService, code: str, analysis_result: dict):
    """Run interactive Q&A mode."""
    print("\n" + "-" * 50)
    print("Entering Q&A mode. Type 'help' for commands, 'exit' to quit.")
    print("-" * 50 + "\n")
    
    # Index the code for RAG
    try:
        chunks_indexed = bug_fixer.index_code(code)
        if chunks_indexed > 0:
            print(f"(Indexed {chunks_indexed} code chunks for context retrieval)\n")
    except Exception as e:
        print(f"(Warning: Could not index code for RAG: {e})\n")
    
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break
        
        if not question:
            continue
        
        # Handle commands
        if question.lower() in ['exit', 'quit']:
            print("\nGoodbye!")
            break
        
        if question.lower() == 'help':
            print_qa_help()
            continue
        
        if question.lower() == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            continue
        
        # Answer the question
        try:
            print("\nThinking...")
            answer = bug_fixer.ask_question(
                question=question,
                code=code,
                analysis_result=analysis_result,
            )
            print(f"\nAI: {answer}\n")
        except Exception as e:
            print(f"\nError: Could not get answer: {e}\n")


def analyze_file(bug_fixer: BugFixerService, filepath: str, use_rag: bool = True):
    """Analyze a single file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        return
    
    if not path.is_file():
        print(f"Error: Not a file: {filepath}")
        return
    
    print(f"Analyzing: {filepath}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        result = bug_fixer.analyze_code(code, path.name, use_rag)
        print_analysis(result)
        
        # Offer Q&A mode
        try:
            response = input("Would you like to ask questions about this code? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                interactive_qa(bug_fixer, code, result)
        except (EOFError, KeyboardInterrupt):
            print("\n")
        
    except UnicodeDecodeError:
        print(f"Error: File must be text-based")
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        import traceback
        traceback.print_exc()


def analyze_directory(bug_fixer: BugFixerService, dirpath: str, extensions: list = None, use_rag: bool = True):
    """Analyze all code files in a directory."""
    path = Path(dirpath)
    
    if not path.exists():
        print(f"Error: Directory not found: {dirpath}")
        return
    
    if not path.is_dir():
        print(f"Error: Not a directory: {dirpath}")
        return
    
    if extensions is None:
        extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
    
    files = {}
    for ext in extensions:
        for file_path in path.rglob(f'*{ext}'):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[str(file_path.relative_to(path))] = f.read()
                except Exception as e:
                    print(f"Warning: Skipping {file_path}: {str(e)}")
    
    if not files:
        print(f"Error: No code files found with extensions: {extensions}")
        return
    
    print(f"Analyzing {len(files)} file(s) in: {dirpath}")
    
    try:
        result = bug_fixer.analyze_files_dict(files)
        print_analysis(result)
        
        # Combine all code for Q&A
        combined_code = "\n\n".join([
            f"=== {fname} ===\n{content}" 
            for fname, content in files.items()
        ])
        
        # Offer Q&A mode
        try:
            response = input("Would you like to ask questions about this code? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                interactive_qa(bug_fixer, combined_code, result)
        except (EOFError, KeyboardInterrupt):
            print("\n")
        
    except Exception as e:
        print(f"Error analyzing directory: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Bug Fixer - Analyze code for bugs and ask questions",
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
    print("Initializing AI Bug Fixer...")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_model = os.getenv("LLM_MODEL")
    
    if not llm_api_key:
        print("Warning: LLM_API_KEY not set in environment")
    
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


if __name__ == '__main__':
    main()
