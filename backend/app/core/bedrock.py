import os
from langchain_core.language_models.fake import FakeListLLM
from langchain_aws import ChatBedrock
from dotenv import load_dotenv

load_dotenv()

# Pre-created shared instance so fake responses increment sequentially across agent calls
_SHARED_MOCK_LLM = FakeListLLM(responses=[
    "### 📋 Lead Planner Agent Strategy\n1. Multi-AZ VPC Network Topography\n2. Elastic Load Balancer (ALB) Setup\n3. EC2 Auto Scaling Group Policies\n4. Amazon RDS PostgreSQL Multi-AZ Storage",
    "### ☁️ Cloud Architect AWS Blueprint\n- **Networking:** VPC across 2 Availability Zones with Public & Private Subnets\n- **Compute:** Application Load Balancer routing to Private Subnet Auto Scaling Group\n- **Database:** Amazon RDS PostgreSQL in Multi-AZ configuration with automated failover\n- **Security:** AWS WAF + KMS Encryption at rest and in transit",
    "### 🛠️ Execution Complete\nArchitecture blueprint successfully finalized."
])

def get_bedrock_llm(model_id: str = None, temperature: float = 0.2):
    """
    Initializes Amazon Bedrock LLM client with local mock support.
    """
    if os.getenv("USE_MOCK_LLM", "true").lower() == "true":
        return _SHARED_MOCK_LLM

    selected_model = model_id or os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    
    return ChatBedrock(
        model_id=selected_model,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        model_kwargs={
            "temperature": temperature,
        }
    )