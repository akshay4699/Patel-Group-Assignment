"""State models and data contracts for the Multi-Agent Book Writer workflow.

Defines schemas for outlines, research items, citations, drafts, and the shared
LangGraph state.
"""

from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class ChapterOutline(BaseModel):
    """Outline specifications for a single chapter."""
    chapter_number: int = Field(description="Sequential chapter number (1, 2, 3)")
    title: str = Field(description="Descriptive chapter title")
    summary: str = Field(description="Summary of chapter objective and narrative arc")
    target_data_points: List[str] = Field(
        default_factory=list,
        description="Key statistics, historical dates, and milestones to address"
    )


class BookOutline(BaseModel):
    """Complete structural plan for the book."""
    title: str = Field(description="Overall title of the book")
    target_audience: str = Field(description="Target reader persona")
    narrative_theme: str = Field(description="Core overarching theme linking all chapters")
    chapters: List[ChapterOutline] = Field(description="Ordered list of chapter outlines")


class ResearchItem(BaseModel):
    """A verified factual research point with an authentic source citation."""
    citation_id: int = Field(description="Numbered index matching in-text reference [n]")
    fact_summary: str = Field(description="The key factual claim, date, or statistic")
    source_name: str = Field(description="Publishing entity (e.g., NPCI, RBI, Press Information Bureau, Reuters)")
    article_title: str = Field(description="Title of the article, report, or press release")
    url: str = Field(description="Public, accessible link to the reference")
    is_verified: bool = Field(default=True, description="Whether the link and claim are validated")


class ChapterReviewFeedback(BaseModel):
    """Review results from the Editor agent."""
    approved: bool = Field(description="True if the chapter meets all editorial standards")
    word_count: int = Field(description="Calculated word count of the chapter body")
    tone_critique: str = Field(description="Assessment of conversational, encouraging tone")
    formatting_critique: str = Field(description="Assessment of flowing prose and absence of bullet points")
    grammar_critique: str = Field(description="Assessment of grammar, punctuation, and clarity")
    actionable_revisions: List[str] = Field(
        default_factory=list,
        description="Specific instructions for the writer if not approved"
    )


class FactCheckFeedback(BaseModel):
    """Verification results from the Fact-checker agent."""
    approved: bool = Field(description="True if all claims are backed by authentic citations")
    total_citations_found: int = Field(description="Count of [n] citation anchors in prose")
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Claims lacking citations or misrepresenting the source"
    )
    broken_or_invalid_sources: List[str] = Field(
        default_factory=list,
        description="Sources that appear fabricated or inaccessible"
    )
    actionable_revisions: List[str] = Field(
        default_factory=list,
        description="Instructions for the writer/researcher to resolve inaccuracies"
    )


class ChapterDraft(BaseModel):
    """Draft payload for an individual chapter during drafting & review."""
    chapter_number: int = Field(description="Chapter index (1-based)")
    title: str = Field(description="Title of the chapter")
    body_prose: str = Field(
        description="The written prose without bullet points, including [n] citation markers"
    )
    takeaway: str = Field(
        description="Single summary sentence starting strictly with 'Takeaway:'"
    )
    references: List[ResearchItem] = Field(
        default_factory=list,
        description="Numbered citation list corresponding to in-text anchors"
    )
    word_count: int = Field(default=0, description="Word count of body_prose + takeaway")
    revision_count: int = Field(default=0, description="How many revision loops this chapter has undergone")
    
    # Review statuses
    editor_feedback: Optional[ChapterReviewFeedback] = None
    factchecker_feedback: Optional[FactCheckFeedback] = None
    is_approved: bool = Field(default=False, description="Approved by both Editor and Fact-checker")


class BookState(TypedDict):
    """The shared state dictionary orchestrated by LangGraph."""
    # Book Metadata
    title: str
    target_audience: str
    
    # Planning
    outline: Optional[Dict[str, Any]]
    
    # Current Execution Pointer
    current_chapter_index: int  # 0-indexed: 0, 1, 2
    total_chapters: int
    
    # Active Chapter Workspace
    current_research: List[Dict[str, Any]]
    current_draft: Optional[Dict[str, Any]]
    
    # Iteration & Safety Guards
    current_revision_count: int
    max_revisions: int
    
    # Completed Final Chapters
    completed_chapters: List[Dict[str, Any]]
    
    # Operational Logs & Status
    logs: List[str]
    system_status: str
