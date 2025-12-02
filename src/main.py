"""Main entry point for AI Job Agent"""

import json
from datetime import datetime
from pathlib import Path

from src.graph import build_graph
from src.state import AgentState


def main():
    """Run the job agent workflow"""
    print("=" * 70)
    print("AI Job Agent - LangGraph Edition")
    print("=" * 70)

    # Build and run graph
    app = build_graph()
    initial_state: AgentState = {
        "raw_emails": [],
        "jobs": [],
        "duplicate_jobs": [],
        "filtered_jobs": [],
        "notifications_sent": 0,
        "analysis_summary": {},
    }

    print("\nRunning workflow...\n")
    final_state = app.invoke(initial_state)

    # Save complete analysis summary
    _save_analysis_summary(final_state)

    # Print summary
    print("\n" + "=" * 70)
    print("Workflow Complete")
    print("=" * 70)
    print(f"Emails processed: {len(final_state['raw_emails'])}")
    print(f"Jobs found: {len(final_state['jobs'])}")
    print(f"Jobs already sent: {len(final_state.get('duplicate_jobs', []))}")
    print(f"Jobs matched: {len(final_state['filtered_jobs'])}")
    print(f"Notifications sent: {final_state['notifications_sent']}")
    
    if final_state["filtered_jobs"]:
        print("\nMatched Jobs:")
        for i, job in enumerate(final_state["filtered_jobs"], 1):
            print(f"\n[{i}] {job['title']} @ {job['company']}")
            print(f"    Score: {job['score']}/100")
            print(f"    {job['link']}")
    else:
        print("\nNo matched jobs to send.")


def _save_analysis_summary(final_state: dict) -> None:
    """Save complete analysis summary including all processed jobs"""
    summary_dir = Path("logs")
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_file = summary_dir / f"analysis_summary_{timestamp}.json"
    test_results_file = summary_dir / f"test_results_{timestamp}.json"
    
    # Build comprehensive summary
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "emails_processed": len(final_state["raw_emails"]),
            "jobs_found": len(final_state["jobs"]),
            "jobs_already_sent": len(final_state.get("duplicate_jobs", [])),
            "jobs_matched": len(final_state["filtered_jobs"]),
            "notifications_sent": final_state["notifications_sent"],
        },
        "all_jobs_processed": [
            {
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "score": job.get("score", "N/A"),
                "reasons": job.get("reasons", ""),
                "link": job["link"],
                "status": "matched" if job in final_state["filtered_jobs"] else 
                         ("already_sent" if job in final_state.get("duplicate_jobs", []) else "filtered"),
            }
            for job in (final_state["jobs"] + final_state.get("duplicate_jobs", []))
        ],
        "duplicate_jobs": [
            {
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "link": job["link"],
                "status": "already_sent",
            }
            for job in final_state.get("duplicate_jobs", [])
        ],
        "matched_jobs": [
            {
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "score": job["score"],
                "reasons": job["reasons"],
                "link": job["link"],
            }
            for job in final_state["filtered_jobs"]
        ],
    }
    
    # Save full analysis to logs/
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    # Save simplified test results to logs/ (for quick tracking)
    test_results_data = {
        "timestamp": summary_data["timestamp"],
        "statistics": summary_data["statistics"],
        "matched_jobs_count": len(summary_data["matched_jobs"]),
        "matched_jobs_titles": [job["title"] for job in summary_data["matched_jobs"]],
    }
    with open(test_results_file, "w", encoding="utf-8") as f:
        json.dump(test_results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Full analysis saved to: {analysis_file}")
    print(f"✅ Test results saved to: {test_results_file}")


if __name__ == "__main__":
    main()
