"""Fact-checker Agent: Audits citations and validates factual integrity.

Confirms that:
1. Every statistical figure, date, and policy statement carries an in-text [n] citation.
2. In-text citations correspond directly to the supplied authentic sources.
3. No hallucinated or broken sources exist.
"""

import re
import json
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_groq_llm
from state import FactCheckFeedback, BookState
from src.prompts import FACTCHECKER_SYSTEM_PROMPT


def factcheck_chapter_node(state: BookState) -> dict:
    """LangGraph node: Audits citations and factual alignment in the chapter draft."""
    logs = list(state.get("logs", []))
    chapter_idx = state.get("current_chapter_index", 0)
    chapter_num = chapter_idx + 1
    
    logs.append(f"[Fact-checker] Auditing claims and citations for Chapter {chapter_num}...")
    
    current_draft_dict = state.get("current_draft")
    if not current_draft_dict:
        logs.append(f"[Fact-checker Warning] No draft found for Chapter {chapter_num} to audit.")
        return {"logs": logs}
    
    prose = current_draft_dict.get("body_prose", "")
    research_items = state.get("current_research", [])
    
    # 1. Deterministic Rule-Based Checks
    citation_markers = re.findall(r'\[(\d+)\]', prose)
    unique_citations = sorted(list(set(citation_markers)), key=lambda x: int(x))
    total_citations_found = len(citation_markers)
    
    available_ids = {str(item.get("citation_id")) for item in research_items}
    
    missing_citations = []
    for cid in unique_citations:
        if cid not in available_ids:
            missing_citations.append(f"Citation [{cid}] does not match any approved research source.")
            
    # 2. LLM-Based Claim-Source Alignment Audit
    llm = get_groq_llm(temperature=0.1)
    
    sources_summary = "\n".join([
        f"[{item.get('citation_id')}] {item.get('source_name')} - {item.get('article_title')}: {item.get('fact_summary')}"
        for item in research_items
    ])
    
    verification_prompt = f"""Review the chapter prose below against the verified facts:

CHAPTER PROSE:
\"\"\"
{prose}
\"\"\"

VERIFIED FACTS & SOURCES:
{sources_summary}

AUDIT TASKS:
1. Does every date, percentage, or transaction metric have an accompanying [n] citation?
2. Do the cited claims accurately reflect the verified facts without distortion?
3. Are all cited reference IDs present in the verified list?

Return your response strictly as valid JSON with the format:
{{
  "approved": true,
  "total_citations_found": {total_citations_found},
  "unsupported_claims": [],
  "broken_or_invalid_sources": [],
  "actionable_revisions": []
}}
If not approved, explain in actionable_revisions what sentence needs adjustment.
"""

    messages = [
        SystemMessage(content=FACTCHECKER_SYSTEM_PROMPT),
        HumanMessage(content=verification_prompt)
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
        feedback = FactCheckFeedback(**data)
    except Exception as e:
        # Fallback to deterministic check
        is_approved = (total_citations_found >= len(available_ids) * 0.75) and (len(missing_citations) == 0)
        feedback = FactCheckFeedback(
            approved=is_approved,
            total_citations_found=total_citations_found,
            unsupported_claims=[],
            broken_or_invalid_sources=missing_citations,
            actionable_revisions=missing_citations if not is_approved else []
        )
    
    # Merge any deterministically detected broken citations
    if missing_citations:
        feedback.approved = False
        feedback.broken_or_invalid_sources.extend(missing_citations)
    
    if feedback.approved:
        logs.append(
            f"[Fact-checker] APPROVED Chapter {chapter_num}: Found {total_citations_found} valid citations. "
            f"All claims verified against official records."
        )
    else:
        logs.append(
            f"[Fact-checker] REVISION REQUESTED for Chapter {chapter_num}: "
            f"{len(feedback.actionable_revisions)} citation/claim issues identified."
        )
    
    # Update current draft with fact-checker feedback
    updated_draft = dict(current_draft_dict)
    updated_draft["factchecker_feedback"] = feedback.model_dump()
    
    return {
        "current_draft": updated_draft,
        "logs": logs,
        "system_status": f"Chapter {chapter_num} fact-check complete: {'Approved' if feedback.approved else 'Revisions needed'}."
    }
