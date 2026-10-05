"""Main execution script for the Multi-Agent Book Writer system.

Orchestrates the end-to-end execution of Planner, Researcher, Writer,
Fact-checker, and Editor to research, draft, and assemble the 3-chapter book.
"""

import os
import sys
import time
from typing import Dict, Any

from config import (
    BOOK_TITLE,
    TARGET_AUDIENCE,
    DEFAULT_CHAPTER_COUNT,
    MAX_REVISION_ROUNDS,
    GROQ_API_KEY,
    DEFAULT_MODEL
)
from state import BookState
from workflow import create_book_writer_graph


def print_banner():
    """Display startup header."""
    print("=" * 80)
    print("       MULTI-AGENT BOOK WRITER — LANGGRAPH & GROQ AI AGENTS       ")
    print("=" * 80)
    print(f"Title           : {BOOK_TITLE}")
    print(f"Target Audience : {TARGET_AUDIENCE}")
    print(f"Target Chapters : {DEFAULT_CHAPTER_COUNT} (600 - 900 words per chapter)")
    print(f"Model Engine    : {DEFAULT_MODEL}")
    print(f"Max Revisions   : {MAX_REVISION_ROUNDS} rounds per chapter")
    print("=" * 80)
    print()


def run_book_generation():
    """Initialize state and execute the multi-agent graph."""
    if not GROQ_API_KEY:
        print("[ERROR] GROQ_API_KEY not found in environment or .env file!")
        print("Please set your Groq API key in a .env file:")
        print("    GROQ_API_KEY=gsk_your_api_key_here")
        print("\nYou can obtain a free Groq API key at: https://console.groq.com/keys")
        sys.exit(1)

    print("[1/3] Compiling LangGraph Multi-Agent Workflow...")
    app = create_book_writer_graph()
    print("      Workflow successfully compiled.")

    # Initialize Root State
    initial_state: BookState = {
        "title": BOOK_TITLE,
        "target_audience": TARGET_AUDIENCE,
        "outline": None,
        "current_chapter_index": 0,
        "total_chapters": DEFAULT_CHAPTER_COUNT,
        "current_research": [],
        "current_draft": None,
        "current_revision_count": 0,
        "max_revisions": MAX_REVISION_ROUNDS,
        "completed_chapters": [],
        "logs": ["[System] Workflow initiated."],
        "system_status": "Starting Planner..."
    }

    print("\n[2/3] Executing Multi-Agent Collaboration Pipeline...\n")
    start_time = time.time()
    
    # Track executed log length for live streaming
    last_log_idx = 0

    try:
        final_state: Dict[str, Any] = {}
        for event in app.stream(initial_state, stream_mode="values"):
            logs = event.get("logs", [])
            while last_log_idx < len(logs):
                print(f"  {logs[last_log_idx]}")
                last_log_idx += 1
            final_state = event

        elapsed = round(time.time() - start_time, 2)
        print("\n" + "=" * 80)
        print(f"[3/3] BOOK GENERATION COMPLETE (Finished in {elapsed}s)")
        print("=" * 80)

        completed_chapters = final_state.get("completed_chapters", [])
        print(f"\nFinal Summary: {len(completed_chapters)} Chapters Generated:")
        
        total_words = 0
        for ch in completed_chapters:
            c_num = ch.get("chapter_number")
            c_title = ch.get("title")
            c_words = ch.get("word_count")
            c_revs = ch.get("revision_count", 0)
            c_refs = len(ch.get("references", []))
            total_words += c_words
            print(f"  - Chapter {c_num}: '{c_title}'")
            print(f"      Length: {c_words} words | Citations: {c_refs} | Revisions: {c_revs}")
            print(f"      Takeaway: {ch.get('takeaway')}\n")

        output_file = os.path.abspath(os.path.join("output", "Pay_Me_on_UPI.md"))
        print(f"Book saved to manuscript file:\n  -> {output_file}")
        print("=" * 80)

    except Exception as exc:
        print(f"\n[FATAL ERROR] An unexpected error occurred during execution: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print_banner()
    run_book_generation()
