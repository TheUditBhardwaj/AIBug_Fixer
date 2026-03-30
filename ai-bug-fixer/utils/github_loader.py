"""
GitHub Repository Loader Module
Handles cloning and loading repositories from GitHub
"""

import os
import tempfile
import subprocess
from typing import Optional, Dict, List
from pathlib import Path
import shutil


class GitHubLoader:
    """
    Loader for GitHub repositories.
    Clones repositories and extracts code files.
    """

    SUPPORTED_EXTENSIONS = [
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".scala",
        ".cs",
        ".vue",
        ".svelte",
        ".m",
        ".mm",
    ]

    EXCLUDED_DIRS = [
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        ".git",
        "dist",
        "build",
        "target",
        ".idea",
        ".vscode",
        "vendor",
        "Pods",
    ]

    def __init__(self, clone_dir: Optional[str] = None):
        """
        Initialize the GitHub loader.

        Args:
            clone_dir: Directory to clone repositories into
        """
        self.clone_dir = clone_dir or tempfile.mkdtemp(prefix="github_repo_")

    def _validate_url(self, url: str) -> bool:
        """
        Validate that the URL is a valid GitHub URL.

        Args:
            url: URL to validate

        Returns:
            True if valid GitHub URL
        """
        return (
            "github.com" in url
            or url.startswith("https://github.com")
            or url.startswith("git@github.com")
        )

    def _parse_url(self, url: str) -> str:
        """
        Parse and normalize GitHub URL.

        Args:
            url: GitHub URL (can be HTTPS or SSH)

        Returns:
            Normalized HTTPS URL
        """
        # Handle SSH URLs
        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/")

        # Remove .git suffix if present
        if url.endswith(".git"):
            url = url[:-4]

        # Ensure HTTPS
        if not url.startswith("https://"):
            if url.startswith("http://"):
                url = "https://" + url[7:]
            elif url.startswith("github.com"):
                url = "https://" + url

        return url

    def _get_repo_name(self, url: str) -> str:
        """
        Extract repository name from URL.

        Args:
            url: GitHub URL

        Returns:
            Repository name (owner/repo)
        """
        url = self._parse_url(url)
        parts = url.rstrip("/").split("/")
        return f"{parts[-2]}_{parts[-1]}"

    def clone_repo(self, repo_url: str, branch: str = "main", depth: int = 1) -> str:
        """
        Clone a GitHub repository.

        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone (default: main)
            depth: Clone depth for shallow clone

        Returns:
            Path to cloned repository

        Raises:
            ValueError: If URL is invalid
            RuntimeError: If clone fails
        """
        if not self._validate_url(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")

        repo_url = self._parse_url(repo_url)
        repo_name = self._get_repo_name(repo_url)
        target_dir = os.path.join(self.clone_dir, repo_name)

        # Remove existing clone if present
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        # Build git clone command
        cmd = [
            "git",
            "clone",
            "--branch",
            branch,
            "--depth",
            str(depth),
            repo_url,
            target_dir,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                # Try with 'master' branch if 'main' fails
                if branch == "main":
                    return self.clone_repo(repo_url, branch="master", depth=depth)
                raise RuntimeError(f"Failed to clone repository: {result.stderr}")

            return target_dir

        except subprocess.TimeoutExpired:
            raise RuntimeError("Clone operation timed out")
        except FileNotFoundError:
            raise RuntimeError("Git is not installed")

    def load_files(
        self,
        repo_path: str,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Load code files from a cloned repository.

        Args:
            repo_path: Path to cloned repository
            extensions: File extensions to include (default: all supported)
            exclude_patterns: Patterns to exclude

        Returns:
            Dictionary mapping relative file paths to content
        """
        if extensions is None:
            extensions = self.SUPPORTED_EXTENSIONS

        files = {}
        repo_path = Path(repo_path)

        for file_path in repo_path.rglob("*"):
            # Skip directories
            if not file_path.is_file():
                continue

            # Check extension
            if file_path.suffix not in extensions:
                continue

            # Check excluded directories
            if any(excluded in file_path.parts for excluded in self.EXCLUDED_DIRS):
                continue

            # Check exclude patterns
            if exclude_patterns:
                relative_path = str(file_path.relative_to(repo_path))
                if any(pattern in relative_path for pattern in exclude_patterns):
                    continue

            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                relative_path = str(file_path.relative_to(repo_path))
                files[relative_path] = content

            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

        return files

    def load_repo(
        self,
        repo_url: str,
        branch: str = "main",
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Clone and load a repository in one step.

        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone
            extensions: File extensions to include

        Returns:
            Dictionary mapping file paths to content
        """
        repo_path = self.clone_repo(repo_url, branch=branch)
        return self.load_files(repo_path, extensions=extensions)

    def get_file_tree(self, repo_path: str, max_depth: int = 3) -> List[Dict]:
        """
        Get the file tree structure of a repository.

        Args:
            repo_path: Path to repository
            max_depth: Maximum depth to traverse

        Returns:
            List of file/directory info dictionaries
        """
        tree = []
        repo_path = Path(repo_path)

        for item in repo_path.rglob("*"):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in self.EXCLUDED_DIRS):
                continue

            # Check depth
            depth = len(item.relative_to(repo_path).parts)
            if depth > max_depth:
                continue

            relative_path = str(item.relative_to(repo_path))
            tree.append(
                {
                    "name": item.name,
                    "path": relative_path,
                    "type": "directory" if item.is_dir() else "file",
                    "extension": item.suffix if item.is_file() else None,
                    "depth": depth,
                }
            )

        # Sort by path
        tree.sort(key=lambda x: x["path"])
        return tree

    def cleanup(self):
        """Clean up cloned repositories."""
        if os.path.exists(self.clone_dir):
            shutil.rmtree(self.clone_dir)


def load_github_repo(
    repo_url: str, branch: str = "main", extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Convenience function to load a GitHub repository.

    Args:
        repo_url: GitHub repository URL
        branch: Branch to clone
        extensions: File extensions to include

    Returns:
        Dictionary mapping file paths to content
    """
    loader = GitHubLoader()
    try:
        return loader.load_repo(repo_url, branch=branch, extensions=extensions)
    finally:
        loader.cleanup()
