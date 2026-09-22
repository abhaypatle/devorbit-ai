from typing import TypedDict, Annotated, List, Any
import operator

class ProjectAgentState(TypedDict):
    project_id: str
    prompt: str
    messages: Annotated[List[Any], operator.add]
    next_agent: str
    task_complete: bool
    cloud_provider: str