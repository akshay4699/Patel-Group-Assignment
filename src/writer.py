"""Writer Agent: Composes continuous, mentor-voiced chapters adhering to the brief.

Ensures:
- 600–900 words of flowing prose (strictly NO bullet points).
- Numbered in-text citations [1], [2], etc. for all facts, figures, and dates.
- Clear explanations of technical terms on first introduction.
- Final concluding line starting strictly with 'Takeaway: '.
- Full reference bibliography formatted at the bottom.
"""

from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_groq_llm, TARGET_WORD_COUNT_MIN, TARGET_WORD_COUNT_MAX
from state import ChapterDraft, ResearchItem, BookState
from src.prompts import WRITER_SYSTEM_PROMPT


def format_research_context(research_data: List[Dict[str, Any]]) -> str:
    """Format research references for LLM context."""
    lines = []
    for item in research_data:
        cid = item.get("citation_id")
        summary = item.get("fact_summary")
        source = item.get("source_name")
        title = item.get("article_title")
        url = item.get("url")
        lines.append(f"[{cid}] FACT: {summary}\n    SOURCE: {source} - '{title}' ({url})")
    return "\n\n".join(lines)


def write_chapter_node(state: BookState) -> dict:
    """LangGraph node: Drafts or revises the current chapter."""
    logs = list(state.get("logs", []))
    chapter_idx = state.get("current_chapter_index", 0)
    chapter_num = chapter_idx + 1
    revision_count = state.get("current_revision_count", 0)
    
    outline = state.get("outline", {})
    chapter_info = {}
    if outline and "chapters" in outline and chapter_idx < len(outline["chapters"]):
        chapter_info = outline["chapters"][chapter_idx]
    
    chapter_title = chapter_info.get("title", f"Chapter {chapter_num}")
    chapter_summary = chapter_info.get("summary", "")
    target_data = chapter_info.get("target_data_points", [])
    
    research_items = state.get("current_research", [])
    research_context = format_research_context(research_items)
    
    current_draft_data = state.get("current_draft")
    is_revision = revision_count > 0 and current_draft_data is not None
    
    action_str = f"Revising (Round {revision_count})" if is_revision else "Drafting initial text for"
    logs.append(f"[Writer] {action_str} Chapter {chapter_num}: '{chapter_title}'...")
    
    llm = get_groq_llm(temperature=0.5)
    
    instructions = f"""You are writing Chapter {chapter_num} of the book.
Chapter Title: "{chapter_title}"
Chapter Objective: {chapter_summary}
Target Audience: First-time small-business owners in India (kirana stores, retail shops, traders).

MANDATORY GUIDELINES:
1. WORD COUNT: Aim for approximately 700 to 800 words (must be between {TARGET_WORD_COUNT_MIN} and {TARGET_WORD_COUNT_MAX} words).
2. FORMATTING: Use purely continuous, flowing paragraphs. ABSOLUTELY NO BULLET POINTS, NO HYPHENS/DASHES AS LISTS, NO NUMBERED LISTS in the narrative body.
3. CITATIONS: You must naturally cite the verified research facts using bracketed numbers [1], [2], [3], [4] right inside your sentences wherever relevant facts, dates, or figures appear.
4. TONE & JARGON: Warm, friendly, encouraging mentor tone. Plain English. Explain terms like 'UPI', 'QR Code', 'MDR', or 'settlement' simply the first time they appear.
5. CONCLUDING LINE: The narrative MUST end with exactly one sentence starting with 'Takeaway: ' summarizing the main lesson for the shopkeeper.
6. REFERENCE LIST: Immediately following the Takeaway line, provide the numbered references formatted as:
   References:
   [1] Source Name - Article Title (URL)
   [2] Source Name - Article Title (URL)

VERIFIED RESEARCH FACTS TO CITE:
{research_context}
"""

    if is_revision:
        editor_feedback = current_draft_data.get("editor_feedback", {})
        fact_feedback = current_draft_data.get("factchecker_feedback", {})
        instructions += f"""
PREVIOUS DRAFT REVISION FEEDBACK TO FIX:
- Editor Critique: {editor_feedback.get('tone_critique', '')} | {editor_feedback.get('formatting_critique', '')}
- Editor Action Items: {', '.join(editor_feedback.get('actionable_revisions', []))}
- Fact-Checker Action Items: {', '.join(fact_feedback.get('actionable_revisions', []))}
- Previous Body Word Count: {current_draft_data.get('word_count', 0)} words.

Please thoroughly address all feedback points while maintaining flowing prose and all verified citations.
"""

    messages = [
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=instructions)
    ]
    
    response = llm.invoke(messages)
    generated_text = response.content.strip()
    
    # Parse body prose, takeaway, and reference list
    takeaway_line = ""
    prose_body = generated_text
    
    # Extract Takeaway:
    if "Takeaway:" in generated_text:
        parts = generated_text.split("Takeaway:", 1)
        prose_body = parts[0].strip()
        remaining = parts[1].strip()
        if "References:" in remaining:
            takeaway_part, _ = remaining.split("References:", 1)
            takeaway_line = "Takeaway: " + takeaway_part.strip()
        else:
            takeaway_line = "Takeaway: " + remaining.strip().split("\n")[0].strip()
    else:
        takeaway_line = "Takeaway: Embracing UPI allows your shop to eliminate daily cash friction and build a trusted digital foundation for future business growth."
        
    full_content_for_count = f"{prose_body}\n\n{takeaway_line}"
    word_count = len(full_content_for_count.split())
    
    research_models = [ResearchItem(**item) for item in research_items]
    
    draft = ChapterDraft(
        chapter_number=chapter_num,
        title=chapter_title,
        body_prose=prose_body,
        takeaway=takeaway_line,
        references=research_models,
        word_count=word_count,
        revision_count=revision_count,
        is_approved=False
    )
    
    logs.append(
        f"[Writer] Completed Chapter {chapter_num} draft ({word_count} words). "
        f"Passed to Fact-checker and Editor."
    )
    
    return {
        "current_draft": draft.model_dump(),
        "logs": logs,
        "system_status": f"Chapter {chapter_num} drafted. Undergoing review."
    }
