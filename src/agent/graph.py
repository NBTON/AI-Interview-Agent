from langgraph.graph import StateGraph, END
from state import InterviewState
from nodes import (
    node_init,
    node_router,
    node_evaluation,
    node_profile_builder,
    node_interviewer,
    node_wrap_up
)
from db import get_postgres_dsn

_postgres_conn = None
_postgres_checkpointer = None


def _build_checkpointer():
    """Use persistent PostgreSQL checkpoints when configured."""
    global _postgres_conn, _postgres_checkpointer

    dsn = get_postgres_dsn()
    if not dsn:
        raise RuntimeError(
            "Persistent checkpointing is required. Set SUPABASE_DB_URL, DATABASE_URL, POSTGRES_URL, "
            "or SUPABASE_DB_PASSWORD with SUPABASE_URL."
        )

    from langgraph.checkpoint.postgres import PostgresSaver
    import psycopg
    from psycopg.rows import dict_row

    _postgres_conn = psycopg.connect(
        dsn,
        autocommit=True,
        row_factory=dict_row,
        prepare_threshold=None,
    )
    _postgres_checkpointer = PostgresSaver(_postgres_conn)
    _postgres_checkpointer.setup()
    return _postgres_checkpointer

def node_router_pass_through(state: InterviewState) -> dict:
    """Pass-through node to serve as a source for conditional routing."""
    return {}

def build_graph():
    builder = StateGraph(InterviewState)

    # Add agent nodes
    builder.add_node("init", node_init)
    builder.add_node("router_node", node_router_pass_through)
    builder.add_node("interviewer", node_interviewer)
    builder.add_node("evaluation", node_evaluation)
    builder.add_node("profile_builder", node_profile_builder)
    builder.add_node("wrap_up", node_wrap_up)

    # Set entry point
    builder.set_entry_point("init")

    # Define simple edges
    builder.add_edge("init", "router_node")
    builder.add_edge("profile_builder", "router_node")
    
    # Conditional routing from router_node using node_router
    builder.add_conditional_edges("router_node", node_router, {
        "evaluate": "evaluation",
        "generate_question": "interviewer",
        "wrap_up": "wrap_up",
    })
    
    # The interviewer generates a question, then transition points to evaluation.
    # Since evaluation is in interrupt_before, the graph pauses here.
    builder.add_edge("interviewer", "evaluation")
    builder.add_edge("evaluation", "profile_builder")
    
    # wrap_up completes the interview
    builder.add_edge("wrap_up", END)

    checkpointer = _build_checkpointer()
    
    # Compile the graph with an interrupt before the evaluation node to capture candidate response
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["evaluation"]
    )
