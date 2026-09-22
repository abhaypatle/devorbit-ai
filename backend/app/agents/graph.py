from langgraph.graph import StateGraph, END
from app.agents.state import ProjectAgentState
from app.agents.planner_agent import planner_node
from app.agents.cloud_agent import cloud_node

def router(state: ProjectAgentState):
    if state.get("task_complete"):
        return END
    return state.get("next_agent", "cloud_agent")

workflow = StateGraph(ProjectAgentState)

workflow.add_node("planner_agent", planner_node)
workflow.add_node("cloud_agent", cloud_node)

workflow.set_entry_point("planner_agent")

workflow.add_conditional_edges(
    "planner_agent",
    router,
    {
        "cloud_agent": "cloud_agent",
        END: END
    }
)

workflow.add_conditional_edges(
    "cloud_agent",
    router,
    {
        END: END
    }
)

orchestrator_graph = workflow.compile()