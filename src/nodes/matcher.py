"""LLM-based job matching node with enhanced evaluation support"""

import json
from typing import List

from langchain_openai import ChatOpenAI
from openai import OpenAI

from src.config import config
from src.state import EnhancedMatchResult, MatchDetail
from src.utils import CVLoader


class JobMatcher:
    """Legacy matcher: Simple score + reasons using LLM"""

    def __init__(self, cv_path: str):
        self.cv_content = CVLoader.load_cv(cv_path)
        self.llm = ChatOpenAI(
            api_key=config.llm.api_key,
            model=config.llm.model,
            temperature=0.1,
        )

    def match_job(self, job: dict) -> dict:
        """Match a single job against CV, return updated job with score and reasons"""
        prompt = self._build_prompt(job)

        try:
            response = self.llm.invoke(prompt)
            result = self._parse_response(response.content)

            job["score"] = result["score"]
            job["reasons"] = result["reasons"]

        except Exception as e:
            job["score"] = 0
            job["reasons"] = f"Error during matching: {str(e)}"

        return job

    def _build_prompt(self, job: dict) -> str:
        """Build matching prompt for LLM"""
        return f"""You are a job matching engine. Analyze how well a candidate's CV matches a job posting.

**Candidate's CV:**
{self.cv_content}

**Job Posting:**
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Link: {job['link']}

**Instructions:**
1. Analyze the match between the CV and job requirements
2. Consider: skills, experience level, technologies, domain knowledge
3. Return a JSON object with:
   - "score": integer from 0-100 (0=no match, 100=perfect match)
   - "reasons": brief explanation (2-3 sentences)

Focus on concrete skill matches and experience relevance. Be realistic but fair.

Return ONLY the JSON object, no other text:"""

    def _parse_response(self, response: str) -> dict:
        """Parse LLM response to extract score and reasons"""
        try:
            response = response.strip()

            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            result = json.loads(response)

            if "score" not in result or "reasons" not in result:
                raise ValueError("Missing required fields")

            score = int(result["score"])
            if not 0 <= score <= 100:
                score = max(0, min(100, score))

            return {"score": score, "reasons": result["reasons"]}

        except Exception:
            return {"score": 0, "reasons": "Failed to parse LLM response"}


class EnhancedJobMatcher:
    """Enhanced matcher: Detailed evaluation report using reasoning model.

    Uses o3-mini with reasoning_effort for deep analysis.
    Produces structured evaluation with evidence tracing.
    """

    def __init__(self, cv_path: str):
        # Load CV with paragraph numbers for evidence tracing
        self.cv_content = CVLoader.load_cv_with_paragraphs(cv_path)
        self.client = OpenAI(api_key=config.llm.api_key)

    def match_job(self, job: dict) -> dict:
        """Match job with detailed evaluation report.

        Args:
            job: Job dict with title, company, requirements

        Returns:
            Updated job with score, reasons, and enhanced_result
        """
        prompt = self._build_prompt(job)

        try:
            # Use reasoning model with effort control
            response = self.client.chat.completions.create(
                model=config.match.match_model,
                reasoning_effort=config.match.reasoning_effort,
                messages=[{"role": "user", "content": prompt}],
            )

            result = self._parse_response(response.choices[0].message.content)

            # Set legacy fields for compatibility
            job["score"] = int(result.get("match_score", 0) * 100)
            job["reasons"] = self._generate_summary(result)
            job["enhanced_result"] = result

        except Exception as e:
            # Fallback to basic result
            job["score"] = 0
            job["reasons"] = f"Enhanced matching error: {str(e)}"
            job["enhanced_result"] = {
                "match_score": 0,
                "strong_matches": [],
                "partial_matches": [],
                "gaps": [],
                "cv_suggestions": [],
            }

        return job

    def _build_prompt(self, job: dict) -> str:
        """Build evaluation prompt for reasoning model.

        Designed to be concise - the model's internal reasoning handles complexity.
        """
        # Format requirements if available
        requirements = job.get("requirements", [])
        if requirements:
            req_text = "\n".join(
                [
                    f"- {r.get('item', '')} ({r.get('level', '')}) [{r.get('priority', 'must')}]"
                    for r in requirements
                ]
            )
        else:
            req_text = f"Infer from title: {job.get('title', '')}"

        return f"""Job matching evaluation.

## Resume (with paragraph numbers)
{self.cv_content}

## Job Information
Title: {job.get('title', '')}
Company: {job.get('company', '')}

## Job Requirements
{req_text}

## Output JSON
{{
  "match_score": 0.0-1.0,
  "strong_matches": [{{"requirement": "...", "evidence": "Paragraph N: ..."}}],
  "partial_matches": [{{"requirement": "...", "evidence": "Paragraph N: ...", "gap": "..."}}],
  "gaps": [{{"requirement": "...", "reason": "..."}}],
  "cv_suggestions": ["..."]
}}

Output ONLY JSON."""

    def _parse_response(self, response: str) -> EnhancedMatchResult:
        """Parse reasoning model response into structured result."""
        try:
            response = response.strip()

            # Remove code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                end_idx = -1
                for i in range(len(lines) - 1, 0, -1):
                    if lines[i].strip() == "```":
                        end_idx = i
                        break
                response = "\n".join(lines[1:end_idx])

            result = json.loads(response)

            # Validate and normalize
            return {
                "match_score": float(result.get("match_score", 0)),
                "strong_matches": result.get("strong_matches", []),
                "partial_matches": result.get("partial_matches", []),
                "gaps": result.get("gaps", []),
                "cv_suggestions": result.get("cv_suggestions", []),
            }

        except Exception:
            return {
                "match_score": 0,
                "strong_matches": [],
                "partial_matches": [],
                "gaps": [],
                "cv_suggestions": [],
            }

    def _generate_summary(self, result: EnhancedMatchResult) -> str:
        """Generate brief summary from enhanced result for legacy compatibility."""
        strong = len(result.get("strong_matches", []))
        partial = len(result.get("partial_matches", []))
        gaps = len(result.get("gaps", []))

        parts = []
        if strong:
            parts.append(f"{strong} strong match(es)")
        if partial:
            parts.append(f"{partial} partial match(es)")
        if gaps:
            parts.append(f"{gaps} gap(s)")

        return ", ".join(parts) if parts else "No match info"


def match_jobs(state: dict) -> dict:
    """LangGraph node: Match jobs against CV using LLM.

    Uses EnhancedJobMatcher if enabled in config, otherwise legacy JobMatcher.
    """
    if config.match.use_enhanced:
        matcher = EnhancedJobMatcher(config.cv_path)
    else:
        matcher = JobMatcher(config.cv_path)

    matched_jobs = []
    for job in state.get("jobs", []):
        matched_job = matcher.match_job(job)
        matched_jobs.append(matched_job)

    state["jobs"] = matched_jobs
    return state
