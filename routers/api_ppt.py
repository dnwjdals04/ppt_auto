from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from datetime import datetime
from starlette.background import BackgroundTask
import os

from services.ppt_builder import build_ppt

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = BASE_DIR / "thepureum.pptx"
BIBLE_DIR = BASE_DIR / "bible"
OUT_DIR = BASE_DIR / "out"


def _store(request: Request):
    return request.app.state.store


def _remove_file(path: str):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@router.post("/api/ppt/{plan_id}/generate")
def generate_ppt(request: Request, plan_id: str):
    store = _store(request)
    plan = store.get(plan_id)
    if not plan:
        return JSONResponse({"error": "plan not found"}, status_code=404)

    out_fp = build_ppt(plan, TEMPLATE, BIBLE_DIR, OUT_DIR)

    date_str = datetime.now().strftime("%Y%m%d")
    download_name = f"thepureum_{date_str}.pptx"

    return FileResponse(
        path=str(out_fp),
        filename=download_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        background=BackgroundTask(_remove_file, str(out_fp)),  # ✅ 전송 끝나면 삭제
    )
