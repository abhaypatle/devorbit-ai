from typing import Dict, Any

class EnterpriseIDPEngine:
    def calculate_finops_cost(self, ec2_count: int = 2, rds_multi_az: bool = True) -> Dict[str, Any]:
        base_ec2 = ec2_count * 40
        base_rds = 120 if rds_multi_az else 45
        base_alb = 35
        total_monthly = base_ec2 + base_rds + base_alb

        return {
            "estimated_monthly_usd": total_monthly,
            "currency": "USD",
            "cost_breakdown": {
                "ec2_compute": f"${base_ec2}",
                "rds_database": f"${base_rds}",
                "alb_load_balancer": f"${base_alb}"
            },
            "savings_recommendation": "Switch Staging environment to Single-AZ RDS to save $75/month."
        }

    def run_cis_security_audit(self, terraform_code: str) -> Dict[str, Any]:
        violations = []
        if "0.0.0.0/0" in terraform_code:
            violations.append("CRITICAL: Open CIDR Block 0.0.0.0/0 in Security Group rules.")
        if "encrypted = false" in terraform_code.lower():
            violations.append("HIGH: Storage encryption disabled on RDS/EBS volume.")

        return {
            "passed": len(violations) == 0,
            "severity": "HIGH" if violations else "PASS",
            "violations": violations
        }