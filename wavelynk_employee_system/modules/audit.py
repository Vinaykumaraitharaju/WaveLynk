from database import execute
from utils import now_str


def log_audit(action: str, actor_name: str, target_name: str = "", details: str = ""):
    execute(
        """
        INSERT INTO audit_logs (action, actor_name, target_name, details, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            action.strip(),
            actor_name.strip() if actor_name else "",
            target_name.strip() if target_name else "",
            details.strip() if details else "",
            now_str(),
        ),
    )