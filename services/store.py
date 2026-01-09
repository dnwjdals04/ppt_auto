import json
from pathlib import Path
from datetime import datetime


class PlanStore:
    def __init__(self, base_dir: str = "out/plans"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _fp(self, plan_id: str) -> Path:
        return self.base / f"{plan_id}.json"

    def create(self, plan: dict) -> str:
        plan_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        plan["plan_id"] = plan_id
        self.save(plan_id, plan)
        return plan_id

    def get(self, plan_id: str) -> dict | None:
        fp = self._fp(plan_id)
        if not fp.exists():
            return None
        return json.loads(fp.read_text(encoding="utf-8"))

    def save(self, plan_id: str, plan: dict) -> None:
        fp = self._fp(plan_id)
        fp.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
