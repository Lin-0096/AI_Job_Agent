"""JD requirements extractor using lightweight LLM"""

import json
from typing import List

from langchain_openai import ChatOpenAI

from src.config import config
from src.state import Requirement


class JDExtractor:
    """Extract structured requirements from job posting using lightweight LLM.

    Uses gpt-4o-mini to parse job title/description into structured requirements.
    This is Stage A of the two-stage matching process, optimized for low token cost.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=config.llm.api_key,
            model=config.match.extract_model,
            temperature=0.1,
        )

    def extract_requirements(self, job: dict) -> List[Requirement]:
        """Extract requirements from job posting.

        Args:
            job: Job dict with title, company, location, desc

        Returns:
            List of structured Requirement dicts
        """
        prompt = self._build_prompt(job)

        try:
            response = self.llm.invoke(prompt)
            requirements = self._parse_response(response.content)
            return requirements

        except Exception as e:
            # Fallback: return basic requirement from title
            return [
                {
                    "category": "role",
                    "item": job.get("title", "Unknown"),
                    "level": "",
                    "priority": "must",
                }
            ]

    def _build_prompt(self, job: dict) -> str:
        """Build extraction prompt.

        Designed to be minimal to save tokens while extracting key info.
        """
        title = job.get("title", "")
        company = job.get("company", "")
        desc = job.get("desc", "")

        # Construct job info, only include non-empty fields
        job_info = f"Title: {title}"
        if company:
            job_info += f"\nCompany: {company}"
        if desc:
            job_info += f"\nDescription: {desc}"

        return f"""Extract job requirements from the posting below.

{job_info}

Output JSON array of requirements. Each requirement:
- category: language/framework/cloud/database/experience/domain/soft_skill
- item: specific skill or requirement
- level: experience level if mentioned (e.g., "3+ years", "proficient")
- priority: must/preferred/nice_to_have

Example output:
[
  {{"category": "language", "item": "Python", "level": "3+ years", "priority": "must"}},
  {{"category": "framework", "item": "Django", "level": "proficient", "priority": "preferred"}}
]

Infer requirements from title if description is empty.
Output ONLY JSON array:"""

    def _parse_response(self, response: str) -> List[Requirement]:
        """Parse LLM response into Requirement list."""
        try:
            response = response.strip()

            # Remove markdown code blocks if present
            if response.startswith("```"):
                lines = response.split("\n")
                # Find end of code block
                end_idx = -1
                for i in range(len(lines) - 1, 0, -1):
                    if lines[i].strip() == "```":
                        end_idx = i
                        break
                response = "\n".join(lines[1:end_idx])

            # Parse JSON
            requirements = json.loads(response)

            if not isinstance(requirements, list):
                return []

            # Validate and normalize each requirement
            validated = []
            for req in requirements:
                if isinstance(req, dict) and "item" in req:
                    validated.append(
                        {
                            "category": req.get("category", "other"),
                            "item": req["item"],
                            "level": req.get("level", ""),
                            "priority": req.get("priority", "must"),
                        }
                    )

            return validated

        except Exception:
            return []


def extract_requirements(state: dict) -> dict:
    """LangGraph node: Extract requirements from all jobs.

    This node runs after parse_jobs and before match_jobs.
    Only extracts for jobs that will go through enhanced matching.
    """
    if not config.match.use_enhanced:
        # Skip if enhanced matching is disabled
        return state

    extractor = JDExtractor()
    jobs = state.get("jobs", [])

    for job in jobs:
        # Skip if already has requirements
        if "requirements" in job and job["requirements"]:
            continue

        requirements = extractor.extract_requirements(job)
        job["requirements"] = requirements

    state["jobs"] = jobs
    return state
