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
OUT_DIR = BASE_DIR / "out"  # ✅ 너 구조에 맞춰 out 사용


def _store(request: Request):
    return request.app.state.store


def _remove_file(path: str):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except Exception:
        # 운영에서 로그 남기고 싶으면 여기에 print/logging 넣어도 됨
        pass


@router.post("/api/ppt/{plan_id}/generate")
def generate_ppt(request: Request, plan_id: str):
    store = _store(request)
    plan = store.get(plan_id)
    if not plan:
        return JSONResponse({"error": "plan not found"}, status_code=404)

    # out/ 폴더 없으면 생성
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # PPT 생성 -> out_fp는 Path 로 온다고 가정
    out_fp = build_ppt(plan, TEMPLATE, BIBLE_DIR, OUT_DIR)

    # ✅ 다운로드 파일명: thepureum_YYYYMMDD.pptx
    date_str = datetime.now().strftime("%Y%m%d")
    download_name = f"thepureum_{date_str}.pptx"

    # (원하면) 같은 날 여러 번 생성 구분하려면:
    # download_name = f"thepureum_{date_str}_{plan_id}.pptx"

    return FileResponse(
        path=str(out_fp),
        filename=download_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        # ✅ 다운로드 응답이 끝나면 out 파일 자동 삭제
        background=BackgroundTask(_remove_file, str(out_fp)),
    )
