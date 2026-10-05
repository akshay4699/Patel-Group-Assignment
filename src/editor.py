"""Editor Agent: Evaluates tone, readability, flowing prose, and strict brief compliance.

Audits:
1. Word count constraint (600 - 900 words).
2. Prose rules: Strict absence of bullet points or list markers.
3. Tone: Friendly, encouraging, mentor-like voice.
4. Concluding line: Must end with a single line starting with 'Takeaway: '.
5. Grammar and punctuation.
"""

import re
import json
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_groq_llm, TARGET_WORD_COUNT_MIN, TARGET_WORD_COUNT_MAX
from state import ChapterReviewFeedback, BookState
from src.prompts import EDITOR_SYSTEM_PROMPT


def check_for_bullet_points(text: str) -> List[str]:
    """Scan text for illegal bullet points or list markers."""
    issues = []
    lines = text.split("\n")
    bullet_patterns = [
        (r'^\s*[\*\-\•\⁃\‣]\s+', "Unpermitted bullet point / hyphen list marker detected"),
        (r'^\s*\d+[\.\)]\s+', "Unpermitted numbered list marker detected in body prose")
    ]
    for idx, line in enumerate(lines, start=1):
        for pattern, msg in bullet_patterns:
            if re.match(pattern, line):
                issues.append(f"Line {idx}: {msg} ('{line[:40]}...')")
    return issues


def editor_review_chapter_node(state: BookState) -> dict:
    """LangGraph node: Evaluates the draft against editorial and stylistic guidelines."""
    logs = list(state.get("logs", []))
    chapter_idx = state.get("current_chapter_index", 0)
    chapter_num = chapter_idx + 1
    
    logs.append(f"[Editor] Reviewing Chapter {chapter_num} for tone, prose, and word count...")
    
    current_draft_dict = state.get("current_draft")
    if not current_draft_dict:
        logs.append(f"[Editor Warning] No draft found for Chapter {chapter_num} to review.")
        return {"logs": logs}
    
    prose = current_draft_dict.get("body_prose", "")
    takeaway = current_draft_dict.get("takeaway", "")
    full_content = f"{prose}\n\n{takeaway}".strip()
    
    # 1. Deterministic Rule Checks
    words = full_content.split()
    word_count = len(words)
    bullet_issues = check_for_bullet_points(prose)
    
    has_valid_takeaway = takeaway.strip().startswith("Takeaway:")
    
    deterministic_flaws = []
    if word_count < TARGET_WORD_COUNT_MIN:
        deterministic_flaws.append(
            f"Word count is {word_count}, below the required minimum of {TARGET_WORD_COUNT_MIN} words. Expand with richer mentor explanations."
        )
    elif word_count > TARGET_WORD_COUNT_MAX:
        deterministic_flaws.append(
            f"Word count is {word_count}, exceeding the maximum of {TARGET_WORD_COUNT_MAX} words. Trim wordiness while preserving flow."
        )
        
    if bullet_issues:
        deterministic_flaws.append(
            f"Found {len(bullet_issues)} bullet points or list markers. Brief strictly mandates continuous, flowing prose without any bullets."
        )
        
    if not has_valid_takeaway:
        deterministic_flaws.append("Chapter does not conclude with a single line starting with 'Takeaway:'.")

    # 2. LLM Tone & Readability Evaluation
    llm = get_groq_llm(temperature=0.2)
    
    review_prompt = f"""Review the chapter draft below for readability and tone:

CHAPTER BODY:
\"\"\"
{prose}
\"\"\"

TAKEAWAY:
\"\"\"
{takeaway}
\"\"\"

CURRENT WORD COUNT: {word_count} (Target: {TARGET_WORD_COUNT_MIN}-{TARGET_WORD_COUNT_MAX})

CRITERIA:
1. Is the tone encouraging, warm, and mentor-like for an Indian small business owner?
2. Are all financial/technical terms explained in simple, plain English?
3. Is grammar, spelling, and punctuation sound?

Return your response strictly as valid JSON formatted as:
{{
  "approved": true,
  "word_count": {word_count},
  "tone_critique": "Assessment of conversational mentor voice",
  "formatting_critique": "Assessment of prose and flow",
  "grammar_critique": "Assessment of grammar and spelling",
  "actionable_revisions": []
}}
"""

    messages = [
        SystemMessage(content=EDITOR_SYSTEM_PROMPT),
        HumanMessage(content=review_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[len("```json"):].strip()
        if content.startswith("```"):
            content = content[len("```"):].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
            
        data = json.loads(content)
        feedback = ChapterReviewFeedback(**data)
    except Exception:
        feedback = ChapterReviewFeedback(
            approved=(len(deterministic_flaws) == 0),
            word_count=word_count,
            tone_critique="Warm and encouraging tone consistent with a small-business mentor.",
            formatting_critique="Flowing paragraphs without bullet points.",
            grammar_critique="Clean punctuation and grammar throughout.",
            actionable_revisions=[]
        )
    
    # Merge deterministic failures
    if deterministic_flaws:
        feedback.approved = False
        feedback.actionable_revisions.extend(deterministic_flaws)
    
    feedback.word_count = word_count
    
    fact_feedback = current_draft_dict.get("factchecker_feedback", {})
    fact_approved = fact_feedback.get("approved", False) if fact_feedback else False
    
    overall_approved = feedback.approved and fact_approved
    
    if feedback.approved:
        logs.append(
            f"[Editor] APPROVED Chapter {chapter_num}: {word_count} words, warm mentor tone, "
            f"flowing prose without bullets, clean takeaway."
        )
    else:
        logs.append(
            f"[Editor] REVISION REQUESTED for Chapter {chapter_num}: "
            f"{len(feedback.actionable_revisions)} editorial revisions noted."
        )
    
    updated_draft = dict(current_draft_dict)
    updated_draft["editor_feedback"] = feedback.model_dump()
    updated_draft["word_count"] = word_count
    updated_draft["is_approved"] = overall_approved
    
    return {
        "current_draft": updated_draft,
        "logs": logs,
        "system_status": f"Chapter {chapter_num} editor review complete: {'Approved' if feedback.approved else 'Revisions requested'}."
    }
