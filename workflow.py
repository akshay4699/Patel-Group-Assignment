"""Workflow orchestration module using LangGraph.

Connects Planner, Researcher, Writer, Fact-checker, and Editor into an autonomous,
multi-agent collaborative graph with revision feedback loops.
"""

import os
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from state import BookState
from src.planner import plan_book_node
from src.researcher import research_chapter_node
from src.writer import write_chapter_node
from src.factchecker import factcheck_chapter_node
from src.editor import editor_review_chapter_node


def post_review_decision(state: BookState) -> dict:
    """Evaluate whether to approve and advance, or trigger a revision loop."""
    logs = list(state.get("logs", []))
    chapter_idx = state.get("current_chapter_index", 0)
    chapter_num = chapter_idx + 1
    current_revision = state.get("current_revision_count", 0)
    max_revisions = state.get("max_revisions", 2)
    draft = state.get("current_draft", {})
    completed_chapters = list(state.get("completed_chapters", []))
    
    is_approved = draft.get("is_approved", False)
    
    # Check if chapter passes or has exhausted allowed revision cycles
    if is_approved or (current_revision >= max_revisions):
        reason = "approved by both Editor and Fact-checker" if is_approved else f"reached max allowed revisions ({max_revisions})"
        logs.append(f"[Workflow] Chapter {chapter_num} finalized ({reason}).")
        
        completed_chapters.append(draft)
        next_idx = chapter_idx + 1
        
        return {
            "completed_chapters": completed_chapters,
            "current_chapter_index": next_idx,
            "current_revision_count": 0,
            "current_draft": None,
            "current_research": [],
            "logs": logs,
            "system_status": f"Chapter {chapter_num} accepted. Moving to next phase."
        }
    else:
        # Trigger revision round
        next_revision = current_revision + 1
        logs.append(
            f"[Workflow] Sending Chapter {chapter_num} back to Writer for Revision Round {next_revision}."
        )
        return {
            "current_revision_count": next_revision,
            "logs": logs,
            "system_status": f"Chapter {chapter_num} in revision cycle {next_revision}."
        }


def check_next_step(state: BookState) -> Literal["researcher", "writer", "compile_book"]:
    """Conditional edge router determining the next node in the graph."""
    current_revision = state.get("current_revision_count", 0)
    current_idx = state.get("current_chapter_index", 0)
    total_chapters = state.get("total_chapters", 3)
    
    # If in active revision, route directly back to writer
    if current_revision > 0:
        return "writer"
        
    # If all chapters are finished, compile the book
    if current_idx >= total_chapters:
        return "compile_book"
        
    # Otherwise, research the next chapter
    return "researcher"


def compile_book_node(state: BookState) -> dict:
    """LangGraph node: Consolidates finalized chapters into the finished book manuscript."""
    logs = list(state.get("logs", []))
    logs.append("[Workflow] Consolidating all chapters into final manuscript...")
    
    title = state.get("title", "Pay Me on UPI: How Digital Payments Changed Small Business in India")
    target_audience = state.get("target_audience", "First-time small-business owners in India")
    chapters = state.get("completed_chapters", [])
    
    os.makedirs("output", exist_ok=True)
    manuscript_path = os.path.join("output", "Pay_Me_on_UPI.md")
    
    book_lines = [
        f"# {title}",
        f"\n**Target Audience:** {target_audience}\n",
        "---\n",
        "## Table of Contents\n"
    ]
    
    for ch in chapters:
        c_num = ch.get("chapter_number")
        c_title = ch.get("title")
        book_lines.append(f"- **Chapter {c_num}:** {c_title}")
        
    book_lines.append("\n---\n")
    
    for ch in chapters:
        c_num = ch.get("chapter_number")
        c_title = ch.get("title")
        c_body = ch.get("body_prose", "")
        c_takeaway = ch.get("takeaway", "")
        c_words = ch.get("word_count", 0)
        c_refs = ch.get("references", [])
        
        book_lines.append(f"## Chapter {c_num}: {c_title}\n")
        book_lines.append(f"*{c_words} words*\n")
        book_lines.append(f"{c_body}\n")
        book_lines.append(f"{c_takeaway}\n")
        book_lines.append("### References\n")
        
        for ref in c_refs:
            cid = ref.get("citation_id")
            sname = ref.get("source_name")
            atitle = ref.get("article_title")
            url = ref.get("url")
            book_lines.append(f"[{cid}] **{sname}** — *{atitle}*\n   URL: {url}\n")
            
        book_lines.append("\n---\n")
        
    final_manuscript = "\n".join(book_lines)
    
    with open(manuscript_path, "w", encoding="utf-8") as f:
        f.write(final_manuscript)
        
    logs.append(f"[Workflow] Successfully exported completed book to '{manuscript_path}'.")
    
    return {
        "logs": logs,
        "system_status": f"Book generation complete! Output saved to {manuscript_path}."
    }


def create_book_writer_graph() -> StateGraph:
    """Build and compile the multi-agent LangGraph workflow."""
    builder = StateGraph(BookState)
    
    # Register Agent Nodes
    builder.add_node("planner", plan_book_node)
    builder.add_node("researcher", research_chapter_node)
    builder.add_node("writer", write_chapter_node)
    builder.add_node("factchecker", factcheck_chapter_node)
    builder.add_node("editor", editor_review_chapter_node)
    builder.add_node("decision_router", post_review_decision)
    builder.add_node("compile_book", compile_book_node)
    
    # Establish Edges & Flow
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", "factchecker")
    builder.add_edge("factchecker", "editor")
    builder.add_edge("editor", "decision_router")
    
    # Conditional edge routing back to writer, forward to researcher, or to completion
    builder.add_conditional_edges(
        "decision_router",
        check_next_step,
        {
            "writer": "writer",
            "researcher": "researcher",
            "compile_book": "compile_book"
        }
    )
    
    builder.add_edge("compile_book", END)
    
    return builder.compile()
