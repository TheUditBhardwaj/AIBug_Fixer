"""
LLM Service Module
Handles communication with the LLM API (NVIDIA Devstral/Claude/OpenAI compatible)
"""

from openai import OpenAI
from typing import Optional, Dict, Any, List
import json
import os


class LLMService:
    """
    Service for interacting with LLM APIs.
    Supports NVIDIA Devstral, OpenAI, and Anthropic Claude endpoints.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "mistralai/devstral-2-123b-instruct-2512",
    ):
        """
        Initialize the LLM service.

        Args:
            base_url: API base URL (defaults to NVIDIA)
            api_key: API key (defaults to environment variable)
            model: Model identifier to use
        """
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        )
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.15,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt/question
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
                seed=42,
                stream=stream,
            )

            if stream:
                result = ""
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        result += chunk.choices[0].delta.content
                return result
            else:
                return completion.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")

    def analyze_code(
        self, code: str, context: Optional[str] = None, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze code for bugs and issues.

        Args:
            code: Source code to analyze
            context: Additional context from RAG retrieval
            language: Programming language of the code

        Returns:
            Structured analysis result
        """
        system_prompt = """You are a senior software engineer and code reviewer.
Analyze the code thoroughly and identify:
1. Syntax errors
2. Logical bugs
3. Performance issues
4. Security vulnerabilities
5. Code quality issues

Provide your response in the following JSON format:
{
  "bugs": [
    {
      "type": "syntax|logic|performance|security|quality",
      "severity": "low|medium|high|critical",
      "line_start": <number>,
      "line_end": <number>,
      "description": "<description of the bug>",
      "simple_explanation": "<beginner-friendly explanation>"
    }
  ],
  "explanation": "<overall explanation of issues found>",
  "fixed_code": "<corrected version of the entire code>",
  "suggestions": [
    "<improvement suggestion 1>",
    "<improvement suggestion 2>"
  ]
}

IMPORTANT: Return ONLY valid JSON, no markdown formatting or extra text."""

        user_prompt = f"""Analyze the following {language or 'code'}:

```{language or ''}
{code}
```
"""

        if context:
            user_prompt += f"\n\nRelevant context from codebase:\n{context}\n"

        user_prompt += "\nIdentify all bugs and provide the fixed code."

        response = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=8192,
        )

        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            # Return raw response if JSON parsing fails
            return {
                "bugs": [],
                "explanation": response,
                "fixed_code": code,
                "suggestions": ["Could not parse structured response from LLM"],
            }

    def analyze_multi_file(
        self, files: Dict[str, str], language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple files for cross-file bugs.

        Args:
            files: Dictionary mapping filename to code content
            language: Primary programming language

        Returns:
            Structured analysis result
        """
        system_prompt = """You are a senior software engineer analyzing a multi-file codebase.
Analyze all files together to identify:
1. Cross-file dependencies and issues
2. Import/export problems
3. Type mismatches between files
4. Missing function implementations
5. Circular dependencies
6. Inconsistent interfaces

Provide your response in JSON format:
{
  "bugs": [...],
  "explanation": "<overall explanation>",
  "fixed_code": "<map of filename to fixed code>",
  "suggestions": [...]
}"""

        files_content = ""
        current_len = 0
        max_total_len = 30000  # Safety limit for concatenated content

        for filename, content in files.items():
            header = f"=== {filename} ===\n"
            if current_len + len(header) + len(content) > max_total_len:
                # If adding this file exceeds limit, truncate or skip
                remaining = max_total_len - current_len - len(header)
                if remaining > 1000:
                    files_content += header + content[:remaining] + "... [TRUNCATED]\n\n"
                break
            
            files_content += header + content + "\n\n"
            current_len = len(files_content)

        user_prompt = f"""Analyze these files for bugs and issues:

{files_content}

Identify all bugs, especially those involving interactions between files."""

        response = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=8192,
        )

        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("\n", 1)[1]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response.rsplit("```", 1)[0]

            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {
                "bugs": [],
                "explanation": response,
                "fixed_code": files,
                "suggestions": ["Could not parse structured response"],
            }

    def answer_question(
        self,
        question: str,
        code_context: str,
        analysis_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Answer a question about code using RAG context.

        Args:
            question: User's question about the code
            code_context: Relevant code snippets retrieved via RAG
            analysis_result: Previous bug analysis results (optional)

        Returns:
            Natural language answer to the question
        """
        system_prompt = """You are a helpful programming assistant answering questions about code.
You have access to the relevant code context and any previous bug analysis.

Guidelines:
- Be concise but thorough
- Reference specific line numbers when relevant
- Explain concepts in simple terms
- If you're not sure about something, say so
- Focus on the specific question asked"""

        user_prompt = f"""Question: {question}

Relevant Code Context:
{code_context}
"""

        if analysis_result:
            bugs = analysis_result.get("bugs", [])
            if bugs:
                user_prompt += "\n\nPrevious Bug Analysis:\n"
                for i, bug in enumerate(bugs, 1):
                    user_prompt += f"{i}. [{bug.get('severity', 'unknown').upper()}] {bug.get('type', 'Unknown')}"
                    if bug.get('line_start'):
                        user_prompt += f" (line {bug.get('line_start')})"
                    user_prompt += f": {bug.get('description', 'N/A')}\n"

        user_prompt += "\nPlease answer the question based on the code context provided."

        response = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2048,
        )

        return response.strip()
