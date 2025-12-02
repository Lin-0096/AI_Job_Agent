"""LangGraph workflow definition"""

from langgraph.graph import StateGraph, END

from src.state import AgentState
from src.nodes.email_reader import read_emails
from src.nodes.job_parser import parse_jobs
from src.nodes.filter import deduplicate_jobs
from src.nodes.jd_extractor import extract_requirements
from src.nodes.matcher import match_jobs
from src.nodes.filter import filter_jobs
from src.nodes.notifier import notify_jobs


def build_graph():
    """Build the job agent workflow graph.

    Workflow:
    read_emails → parse_jobs → deduplicate_jobs → extract_requirements → match_jobs → filter_jobs → notify_jobs
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("read_emails", read_emails)
    graph.add_node("parse_jobs", parse_jobs)
    graph.add_node("deduplicate_jobs", deduplicate_jobs)
    graph.add_node("extract_requirements", extract_requirements)  # Stage A: JD extraction
    graph.add_node("match_jobs", match_jobs)  # Stage B: Deep matching
    graph.add_node("filter_jobs", filter_jobs)
    graph.add_node("notify_jobs", notify_jobs)

    # Set entry point
    graph.set_entry_point("read_emails")

    # Add edges
    graph.add_edge("read_emails", "parse_jobs")
    graph.add_edge("parse_jobs", "deduplicate_jobs")
    graph.add_edge("deduplicate_jobs", "extract_requirements")
    graph.add_edge("extract_requirements", "match_jobs")
    graph.add_edge("match_jobs", "filter_jobs")
    graph.add_edge("filter_jobs", "notify_jobs")
    graph.add_edge("notify_jobs", END)

    return graph.compile()
