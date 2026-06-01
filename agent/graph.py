from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import InterviewState
from nodes import (node_ask_question, node_evaluate_answer,
                   node_update_profile, node_check_gaps, node_terminate)

MAX_TURNS = 15

def should_continue(state: InterviewState) -> str:
    if state["turn_count"] >= MAX_TURNS:
        return "terminate"
    if not state["missing_info"]:
        return "terminate"
    return "ask_question"

def build_graph():
    builder = StateGraph(InterviewState)

    builder.add_node("ask_question",    node_ask_question)
    builder.add_node("evaluate_answer", node_evaluate_answer)
    builder.add_node("update_profile",  node_update_profile)
    builder.add_node("check_gaps",      node_check_gaps)
    builder.add_node("terminate",       node_terminate)

    builder.set_entry_point("ask_question")
    builder.add_edge("ask_question",    "evaluate_answer")   # answer comes in between
    builder.add_edge("evaluate_answer", "update_profile")
    builder.add_edge("update_profile",  "check_gaps")
    builder.add_conditional_edges("check_gaps", should_continue, {
        "ask_question": "ask_question",
        "terminate":    "terminate",
    })
    builder.add_edge("terminate", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)
