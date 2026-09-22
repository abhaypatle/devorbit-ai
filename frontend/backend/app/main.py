from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="DevOrbit AI Backend Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrchestratorRequest(BaseModel):
    project_id: str
    prompt: str

@app.get("/")
def read_root():
    return {"message": "DevOrbit AI Core Engine Active"}

@app.post("/api/v1/orchestrator/run")
def run_orchestrator(payload: OrchestratorRequest):
    p = payload.prompt.lower()
    pid = payload.project_id

    # 1. SERVERLESS ARCHITECTURE
    if "serverless" in p or "lambda" in p or "dynamodb" in p:
        return {
            "status": "success",
            "diagram": "lambda dynamodb serverless api gateway",
            "messages": [
                {"role": "human", "content": payload.prompt},
                {"role": "ai", "content": f"Serverless Strategy for {pid}"},
                {"role": "ai", "content": "AWS Lambda & API Gateway Blueprint"},
                {"role": "ai", "content": f'resource "aws_lambda_function" "api_{pid}" {{\n  function_name = "{pid}_lambda"\n  handler       = "index.handler"\n  runtime       = "nodejs18.x"\n}}'}
            ]
        }

    # 2. CONTAINER ARCHITECTURE
    elif "container" in p or "fargate" in p or "ecs" in p:
        return {
            "status": "success",
            "diagram": "container ecs fargate redis",
            "messages": [
                {"role": "human", "content": payload.prompt},
                {"role": "ai", "content": f"Container Strategy for {pid}"},
                {"role": "ai", "content": "ECS Fargate & ElastiCache Blueprint"},
                {"role": "ai", "content": f'resource "aws_ecs_cluster" "cluster_{pid}" {{\n  name = "{pid}-ecs-cluster"\n}}'}
            ]
        }

    # 3. DEFAULT MULTI-AZ EC2 + RDS
    else:
        return {
            "status": "success",
            "diagram": "multi-az ec2 rds autoscale",
            "messages": [
                {"role": "human", "content": payload.prompt},
                {"role": "ai", "content": f"Multi-AZ EC2 Strategy for {pid}"},
                {"role": "ai", "content": "EC2 + RDS Blueprint"},
                {"role": "ai", "content": f'resource "aws_db_instance" "db_{pid}" {{\n  engine         = "postgres"\n  instance_class = "db.t4g.micro"\n  multi_az       = true\n}}'}
            ]
        }