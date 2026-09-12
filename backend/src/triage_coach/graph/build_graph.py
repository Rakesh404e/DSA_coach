"""Assembly and compilation of the Triage Coach StateGraph."""

from langgraph.graph import END, START, StateGraph

from triage_coach.graph.nodes import (
    classify_failure_node,
    escalate_check_node,
    generate_hint_node,
    run_tests_node,
)
from triage_coach.graph.routing import (
    route_after_classification,
    route_after_tests,
)
from triage_coach.graph.state import TriageState

builder = StateGraph(TriageState)

builder.add_node("run_tests", run_tests_node)
builder.add_node("classify_failure", classify_failure_node)
builder.add_node("generate_hint", generate_hint_node)
builder.add_node("escalate_check", escalate_check_node)

builder.add_edge(START, "run_tests")

builder.add_conditional_edges(
    "run_tests",
    route_after_tests,
    {
        "classify_failure": "classify_failure",
        "resolved": END,
    },
)

builder.add_conditional_edges(
    "classify_failure",
    route_after_classification,
    {
        "generate_hint": "generate_hint",
        "end": END,
    },
)

builder.add_edge("generate_hint", END)
builder.add_edge("escalate_check", "generate_hint")

graph = builder.compile()
