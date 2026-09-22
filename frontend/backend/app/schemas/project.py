from pydantic import BaseModel

class OrchestratorRequest(BaseModel):
    project_id: str
    prompt: str