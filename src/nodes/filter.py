"""Filter jobs by score and deduplicate"""

import json
import os
from typing import List

from src.config import config


class JobFilter:
    """Filter jobs by threshold and deduplicate against history"""

    def __init__(self, history_path: str, threshold: int):
        self.history_path = history_path
        self.threshold = threshold
        self.history = self._load_history()

    def _load_history(self) -> set:
        """Load sent job links from history file"""
        if not os.path.exists(self.history_path):
            return set()

        try:
            with open(self.history_path, "r") as f:
                data = json.load(f)
                return set(data.get("sent_jobs", []))
        except Exception:
            return set()

    def _save_history(self):
        """Save history to file"""
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        with open(self.history_path, "w") as f:
            json.dump({"sent_jobs": list(self.history)}, f, indent=2)

    def _mark_jobs_as_processed(self, jobs: List[dict]) -> None:
        """Mark jobs as processed (seen) to avoid re-analyzing them later"""
        for job in jobs:
            self.history.add(job["link"])
        self._save_history()

    def deduplicate_jobs(self, jobs: List[dict]) -> tuple:
        """Deduplicate jobs against history before analysis, exclude senior roles
        
        Returns:
            (new_jobs, duplicate_jobs) - jobs to analyze and already sent jobs
        """
        new_jobs = []
        duplicate_jobs = []
        excluded_jobs = []

        for job in jobs:
            # Exclude senior positions
            if self._is_senior_role(job["title"]):
                excluded_jobs.append(job)
                continue
            
            if job["link"] in self.history:
                duplicate_jobs.append(job)
            else:
                new_jobs.append(job)

        if excluded_jobs:
            print(f"⏭️  Excluded {len(excluded_jobs)} senior/lead roles")

        return new_jobs, duplicate_jobs

    def _is_senior_role(self, title: str) -> bool:
        """Check if job title is a senior/lead position"""
        excluded_keywords = [
            "senior",
            "lead",
            "principal",
            "architect",
            "director",
            "manager",
            "head of",
        ]
        
        title_lower = title.lower()
        for keyword in excluded_keywords:
            if keyword in title_lower:
                return True
        
        return False

    def filter_jobs(self, jobs: List[dict]) -> List[dict]:
        """Filter jobs by threshold and remove duplicates"""
        filtered = []

        for job in jobs:
            # Check threshold
            if job.get("score", 0) < self.threshold:
                continue

            # Check if already sent
            if job["link"] in self.history:
                continue

            filtered.append(job)
            self.history.add(job["link"])

        # Save updated history
        if filtered:
            self._save_history()

        return filtered


def deduplicate_jobs(state: dict) -> dict:
    """LangGraph node: Deduplicate jobs BEFORE AI analysis (save tokens)"""
    job_filter = JobFilter(config.history_path, config.match_threshold)
    all_jobs = state.get("jobs", [])
    
    # Deduplicate before analysis and exclude senior roles
    new_jobs, duplicate_jobs = job_filter.deduplicate_jobs(all_jobs)
    
    # Count excluded senior/lead roles
    excluded_count = len(all_jobs) - len(new_jobs) - len(duplicate_jobs)
    
    # Only keep new jobs for analysis
    state["jobs"] = new_jobs
    state["duplicate_jobs"] = duplicate_jobs
    
    print(f"📊 Deduplication result:")
    print(f"   • Total jobs: {len(all_jobs)}")
    print(f"   • Excluded (senior/lead): {excluded_count}")
    print(f"   • Already sent: {len(duplicate_jobs)}")
    print(f"   • To analyze: {len(new_jobs)}")

    # Note: Jobs will be added to history in filter_jobs after scoring
    # Don't mark them here, or they'll be skipped in filter_jobs

    return state


def filter_jobs(state: dict) -> dict:
    """LangGraph node: Filter jobs by score and mark as sent"""
    job_filter = JobFilter(config.history_path, config.match_threshold)
    filtered = job_filter.filter_jobs(state.get("jobs", []))
    state["filtered_jobs"] = filtered
    return state
