from langgraph.graph import StateGraph, END
from app.agents.state import ProjectAgentState
from app.agents.planner_agent import planner_node
from app.agents.cloud_agent import cloud_node

def build_orchestrator_graph():
    workflow = StateGraph(ProjectAgentState)
    
    # 1. Add Agent Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("cloud_agent", cloud_node)
    
    # 2. Set Entry Point
    workflow.set_entry_point("planner")
    
    # 3. Add Edges
    workflow.add_edge("planner", "cloud_agent")
    workflow.add_edge("cloud_agent", END)
    
    return workflow.compile()

orchestrator_app = build_orchestrator_graph()