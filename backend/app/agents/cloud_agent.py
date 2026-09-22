from langchain_core.messages import SystemMessage
from app.core.bedrock import get_bedrock_llm
from app.agents.state import ProjectAgentState
from app.services.enterprise_features import cloud_architecture_prompt

def cloud_node(state: ProjectAgentState):
    llm = get_bedrock_llm(temperature=0.2)
    provider = state.get("cloud_provider", "aws")
    prompt = cloud_architecture_prompt(provider, state.get("prompt", ""))
    messages = [SystemMessage(content=prompt)] + list(state.get("messages", []))
    
    response = llm.invoke(messages)
    
    return {
        "messages": [response],
        "next_agent": "END",
        "task_complete": True
    }