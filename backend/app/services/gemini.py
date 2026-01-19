"""Gemini AI service for error analysis."""
import google.generativeai as genai
from typing import Optional
import asyncio
from functools import partial

from app.config import settings
from app.models.error import DetectedError, Solution
from app.templates.prompts import build_error_analysis_prompt


class GeminiService:
    """Service for analyzing errors using Google Gemini API."""
    
    def __init__(self):
        self._configured = False
        self._model = None
    
    def configure(self, api_key: Optional[str] = None):
        """Configure the Gemini API client."""
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in .env")
        
        genai.configure(api_key=key)
        self._model = genai.GenerativeModel('gemini-pro')
        self._configured = True
    
    async def analyze_error(
        self, 
        error: DetectedError,
        command_history: str = ""
    ) -> Solution:
        """
        Analyze an error and generate a solution.
        
        Args:
            error: The detected error with context
            command_history: Recent commands sent to the device
            
        Returns:
            Solution with root cause, impact, solution, and prevention
        """
        if not self._configured:
            self.configure()
        
        # Build the prompt
        prompt = build_error_analysis_prompt(
            device_id=error.device_id,
            timestamp=error.timestamp.isoformat(),
            context=error.context,
            error_line=error.error_line,
            context_lines=settings.context_lines,
            command_history=command_history
        )
        
        # Run synchronous Gemini call in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            partial(self._generate_content, prompt)
        )
        
        # Parse the response
        return self._parse_response(response, error.id or 0)
    
    def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini (sync call)."""
        response = self._model.generate_content(prompt)
        return response.text
    
    def _parse_response(self, response_text: str, error_id: int) -> Solution:
        """Parse Gemini response into a Solution object."""
        # Simple parsing - look for sections
        sections = {
            "root_cause": "",
            "impact": "",
            "solution": "",
            "prevention": ""
        }
        
        current_section = None
        lines = response_text.split("\n")
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
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
            
            # Add content to current section
            if current_section and line.strip():
                sections[current_section] += line + "\n"
        
        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()
            if not sections[key]:
                sections[key] = "Unable to determine from context."
        
        return Solution(
            error_id=error_id,
            root_cause=sections["root_cause"],
            impact=sections["impact"],
            solution=sections["solution"],
            prevention=sections["prevention"]
        )


# Global Gemini service instance
gemini_service = GeminiService()
