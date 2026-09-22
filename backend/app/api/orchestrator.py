import json
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from sse_starlette.sse import EventSourceResponse
from app.agents.graph import orchestrator_graph
from langchain_core.messages import HumanMessage

router = APIRouter()

class ProjectRequest(BaseModel):
    project_id: str
    prompt: str
    cloud_provider: Literal["aws", "azure", "gcp"] = Field(default="aws")

@router.post("/run")
async def run_orchestrator(request: ProjectRequest):
    try:
        initial_state = {
            "project_id": request.project_id,
            "prompt": request.prompt,
            "messages": [HumanMessage(content=request.prompt)],
            "next_agent": "planner_agent",
            "task_complete": False
            ,"cloud_provider": request.cloud_provider
        }
        
        result = orchestrator_graph.invoke(initial_state)
        
        output_messages = []
        for msg in result.get("messages", []):
            if hasattr(msg, "type") and hasattr(msg, "content"):
                output_messages.append({"role": msg.type, "content": msg.content})
            elif isinstance(msg, dict):
                output_messages.append({"role": msg.get("role", "ai"), "content": msg.get("content", "")})
            else:
                output_messages.append({"role": "ai", "content": str(msg)})
        
        return {
            "status": "success",
            "project_id": result.get("project_id"),
            "messages": output_messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_orchestrator(request: ProjectRequest):
    """
    Streams multi-agent updates in real time using Server-Sent Events (SSE).
    """
    async def event_generator():
        initial_state = {
            "project_id": request.project_id,
            "prompt": request.prompt,
            "messages": [HumanMessage(content=request.prompt)],
            "next_agent": "planner_agent",
            "task_complete": False
            ,"cloud_provider": request.cloud_provider
        }

        # Stream node updates as agents complete their tasks
        for output in orchestrator_graph.stream(initial_state):
            for node_name, node_state in output.items():
                messages = node_state.get("messages", [])
                latest_msg = messages[-1] if messages else None
                content = latest_msg.content if latest_msg else ""
                
                payload = {
                    "agent": node_name,
                    "content": content
                }
                yield {
                    "event": "agent_update",
                    "data": json.dumps(payload)
                }
                await asyncio.sleep(0.5)

        yield {
            "event": "complete",
            "data": json.dumps({"status": "finished"})
        }

    return EventSourceResponse(event_generator())