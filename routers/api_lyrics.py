from fastapi import APIRouter
from pydantic import BaseModel
from services.melon import fetch_lyrics_melon

router = APIRouter()


class LyricsReq(BaseModel):
    title: str
    artist: str | None = ""


@router.post("/api/lyrics/fetch")
def fetch_lyrics(req: LyricsReq):
    lyrics = fetch_lyrics_melon(req.title, req.artist or "")
    return {"lyrics": lyrics}
