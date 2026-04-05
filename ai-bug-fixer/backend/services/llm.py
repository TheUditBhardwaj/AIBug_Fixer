  """
LLM Service Module
Handles communication with the LLM API using LangChain LCEL chains.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional, Dict, Any
import json
import os


class LLMService:
    """
    Service for interacting with LLM APIs via LangChain LCEL chains.
    Supports NVIDIA Devstral, OpenAI, and compatible endpoints.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "mistralai/devstral-2-123b-instruct-2512",
    ):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.api_key  = api_key  or os.getenv("LLM_API_KEY", "")
        self.model    = model

        self._llm = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            temperature=0.1,
            max_tokens=8192,
        )

        # ── Build named LCEL chains ─────────────────────────────
        self._analyze_chain   = self._build_analyze_chain()
        self._qa_chain        = self._build_qa_chain()
        self._multifile_chain = self._build_multifile_chain()

        # Print chain graphs once on startup
        self._print_chain_graphs()

    # ── Chain Builders ──────────────────────────────────────────

    def _build_analyze_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human",  "{user_prompt}"),
        ])
        return prompt | self._llm | StrOutputParser()

    def _build_qa_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human",  "{user_prompt}"),
        ])
        return prompt | self._llm | StrOutputParser()

    def _build_multifile_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human",  "{user_prompt}"),
        ])
        return prompt | self._llm | StrOutputParser()

    # ── ASCII Graph Printer ─────────────────────────────────────

    def _print_chain_graphs(self):
        """Print the ASCII graph of all LCEL chains to the terminal."""
        sep = "─" * 60

        print(f"\n{sep}")
        print("  ⛓  ANALYZE CODE CHAIN")
        print(sep)
        self._analyze_chain.get_graph().print_ascii()

        print(f"\n{sep}")
        print("  ⛓  Q&A CHAIN")
        print(sep)
        self._qa_chain.get_graph().print_ascii()

        print(f"\n{sep}")
        print("  ⛓  MULTI-FILE CHAIN")
        print(sep)
        self._multifile_chain.get_graph().print_ascii()
        print(f"{sep}\n")

    # ── Internal helper ─────────────────────────────────────────

    @staticmethod
    def _clean_json(response: str) -> str:
        """Strip markdown code fences from a JSON response."""
        s = response.strip()
        if s.startswith("```json"):
            s = s[7:]
        elif s.startswith("```"):
            s = s[3:]
        if s.endswith("```"):
            s = s[:-3]
        return s.strip()

    # ── Public methods ──────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.15,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> str:
        """Raw generation — used when a custom chain isn't needed."""
        chain = self._analyze_chain
        return chain.invoke({
            "system_prompt": system_prompt or "You are a helpful assistant.",
            "user_prompt": prompt,
        })

    def analyze_code(
        self, code: str, context: Optional[str] = None, language: Optional[str] = None
    ) -> Dict[str, Any]:
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

        user_prompt = f"Analyze the following {language or 'code'}:\n\n```{language or ''}\n{code}\n```\n"
        if context:
            user_prompt += f"\n\nRelevant context from codebase:\n{context}\n"
        user_prompt += "\nIdentify all bugs and provide the fixed code."

        response = self._analyze_chain.invoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })

        try:
            return json.loads(self._clean_json(response))
        except json.JSONDecodeError:
            return {
                "bugs": [],
                "explanation": response,
                "fixed_code": code,
                "suggestions": ["Could not parse structured response from LLM"],
            }

    def analyze_multi_file(
        self, files: Dict[str, str], language: Optional[str] = None
    ) -> Dict[str, Any]:
        system_prompt = """You are a senior software engineer analyzing a multi-file codebase.
Analyze all files together to identify cross-file dependencies, import problems,
type mismatches, missing implementations, circular dependencies, and inconsistent interfaces.

Respond in JSON:
{
  "bugs": [...],
  "explanation": "<overall explanation>",
  "fixed_code": "<map of filename to fixed code>",
  "suggestions": [...]
}"""

        files_content = ""
        current_len   = 0
        max_total_len = 30000

        for filename, content in files.items():
            header = f"=== {filename} ===\n"
            if current_len + len(header) + len(content) > max_total_len:
                remaining = max_total_len - current_len - len(header)
                if remaining > 1000:
                    files_content += header + content[:remaining] + "... [TRUNCATED]\n\n"
                break
            files_content += header + content + "\n\n"
            current_len = len(files_content)

        user_prompt = (
            f"Analyze these files for bugs and issues:\n\n{files_content}\n\n"
            "Identify all bugs, especially those involving interactions between files."
        )

        response = self._multifile_chain.invoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })

        try:
            return json.loads(self._clean_json(response))
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
        system_prompt = """You are a helpful programming assistant answering questions about code.
You have access to the relevant code context and any previous bug analysis.

Guidelines:
- Be concise but thorough
- Reference specific line numbers when relevant
- Explain concepts in simple terms
- If you're not sure about something, say so
- Focus on the specific question asked"""

        user_prompt = f"Question: {question}\n\nRelevant Code Context:\n{code_context}\n"

        if analysis_result:
            bugs = analysis_result.get("bugs", [])
            if bugs:
                user_prompt += "\n\nPrevious Bug Analysis:\n"
                for i, bug in enumerate(bugs, 1):
                    user_prompt += f"{i}. [{bug.get('severity','unknown').upper()}] {bug.get('type','Unknown')}"
                    if bug.get("line_start"):
                        user_prompt += f" (line {bug['line_start']})"
                    user_prompt += f": {bug.get('description', 'N/A')}\n"

        user_prompt += "\nPlease answer the question based on the code context provided."

        return self._qa_chain.invoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }).strip()

