"""LangGraph state definitions"""

from typing import List
from typing_extensions import TypedDict


class Requirement(TypedDict, total=False):
    """Single job requirement extracted from JD"""
    category: str  # language, framework, cloud, experience, etc.
    item: str  # Python, AWS, 3 years experience
    level: str  # 3+ years, proficient, expert
    priority: str  # must, preferred, nice_to_have


class MatchDetail(TypedDict, total=False):
    """Detailed match result for a single requirement"""
    requirement: str  # The requirement text
    evidence: str  # CV paragraph reference
    gap: str  # What's missing (for partial matches)
    reason: str  # Explanation (for gaps)


class EnhancedMatchResult(TypedDict, total=False):
    """Structured evaluation report from enhanced matching"""
    match_score: float  # 0-1 overall score
    strong_matches: List[MatchDetail]  # Fully matched requirements
    partial_matches: List[MatchDetail]  # Partially matched
    gaps: List[MatchDetail]  # Not matched
    cv_suggestions: List[str]  # Resume improvement suggestions


class Job(TypedDict, total=False):
    title: str
    company: str
    location: str
    link: str
    desc: str
    score: int  # Legacy: 0-100 score
    reasons: str  # Legacy: brief explanation
    # Enhanced matching fields
    requirements: List[Requirement]  # Extracted JD requirements
    enhanced_result: EnhancedMatchResult  # Detailed evaluation report


class AgentState(TypedDict):
    raw_emails: List[str]
    jobs: List[Job]
    duplicate_jobs: List[Job]  # Already sent jobs
    filtered_jobs: List[Job]
    notifications_sent: int
    analysis_summary: dict  # Summary of all processed data
