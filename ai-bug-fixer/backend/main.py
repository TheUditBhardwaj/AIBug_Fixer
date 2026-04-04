"""
AI Bug Fixer - FastAPI Backend
Main API endpoints for code analysis and bug fixing
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import os
import tempfile
import asyncio
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.services.bug_fixer import BugFixerService
from utils.github_loader import GitHubLoader

# Initialize FastAPI app
app = FastAPI(
    title="AI Bug Fixer API",
    description="Analyze code and automatically detect and fix bugs",
    version="1.0.0",
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (use environment variables from .env)
llm_api_key = os.getenv("LLM_API_KEY")
llm_base_url = os.getenv("LLM_BASE_URL")
llm_model = os.getenv("LLM_MODEL")

# Thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

# Global service instance
bug_fixer = BugFixerService(api_key=llm_api_key, base_url=llm_base_url, model=llm_model)


# Request/Response Models
class CodeAnalysisRequest(BaseModel):
    """Request model for single code analysis."""

    code: str
    filename: Optional[str] = None
    use_rag: bool = True


class RepoAnalysisRequest(BaseModel):
    """Request model for repository analysis."""

    repo_url: HttpUrl
    branch: str = "main"
    extensions: Optional[List[str]] = None


class MultiFileAnalysisRequest(BaseModel):
    """Request model for multi-file analysis."""

    files: Dict[str, str]


class BugInfo(BaseModel):
    """Model for individual bug."""

    type: str
    severity: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: str
    simple_explanation: str


class AnalysisResponse(BaseModel):
    """Response model for analysis."""

    bugs: List[BugInfo]
    explanation: str
    fixed_code: str
    suggestions: List[str]
    language: Optional[str] = None
    filename: Optional[str] = None


class MultiFileAnalysisResponse(BaseModel):
    """Response model for multi-file analysis."""

    bugs: List[BugInfo]
    explanation: str
    fixed_code: Dict[str, str]
    suggestions: List[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class QuestionRequest(BaseModel):
    """Request model for Q&A about code."""

    question: str
    code: str
    filename: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None


class QuestionResponse(BaseModel):
    """Response model for Q&A."""

    answer: str
    question: str


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/analyze-code", response_model=AnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyze a single code snippet for bugs.

    Args:
        request: Code analysis request with code content

    Returns:
        Analysis result with bugs, explanation, and fixed code
    """
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    try:
        # Run analysis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            bug_fixer.analyze_code,
            request.code,
            request.filename,
            request.use_rag,
        )

        return AnalysisResponse(
            bugs=[
                BugInfo(
                    type=bug.get("type", "unknown"),
                    severity=bug.get("severity", "medium"),
                    line_start=bug.get("line_start"),
                    line_end=bug.get("line_end"),
                    description=bug.get("description", ""),
                    simple_explanation=bug.get("simple_explanation", ""),
                )
                for bug in result.get("bugs", [])
            ],
            explanation=result.get("explanation", ""),
            fixed_code=result.get("fixed_code", request.code),
            suggestions=result.get("suggestions", []),
            language=result.get("language"),
            filename=result.get("filename"),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze-repo", response_model=MultiFileAnalysisResponse)
async def analyze_repo(request: RepoAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze an entire GitHub repository for bugs.

    Args:
        request: Repository URL and analysis options

    Returns:
        Analysis result for the entire repository
    """
    try:
        loader = GitHubLoader()

        # Run repository loading in thread pool
        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(
            executor,
            loader.load_repo,
            str(request.repo_url),
            request.branch,
            request.extensions,
        )

        if not files:
            raise HTTPException(
                status_code=400, detail="No code files found in repository"
            )

        # Analyze files
        result = await loop.run_in_executor(
            executor, bug_fixer.analyze_files_dict, files
        )

        # Schedule cleanup
        background_tasks.add_task(loader.cleanup)

        return MultiFileAnalysisResponse(
            bugs=[
                BugInfo(
                    type=bug.get("type", "unknown"),
                    severity=bug.get("severity", "medium"),
                    line_start=bug.get("line_start"),
                    line_end=bug.get("line_end"),
                    description=bug.get("description", ""),
                    simple_explanation=bug.get("simple_explanation", ""),
                )
                for bug in result.get("bugs", [])
            ],
            explanation=result.get("explanation", ""),
            fixed_code=result.get("fixed_code", {}),
            suggestions=result.get("suggestions", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Repository analysis failed: {str(e)}"
        )


@app.post("/analyze-multi-file", response_model=MultiFileAnalysisResponse)
async def analyze_multi_file(request: MultiFileAnalysisRequest):
    """
    Analyze multiple files for bugs.

    Args:
        request: Dictionary of filename -> content pairs

    Returns:
        Analysis result for all files
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, bug_fixer.analyze_files_dict, request.files
        )

        return MultiFileAnalysisResponse(
            bugs=[
                BugInfo(
                    type=bug.get("type", "unknown"),
                    severity=bug.get("severity", "medium"),
                    line_start=bug.get("line_start"),
                    line_end=bug.get("line_end"),
                    description=bug.get("description", ""),
                    simple_explanation=bug.get("simple_explanation", ""),
                )
                for bug in result.get("bugs", [])
            ],
            explanation=result.get("explanation", ""),
            fixed_code=result.get("fixed_code", {}),
            suggestions=result.get("suggestions", []),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze-file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    Analyze an uploaded file for bugs.

    Args:
        file: Uploaded file

    Returns:
        Analysis result for the file
    """
    try:
        # Read file content
        content = await file.read()
        code = content.decode("utf-8")

        if not code.strip():
            raise HTTPException(status_code=400, detail="File is empty")

        # Analyze the code
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, bug_fixer.analyze_code, code, file.filename, True
        )

        return AnalysisResponse(
            bugs=[
                BugInfo(
                    type=bug.get("type", "unknown"),
                    severity=bug.get("severity", "medium"),
                    line_start=bug.get("line_start"),
                    line_end=bug.get("line_end"),
                    description=bug.get("description", ""),
                    simple_explanation=bug.get("simple_explanation", ""),
                )
                for bug in result.get("bugs", [])
            ],
            explanation=result.get("explanation", ""),
            fixed_code=result.get("fixed_code", code),
            suggestions=result.get("suggestions", []),
            language=result.get("language"),
            filename=file.filename,
        )

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be text-based")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get statistics about the loaded index."""
    return bug_fixer.retriever.get_stats()


@app.post("/ask-question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer a question about analyzed code using RAG.

    Args:
        request: Question request with code and optional analysis result

    Returns:
        AI-generated answer to the question
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    try:
        loop = asyncio.get_event_loop()
        
        # Use the real filename for RAG indexing (falls back to a generic label)
        index_filename = request.filename or "analyzed_code"
        
        # Index the code for RAG retrieval with the actual filename
        await loop.run_in_executor(
            executor,
            bug_fixer.index_code,
            request.code,
            index_filename,
        )

        # Get answer using RAG, passing filename for better context
        answer = await loop.run_in_executor(
            executor,
            bug_fixer.ask_question,
            request.question,
            request.code,
            request.analysis_result,
            index_filename,
        )

        return QuestionResponse(
            answer=answer,
            question=request.question,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
