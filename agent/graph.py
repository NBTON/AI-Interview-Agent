from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import InterviewState
from nodes import (node_init, node_router, node_evaluate_and_extract,
                   node_generate_question, node_wrap_up)

MAX_TURNS = 15

def node_router_pass_through(state: InterviewState) -> dict:
    """Pass-through node to serve as a source for conditional routing."""
    return {}

def build_graph():
    builder = StateGraph(InterviewState)

    # Add nodes
    builder.add_node("init", node_init)
    builder.add_node("router_node", node_router_pass_through)
    builder.add_node("evaluate_and_extract", node_evaluate_and_extract)
    builder.add_node("generate_question", node_generate_question)
    builder.add_node("wrap_up", node_wrap_up)

    # Set entry point
    builder.set_entry_point("init")

    # Define edges
    builder.add_edge("init", "router_node")
    builder.add_edge("evaluate_and_extract", "router_node")
    
    # Conditional routing from router_node using node_router
    builder.add_conditional_edges("router_node", node_router, {
        "evaluate": "evaluate_and_extract",
        "generate_question": "generate_question",
        "wrap_up": "wrap_up",
    })
    
    # generate_question points directly to evaluate_and_extract. 
    # Because evaluate_and_extract is in interrupt_before, this transition pauses execution.
    builder.add_edge("generate_question", "evaluate_and_extract")
    
    # wrap_up node completes the process
    builder.add_edge("wrap_up", END)

    memory = MemorySaver()
    
    # Compile with interrupt_before evaluating candidate answers
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["evaluate_and_extract"]
    )
