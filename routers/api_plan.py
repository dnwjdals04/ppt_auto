# routers/api_plan.py

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse

from services.melon import fetch_lyrics_batch_melon

router = APIRouter()


def _store(request: Request):
    return request.app.state.store


@router.post("/api/plan/init")
async def plan_init(
    request: Request,
    praise_count: int = Form(...),
    prayer: str = Form("기도 | "),
    sermon_title: str = Form(""),
    sermon_phrases_raw: str = Form(""),
    include_offering: int = Form(1),
    include_closing: int = Form(1),
):
    if not (1 <= praise_count <= 20):
        raise HTTPException(status_code=400, detail="praise_count must be 1..20")

    sermon_phrases = [x.strip() for x in sermon_phrases_raw.splitlines() if x.strip()]

    plan = {
        "praise_count": int(praise_count),
        "prayer": prayer.strip(),
        "sermon_title": sermon_title.strip(),
        "sermon_phrases": sermon_phrases,
        "songs": {
            "praise": [],
            "offering": None,
            "closing": None,
        },
        "flags": {
            "include_offering": bool(int(include_offering)),
            "include_closing": bool(int(include_closing)),
        },
    }

    store = _store(request)
    plan_id = store.create(plan)
    return RedirectResponse(url=f"/step/2?plan_id={plan_id}", status_code=303)


@router.post("/api/plan/{plan_id}/songs/basic")
async def save_songs_basic(request: Request, plan_id: str):
    """
    Step2 제출:
    - 제목/가수 저장
    - 그 즉시 멜론에서 가사 크롤링
    - plan에 lyrics 채워서 저장
    - Step3로 이동(수정만)
    """
    store = _store(request)
    plan = store.get(plan_id)
    if not plan:
        return RedirectResponse(url=f"/step/2?plan_id={plan_id}", status_code=303)

    praise_count = int(plan.get("praise_count", 3))
    form = await request.form()

    # 1) praise 구성
    praise = []
    for i in range(praise_count):
        title = str(form.get(f"praise_title_{i}", "")).strip()
        artist = str(form.get(f"praise_artist_{i}", "")).strip()
        praise.append({"title": title, "artist": artist, "lyrics": ""})

    # ✅ 2) offering/closing은 flags 안 믿고 "입력값 있으면" 무조건 저장
    offering = None
    ot = str(form.get("offering_title", "")).strip()
    oa = str(form.get("offering_artist", "")).strip()
    if ot:
        offering = {"title": ot, "artist": oa, "lyrics": ""}

    closing = None
    ct = str(form.get("closing_title", "")).strip()
    ca = str(form.get("closing_artist", "")).strip()
    if ct:
        closing = {"title": ct, "artist": ca, "lyrics": ""}

    plan["songs"]["praise"] = praise
    plan["songs"]["offering"] = offering
    plan["songs"]["closing"] = closing

    # 3) 여기서 즉시 크롤링(배치)
    batch = list(plan["songs"]["praise"])
    if offering:
        batch.append(offering)
    if closing:
        batch.append(closing)

    results = fetch_lyrics_batch_melon(batch, headless=True)

    # 4) 결과 반영 (song_dict를 그대로 넘겼으므로 in-place로 채움)
    for song_obj, lyrics in results:
        song_obj["lyrics"] = (lyrics or "").replace("\r\n", "\n")

    store.save(plan_id, plan)
    return RedirectResponse(url=f"/step/3?plan_id={plan_id}", status_code=303)


@router.post("/api/plan/{plan_id}/songs/lyrics")
async def save_lyrics(request: Request, plan_id: str):
    """
    Step3 제출: textarea 수정 내용 저장만
    """
    store = _store(request)
    plan = store.get(plan_id)
    if not plan:
        return RedirectResponse(url=f"/step/3?plan_id={plan_id}", status_code=303)

    form = await request.form()

    # praise
    for idx, s in enumerate(plan["songs"]["praise"]):
        s["lyrics"] = str(form.get(f"lyrics_praise_{idx}", "")).replace("\r\n", "\n")

    # offering
    if plan["songs"].get("offering"):
        plan["songs"]["offering"]["lyrics"] = str(form.get("lyrics_offering", "")).replace("\r\n", "\n")

    # closing
    if plan["songs"].get("closing"):
        plan["songs"]["closing"]["lyrics"] = str(form.get("lyrics_closing", "")).replace("\r\n", "\n")

    store.save(plan_id, plan)
    return RedirectResponse(url=f"/step/4?plan_id={plan_id}", status_code=303)
