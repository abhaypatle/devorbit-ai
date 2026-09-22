from typing import List, Dict

class StartupMVPEngine:
    def auto_assign_tasks(self, team_members: List[Dict], backlog: List[str]) -> List[Dict]:
        assignments = []
        for idx, task in enumerate(backlog):
            assigned = team_members[idx % len(team_members)]["name"]
            assignments.append({
                "task_id": f"TSK-00{idx + 1}",
                "task_name": task,
                "assigned_to": assigned,
                "status": "In Progress"
            })
        return assignments