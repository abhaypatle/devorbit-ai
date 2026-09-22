from langchain_core.messages import SystemMessage, AIMessage
from app.core.bedrock import get_bedrock_llm
from app.agents.state import ProjectAgentState

def planner_node(state: ProjectAgentState):
    llm = get_bedrock_llm(temperature=0.3)
    
    messages = [SystemMessage(content="You are Lead Planner.")]
    if "prompt" in state and state["prompt"]:
        messages.append(SystemMessage(content=f"User Request: {state['prompt']}"))
    messages.extend(list(state.get("messages", [])))
    
    response = llm.invoke(messages)
    
    # Ensure response is a LangChain message object or wrapped
    if isinstance(response, str):
        response = AIMessage(content=response)
        
    return {
        "messages": [response],
        "next_agent": "cloud_agent",
        "task_complete": False
    }