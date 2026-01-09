from fastapi import FastAPI
from routers.wizard import router as wizard_router
from routers.api_plan import router as plan_router
from routers.api_lyrics import router as lyrics_router
from routers.api_ppt import router as ppt_router

from services.store import PlanStore

import asyncio
from pathlib import Path

from services.cleanup import cleanup_dir_by_age, env_int


async def _cleanup_loop(app: FastAPI):
    """
    주기적으로 out/ 및 out/plans/ 파일을 TTL 기준으로 정리.
    여러 worker로 띄우면 각 worker가 청소할 수 있는데,
    삭제 실패는 무시하도록 safe unlink로 처리했음.
    """
    # 환경변수로 조절 가능
    interval_sec = env_int("CLEANUP_INTERVAL_SEC", 3600)   # 1시간마다
    ppt_ttl_sec = env_int("PPT_TTL_SEC", 3600)             # pptx 1시간 보관
    plan_ttl_sec = env_int("PLAN_TTL_SEC", 6 * 3600)       # plan json 6시간 보관(원하면 더 늘려)

    out_dir = Path("out")
    plans_dir = out_dir / "plans"

    while True:
        try:
            # out/*.pptx 삭제 (너 프로젝트는 out 아래에 pptx 생성)
            cleanup_dir_by_age(out_dir, patterns=["*.pptx"], max_age_seconds=ppt_ttl_sec)

            # out/plans/*.json 삭제
            cleanup_dir_by_age(plans_dir, patterns=["*.json"], max_age_seconds=plan_ttl_sec)
        except Exception:
            # 운영이면 logging 넣는 걸 추천하지만, 일단 조용히 넘어가게
            pass

        await asyncio.sleep(interval_sec)


def create_app() -> FastAPI:
    app = FastAPI()

    # ✅ plan not found 방지: 전역 store 인스턴스 1개를 app.state로 공유
    app.state.store = PlanStore(base_dir="out/plans")

    app.include_router(wizard_router)
    app.include_router(plan_router)
    app.include_router(lyrics_router)
    app.include_router(ppt_router)

    @app.on_event("startup")
    async def _startup():
        # 백그라운드 정리 루프 시작
        asyncio.create_task(_cleanup_loop(app))

    return app


app = create_app()
