from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import InterviewState
from nodes import (
    node_init,
    node_router,
    node_evaluation,
    node_profile_builder,
    node_interviewer,
    node_wrap_up
)

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

    memory = MemorySaver()
    
    # Compile the graph with an interrupt before the evaluation node to capture candidate response
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["evaluation"]
    )
