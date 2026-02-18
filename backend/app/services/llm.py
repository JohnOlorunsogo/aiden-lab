"""LLM service for error analysis using a self-hosted llama.cpp server (OpenAI-compatible API)."""
import logging
from typing import Optional

import httpx

from app.config import settings
from app.models.error import DetectedError, Solution
from app.templates.prompts import build_error_analysis_prompt

logger = logging.getLogger(__name__)


class LLMService:
    """Service for analyzing errors using a self-hosted LLM via OpenAI-compatible API."""

    def __init__(self):
        self._configured = False
        self._base_url: str = ""
        self._model: str = ""

    def configure(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Configure the LLM client.

        Args:
            base_url: Base URL of the llama.cpp server (e.g. http://host:8000)
            model: Model identifier to use in API requests
        """
        self._base_url = (base_url or settings.llm_base_url).rstrip("/")
        self._model = model or settings.llm_model

        if not self._base_url:
            raise ValueError(
                "LLM base URL is required. Set LLM_BASE_URL in .env"
            )

        self._configured = True
        logger.info(f"LLM service configured: {self._base_url} / {self._model}")

    async def analyze_error(
        self,
        error: DetectedError,
        command_history: str = "",
    ) -> Solution:
        """Analyze an error and generate a solution.

        Args:
            error: The detected error with context
            command_history: Recent commands sent to the device

        Returns:
            Solution with root cause, impact, solution, and prevention
        """
        if not self._configured:
            self.configure()

        prompt = build_error_analysis_prompt(
            device_id=error.device_id,
            timestamp=error.timestamp.isoformat(),
            context=error.context,
            error_line=error.error_line,
            context_lines=settings.context_lines,
            command_history=command_history,
        )

        response_text = await self._generate_content(prompt)
        return self._parse_response(response_text, error.id or 0)

    async def _generate_content(self, prompt: str) -> str:
        """Call the llama.cpp OpenAI-compatible chat completions endpoint."""
        url = f"{self._base_url}/v1/chat/completions"
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            data = response.json()
            text = data["choices"][0]["message"]["content"]
            logger.info("LLM API call successful")
            return text

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP Error {e.response.status_code}: {e}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"LLM Connection Error: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"LLM Timeout Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected LLM Error: {type(e).__name__}: {e}")
            raise

    @staticmethod
    def _parse_response(response_text: str, error_id: int) -> Solution:
        """Parse LLM response into a Solution object."""
        sections = {
            "root_cause": "",
            "impact": "",
            "solution": "",
            "prevention": "",
        }

        current_section = None

        for line in response_text.split("\n"):
            line_lower = line.lower().strip()

            if "root cause" in line_lower:
                current_section = "root_cause"
                continue
            elif "impact" in line_lower:
                current_section = "impact"
                continue
            elif "solution" in line_lower and "prevention" not in line_lower:
                current_section = "solution"
                continue
            elif "prevention" in line_lower:
                current_section = "prevention"
                continue

            if current_section and line.strip():
                sections[current_section] += line + "\n"

        for key in sections:
            sections[key] = sections[key].strip()
            if not sections[key]:
                sections[key] = "Unable to determine from context."

        return Solution(
            error_id=error_id,
            root_cause=sections["root_cause"],
            impact=sections["impact"],
            solution=sections["solution"],
            prevention=sections["prevention"],
        )


# Global LLM service instance
llm_service = LLMService()
