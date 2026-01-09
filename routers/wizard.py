from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _store(request: Request):
    return request.app.state.store


@router.get("/")
def step1(request: Request):
    return templates.TemplateResponse("step1.html", {"request": request})



@router.get("/step/2")
def step2(request: Request, plan_id: str):
    store = _store(request)
    plan = store.get(plan_id)

    if not plan:
        return templates.TemplateResponse(
            "step2.html",
            {"request": request, "plan_id": plan_id, "error": "plan not found"},
        )

    praise_count = int(plan.get("praise_count", 3))
    return templates.TemplateResponse(
        "step2.html",
        {"request": request, "plan_id": plan_id, "praise_count": praise_count},
    )


@router.get("/step/3")
def step3(request: Request, plan_id: str):
    store = _store(request)
    plan = store.get(plan_id)

    if not plan:
        return templates.TemplateResponse(
            "step3.html",
            {"request": request, "plan_id": plan_id, "error": "plan not found"},
        )

    # 템플릿에서 plan.songs.praise / plan.songs.offering / plan.songs.closing 사용
    return templates.TemplateResponse(
        "step3.html",
        {"request": request, "plan_id": plan_id, "plan": plan},
    )


@router.get("/step/4")
def step4(request: Request, plan_id: str):
    store = _store(request)
    plan = store.get(plan_id)
    return templates.TemplateResponse(
        "step4.html",
        {"request": request, "plan_id": plan_id, "has_plan": plan is not None},
    )
