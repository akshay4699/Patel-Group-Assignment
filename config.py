"""Configuration module for the Multi-Agent Book Writer system.

Handles environment variables, LLM model settings, and execution constants.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

# API Keys
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# LLM Configuration
# Groq-supported OpenAI OSS model and other popular Groq model names:
# 'openai/gpt-oss-120b', 'llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'llama-3.1-8b-instant'
DEFAULT_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.4"))

# Book Generation Specifications according to the assignment brief
BOOK_TITLE: str = "Pay Me on UPI: How Digital Payments Changed Small Business in India"
TARGET_AUDIENCE: str = "First-time small-business owners in India"
TARGET_WORD_COUNT_MIN: int = 600
TARGET_WORD_COUNT_MAX: int = 900
MAX_REVISION_ROUNDS: int = int(os.getenv("MAX_REVISION_ROUNDS", "2"))
DEFAULT_CHAPTER_COUNT: int = 3

def get_groq_llm(temperature: Optional[float] = None, model: Optional[str] = None):
    """Instantiate and return the Groq Chat model with specified temperature.
    
    Raises:
        ValueError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Please create a .env file with GROQ_API_KEY=your_key "
            "or set the GROQ_API_KEY environment variable."
        )
    
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=model or DEFAULT_MODEL,
        temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
        api_key=api_key,
    )
