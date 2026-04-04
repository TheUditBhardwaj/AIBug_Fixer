"""
Bug Fixer Service Module
Orchestrates the bug detection and fixing pipeline
"""

from typing import Dict, Any, List, Optional
from .llm import LLMService
from .embeddings import EmbeddingService
from .retriever import RetrieverService
import os
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


class BugFixerService:
    """
    Main service for analyzing code and fixing bugs.
    Coordinates between LLM, embeddings, and retrieval services.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "mistralai/devstral-2-123b-instruct-2512",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the bug fixer service.

        Args:
            api_key: LLM API key
            base_url: LLM API base URL
            model: LLM model to use
            embedding_model: Embedding model to use
        """
        self.llm = LLMService(api_key=api_key, base_url=base_url, model=model)
        self.embedding = EmbeddingService(model_name=embedding_model)
        self.retriever = RetrieverService(
            embedding_dim=self.embedding.get_embedding_dimension()
        )

    def _detect_language(self, code: str, filename: Optional[str] = None) -> str:
        """
        Detect programming language from code content or filename.

        Args:
            code: Source code
            filename: Optional filename hint

        Returns:
            Detected language string
        """
        # Check filename extension first
        if filename:
            ext = Path(filename).suffix.lower()
            extension_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
                ".go": "go",
                ".rs": "rust",
                ".rb": "ruby",
                ".php": "php",
                ".swift": "swift",
                ".kt": "kotlin",
                ".scala": "scala",
                ".cs": "csharp",
            }
            if ext in extension_map:
                return extension_map[ext]

        # Try to detect from code patterns
        patterns = {
            "python": [r"def\s+\w+\s*\(", r"import\s+\w+", r"from\s+\w+\s+import"],
            "javascript": [
                r"function\s+\w+\s*\(",
                r"const\s+\w+\s*=",
                r"let\s+\w+\s*=",
            ],
            "typescript": [r":\s*(string|number|boolean)", r"interface\s+\w+"],
            "java": [r"public\s+class\s+", r"private\s+\w+\s+\w+"],
            "cpp": [r"#include\s*<", r"std::", r"cout\s*<<"],
            "go": [r"func\s+\w+\s*\(", r"package\s+\w+"],
            "rust": [r"fn\s+\w+\s*\(", r"let\s+mut\s+"],
            "ruby": [r"def\s+\w+", r"end\s*$", r"require\s+[\'\"]"],
        }

        max_matches = 0
        detected_lang = "python"  # Default

        for lang, pattern_list in patterns.items():
            matches = sum(1 for p in pattern_list if re.search(p, code))
            if matches > max_matches:
                max_matches = matches
                detected_lang = lang

        return detected_lang

    def _chunk_code(
        self, code: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split code into overlapping chunks for processing.

        Args:
            code: Source code
            chunk_size: Target size per chunk in characters
            overlap: Overlap between chunks

        Returns:
            List of chunk dictionaries
        """
        lines = code.split("\n")
        chunks = []
        current_chunk = []
        current_size = 0
        start_line = 0
        current_line = 0

        for i, line in enumerate(lines):
            if current_size + len(line) > chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": "\n".join(current_chunk),
                        "metadata": {
                            "start_line": start_line,
                            "end_line": current_line,
                            "type": "code_chunk",
                        },
                    }
                )
                # Keep overlap lines
                overlap_lines = (
                    current_chunk[-overlap:]
                    if len(current_chunk) > overlap
                    else current_chunk
                )
                current_chunk = overlap_lines
                current_size = sum(len(l) for l in overlap_lines)
                start_line = current_line - len(overlap_lines)
            else:
                current_chunk.append(line)
                current_size += len(line)
            current_line = i + 1

        # Add final chunk
        if current_chunk:
            chunks.append(
                {
                    "content": "\n".join(current_chunk),
                    "metadata": {
                        "start_line": start_line,
                        "end_line": current_line,
                        "type": "code_chunk",
                    },
                }
            )

        return chunks

    def analyze_code(
        self, code: str, filename: Optional[str] = None, use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a single code snippet for bugs.

        Args:
            code: Source code to analyze
            filename: Optional filename for language detection
            use_rag: Whether to use RAG for context

        Returns:
            Analysis result dictionary
        """
        # Detect language
        language = self._detect_language(code, filename)

        # Get context from retriever if available
        context = None
        if use_rag and self.retriever.get_stats()["total_documents"] > 0:
            query_embedding = self.embedding.embed_text(code)
            context = self.retriever.get_context_for_query(query_embedding)

        # Analyze with LLM
        result = self.llm.analyze_code(code, context, language)

        # Add metadata
        result["language"] = language
        result["filename"] = filename

        return result

    def analyze_file(self, file_path: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Analyze a file for bugs.

        Args:
            file_path: Path to the file
            use_rag: Whether to use RAG

        Returns:
            Analysis result
        """
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        return self.analyze_code(
            code, filename=os.path.basename(file_path), use_rag=use_rag
        )

    def analyze_repository(
        self, repo_path: str, file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an entire repository.

        Args:
            repo_path: Path to repository
            file_extensions: List of file extensions to include

        Returns:
            Combined analysis result
        """
        if file_extensions is None:
            file_extensions = [
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".java",
                ".cpp",
                ".c",
                ".go",
                ".rs",
                ".rb",
                ".php",
            ]

        # Collect all code files
        all_files = {}
        for ext in file_extensions:
            for file_path in Path(repo_path).rglob(f"*{ext}"):
                # Skip hidden directories and common non-source directories
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if "node_modules" in file_path.parts or "venv" in file_path.parts:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    relative_path = str(file_path.relative_to(repo_path))
                    all_files[relative_path] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

        if not all_files:
            return {
                "bugs": [],
                "explanation": "No code files found in repository",
                "fixed_code": {},
                "suggestions": [],
            }

        # Index all files for RAG
        self._index_files(all_files)

        # Analyze all files together
        language = (
            self._detect_language(list(all_files.values())[0]) if all_files else None
        )
        result = self.llm.analyze_multi_file(all_files, language)

        return result

    def _index_files(self, files: Dict[str, str]):
        """
        Index files for RAG retrieval.

        Args:
            files: Dictionary mapping filename to content
        """
        self.retriever.clear()

        for filename, content in files.items():
            chunks = self._chunk_code(content)
            for chunk in chunks:
                chunk["metadata"]["filepath"] = filename

            # Generate embeddings
            embeddings_with_metadata = self.embedding.embed_code_chunks(chunks)

            # Add to retriever
            self.retriever.add_code_chunks(embeddings_with_metadata, chunks)

    def analyze_files_dict(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze multiple files provided as a dictionary.
        Uses a size-aware strategy to prevent LLM API "request too large" errors.

        Args:
            files: Dictionary mapping filename to content

        Returns:
            Combined analysis result
        """
        if not files:
            return {
                "bugs": [],
                "explanation": "No files provided",
                "fixed_code": {},
                "suggestions": [],
            }

        # Index ALL files for RAG context (semantic search)
        self._index_files(files)

        # Detect primary language
        filenames = list(files.keys())
        primary_lang = self._detect_language(files[filenames[0]], filenames[0])

        # Estimate total content size
        total_size = sum(len(content) for content in files.values())
        
        # Threshold: ~40KB or ~10,000 tokens is typically safe for most APIs
        if total_size < 40000 and len(files) <= 12:
            # Small repo: Analyze all files together for cross-file context
            return self.llm.analyze_multi_file(files, primary_lang)
        else:
            # Large repo: Hybrid strategy to prevent 400/500 errors
            print(f"Repo too large ({total_size} bytes, {len(files)} files). Using hybrid RAG analysis...")
            
            combined_bugs = []
            combined_fixed_code = {}
            all_suggestions = []
            explanations = []

            # Pick the top N most important files to analyze deeply
            sorted_files = sorted(files.items(), key=lambda x: len(x[1]), reverse=True)
            files_to_analyze = sorted_files[:10]  # Analyze up to 10 most "significant" files

            def analyze_single_file(filename, content):
                """Worker function for parallel analysis."""
                # Use RAG to get context for THIS specific file
                query_embedding = self.embedding.embed_text(content)
                context = self.retriever.get_context_for_query(query_embedding, max_tokens=2000)
                
                # Individual analysis with RAG context
                analysis = self.llm.analyze_code(content, context, primary_lang)
                return filename, analysis

            # Analyze files in parallel to reduce total response time
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Map futures to filenames so we know which one failed
                future_to_filename = {
                    executor.submit(analyze_single_file, f, c): f 
                    for f, c in files_to_analyze
                }
                
                for future in future_to_filename:
                    filename = future_to_filename[future]
                    try:
                        _, analysis = future.result()
                        
                        # Add metadata to bugs
                        for bug in analysis.get("bugs", []):
                            bug["filename"] = filename
                            combined_bugs.append(bug)
                        
                        if "fixed_code" in analysis:
                            combined_fixed_code[filename] = analysis["fixed_code"]
                        
                        if "explanation" in analysis:
                            explanations.append(f"File {filename}: {analysis['explanation']}")
                        
                        if "suggestions" in analysis:
                            all_suggestions.extend(analysis["suggestions"])
                    except Exception as e:
                        print(f"Error analyzing {filename}: {e}")

            # Deduplicate suggestions
            unique_suggestions = list(set(all_suggestions))[:10]

            return {
                "bugs": combined_bugs,
                "explanation": "\n\n".join(explanations) if explanations else "Analyzed repository files with RAG context.",
                "fixed_code": combined_fixed_code,
                "suggestions": unique_suggestions,
            }

    def get_severity_summary(self, bugs: List[Dict]) -> Dict[str, int]:
        """
        Get summary count of bugs by severity.

        Args:
            bugs: List of bug dictionaries

        Returns:
            Dictionary with counts per severity level
        """
        summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for bug in bugs:
            severity = bug.get("severity", "medium").lower()
            if severity in summary:
                summary[severity] += 1
        return summary

    def get_bug_type_summary(self, bugs: List[Dict]) -> Dict[str, int]:
        """
        Get summary count of bugs by type.

        Args:
            bugs: List of bug dictionaries

        Returns:
            Dictionary with counts per bug type
        """
        summary = {}
        for bug in bugs:
            bug_type = bug.get("type", "unknown")
            summary[bug_type] = summary.get(bug_type, 0) + 1
        return summary

    def ask_question(
        self,
        question: str,
        code: str,
        analysis_result: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        max_context_tokens: int = 2000,
    ) -> str:
        """
        Answer a question about the analyzed code using RAG.

        Args:
            question: User's question about the code
            code: The code being analyzed
            analysis_result: Previous bug analysis results
            filename: The actual filename to include in context
            max_context_tokens: Maximum tokens for context retrieval

        Returns:
            Natural language answer to the question
        """
        context_parts = []

        # Always include the code with an accurate filename header
        file_label = filename or "analyzed_code"
        context_parts.append(f"=== File: {file_label} ===\n{code}\n")

        # Try to get additional context from RAG if index has documents
        if self.retriever.get_stats()["total_documents"] > 0:
            try:
                query_embedding = self.embedding.embed_text(question)
                rag_context = self.retriever.get_context_for_query(
                    query_embedding, max_tokens=max_context_tokens
                )
                if rag_context:
                    context_parts.append(f"=== Related Code Context ===\n{rag_context}\n")
            except Exception:
                pass

        combined_context = "\n".join(context_parts)

        return self.llm.answer_question(
            question=question,
            code_context=combined_context,
            analysis_result=analysis_result,
        )


    def index_code(self, code: str, filename: Optional[str] = None) -> int:
        """
        Index code for RAG retrieval.

        Args:
            code: Source code to index
            filename: Optional filename for metadata

        Returns:
            Number of chunks indexed
        """
        # Split code into chunks
        chunks = self._chunk_code(code, chunk_size=500, overlap=50)
        
        if not chunks:
            return 0

        # Create metadata for each chunk
        metadatas = []
        for chunk in chunks:
            metadatas.append({
                "filepath": filename or "unknown",
                "start_line": chunk.get("start_line", 0),
                "end_line": chunk.get("end_line", 0),
                "type": "code_chunk",
            })

        # Get content strings
        contents = [chunk["content"] for chunk in chunks]

        # Embed and add to index
        embeddings = self.embedding.embed_batch(contents)
        self.retriever.add_documents(embeddings, contents, metadatas)

        return len(chunks)
