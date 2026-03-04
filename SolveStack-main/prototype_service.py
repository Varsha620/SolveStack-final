import os
import logging
import google.generativeai as genai
from models import Problem
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class PrototypeService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            print(f"[AI] Gemini API Key found (starts with {self.api_key[:5]}...)")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not found in environment. AI features will be disabled.")

    async def generate_implementation_plan(self, problem: Problem) -> str:
        """
        Generate a professional 3-step implementation plan for a given problem.
        """
        if not self.model:
            return "AI Generation is currently unavailable (Missing API Key)."

        prompt = f"""
        Given this engineering problem:
        Title: {problem.title}
        Description: {problem.description}
        Tags: {', '.join(problem.tags) if problem.tags else 'N/A'}

        Act as a Principal Software Engineer. Provide a high-impact, professional 3-step implementation plan to build a Minimum Viable Product (MVP) or solving the core technical challenge.
        
        Format your response exactly like this:
        1. [Step Name]: [Concise 2-sentence description focusing on architecture and tech stack]
        2. [Step Name]: [Concise 2-sentence description focusing on core logic/implementation]
        3. [Step Name]: [Concise 2-sentence description focusing on deployment/scaling]
        
        Keep it highly technical and "Expo-ready". Avoid fluff.
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating AI plan: {error_msg}")
            if "429" in error_msg:
                return "AI Quota Exceeded. Please check your Gemini API quota or try again in a few minutes."
            return f"Failed to generate implementation plan: {error_msg}"

# Singleton
_prototype_service = None
def get_prototype_service():
    global _prototype_service
    if _prototype_service is None:
        _prototype_service = PrototypeService()
    return _prototype_service
