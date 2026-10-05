"""Planner Agent: Outlines the 3-chapter book structure.

Responsible for defining chapter themes, progression, and target data points
tailored for Indian small-business owners.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_groq_llm, BOOK_TITLE, TARGET_AUDIENCE
from state import BookOutline, ChapterOutline, BookState
from src.prompts import PLANNER_SYSTEM_PROMPT


def plan_book_node(state: BookState) -> dict:
    """LangGraph node: Generates the 3-chapter book outline.
    
    Args:
        state: The current BookState.
        
    Returns:
        Partial state update containing the generated outline and updated logs.
    """
    logs = list(state.get("logs", []))
    logs.append("[Planner] Initiating book structure design...")
    
    title = state.get("title", BOOK_TITLE)
    audience = state.get("target_audience", TARGET_AUDIENCE)
    
    llm = get_groq_llm(temperature=0.3)
    
    prompt_content = f"""Book Title: "{title}"
Target Reader: {audience}

Design the 3-chapter outline following the narrative arc:
1. Chapter 1: The Cash Dilemma and the Rise of UPI (Overcoming early fear, understanding NPCI/UPI basics).
2. Chapter 2: The Soundbox and the Street-Level Revolution (Everyday commerce, audio alerts, QR codes, building consumer trust).
3. Chapter 3: Beyond Payments: Credit, Growth, and the Future (Formal financial inclusion, cashflow-based micro-loans, digitizing shop records).

Return your response as a valid JSON object matching this schema:
{{
  "title": "{title}",
  "target_audience": "{audience}",
  "narrative_theme": "A practical, reassuring journey from cash friction to digital empowerment for Indian shopkeepers",
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "Chapter title",
      "summary": "Chapter summary",
      "target_data_points": ["Stat or milestone 1", "Stat or milestone 2", "Stat or milestone 3"]
    }},
    ...
  ]
}}
Only return raw JSON without markdown code fences or conversational text.
"""
    
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content)
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    
    # Strip any accidental markdown formatting
    if content.startswith("```json"):
        content = content[len("```json"):].strip()
    if content.startswith("```"):
        content = content[len("```"):].strip()
    if content.endswith("```"):
        content = content[:-3].strip()
        
    try:
        data = json.loads(content)
        outline = BookOutline(**data)
    except Exception as e:
        # Fallback to robust default outline if LLM json formatting had a hitch
        logs.append(f"[Planner Warning] JSON parsing error ({e}), using robust structured template.")
        outline = BookOutline(
            title=title,
            target_audience=audience,
            narrative_theme="How UPI transformed small enterprise operations from cash headaches to formal growth in India",
            chapters=[
                ChapterOutline(
                    chapter_number=1,
                    title="The Cash Dilemma and the Dawn of Digital Trust",
                    summary="Explores the challenges of handling physical cash, change shortages, and counterfeit risk, followed by the breakthrough launch of UPI in 2016 by NPCI.",
                    target_data_points=[
                        "Launch of UPI in April 2016 by National Payments Corporation of India (NPCI) under RBI guidance",
                        "Initial merchant hesitation regarding digital fraud and banking delays",
                        "Interoperability: how one QR code connected all bank accounts seamlessly"
                    ]
                ),
                ChapterOutline(
                    chapter_number=2,
                    title="The Soundbox and the Street-Level Revolution",
                    summary="Examines how QR codes and audio confirmation soundboxes eliminated payment mistrust at busy retail counters and supercharged everyday adoption.",
                    target_data_points=[
                        "Rise of QR codes and zero Merchant Discount Rate (MDR) policy enacted by the Government of India",
                        "Invention and massive deployment of audio soundbox devices providing real-time voice confirmations",
                        "Explosive monthly transaction milestones exceeding 10 billion transactions on UPI"
                    ]
                ),
                ChapterOutline(
                    chapter_number=3,
                    title="Beyond Payments: Unlocking Credit and the Future of Retail",
                    summary="Shows how daily digital transaction footprints empower kirana stores to access collateral-free business loans, digital bookkeeping, and future innovations like credit on UPI.",
                    target_data_points=[
                        "Transition from physical collateral to cash-flow based formal lending using UPI transaction history",
                        "Reserve Bank of India (RBI) initiative linking RuPay credit cards to UPI for merchant transactions",
                        "Long-term financial security and digital bookkeeping for micro and small enterprises"
                    ]
                )
            ]
        )
    
    logs.append(f"[Planner] Generated comprehensive outline with {len(outline.chapters)} chapters.")
    
    return {
        "outline": outline.model_dump(),
        "logs": logs,
        "system_status": "Outline completed. Proceeding to Chapter 1 research."
    }
