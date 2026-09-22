from typing import Dict, Any, List

class DigitalTwinEngine:
    def __init__(self, project_id: str):
        self.project_id = project_id

    def check_architecture_drift(self, commit_infra: Dict[str, Any], live_aws_infra: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects drift between current code commit and active live AWS infrastructure.
        """
        outdated_artefacts: List[str] = []
        drift_detected = False

        # Database Configuration Drift
        if commit_infra.get("database_type") != live_aws_infra.get("database_type"):
            drift_detected = True
            outdated_artefacts.extend(["Architecture_Diagram.png", "SRS_Document.pdf", "Thesis_Chapter_4.docx"])

        # Compute Layer Drift (e.g., EC2 to ECS)
        if commit_infra.get("compute_type") != live_aws_infra.get("compute_type"):
            drift_detected = True
            outdated_artefacts.extend(["Deployment_Guide.md", "Viva_Presentation.pptx"])

        return {
            "project_id": self.project_id,
            "drift_detected": drift_detected,
            "invalidated_documents": list(set(outdated_artefacts)),
            "sync_recommended": drift_detected,
            "status_message": "⚠️ Architecture Drift Detected! Documentation is outdated." if drift_detected else "🟢 Digital Twin in 100% Sync"
        }