from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    generate_analysis,
    prepare_context,
)
from app.graph.schemas import RiskGraphState


def build_risk_graph():
    graph = StateGraph(RiskGraphState)

    graph.add_node(
        "prepare_context",
        prepare_context,
    )

    graph.add_node(
        "generate_analysis",
        generate_analysis,
    )

    graph.add_edge(
        START,
        "prepare_context",
    )

    graph.add_edge(
        "prepare_context",
        "generate_analysis",
    )

    graph.add_edge(
        "generate_analysis",
        END,
    )

    return graph.compile()
