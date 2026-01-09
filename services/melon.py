import time
from typing import List, Dict, Tuple
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager




def _new_driver(headless: bool = True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")

    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chromedriver_bin = os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")
    options.binary_location = chrome_bin

    return webdriver.Chrome(
        service=ChromeService(executable_path=chromedriver_bin),
        options=options,
    )


def _search_song_open_lyrics(driver, query: str) -> bool:
    # 멜론 홈에서 검색
    search = driver.find_element(By.ID, "top_search")
    search.clear()
    search.send_keys(query)
    driver.find_element(By.CSS_SELECTOR, "button.btn_icon.search_m").click()
    time.sleep(1)

    try:
        # 첫 결과 상세
        driver.find_element(By.CSS_SELECTOR, ".btn.btn_icon_detail").click()
        time.sleep(1)
        # 가사 더보기
        driver.find_element(By.CSS_SELECTOR, ".button_more.arrow_d").click()
        time.sleep(1)
        return True
    except Exception:
        return False


def _extract_lyrics(driver) -> str:
    try:
        lyrics_element = driver.find_element(By.CSS_SELECTOR, "#d_video_summary")
        lyrics = lyrics_element.text.strip()
        return lyrics if lyrics else "(가사 비어있음)"
    except Exception:
        return "(가사 파싱 실패)"


def fetch_lyrics_melon(song_title: str, artist_name: str = "", headless: bool = True) -> str:
    """
    단일 곡 가사 크롤링(호환용)
    """
    driver = _new_driver(headless=headless)
    driver.get("https://www.melon.com/")
    time.sleep(1)

    try:
        q1 = f"{song_title} {artist_name}".strip()
        ok = _search_song_open_lyrics(driver, q1)

        if not ok:
            ok = _search_song_open_lyrics(driver, song_title.strip())

        if not ok:
            return "(가사를 찾지 못했습니다)"

        return _extract_lyrics(driver)
    except Exception as e:
        return f"(크롤링 실패: {e})"
    finally:
        driver.quit()


def fetch_lyrics_batch_melon(songs: List[Dict], headless: bool = True) -> List[Tuple[Dict, str]]:
    """
    ✅ Step2 제출 시 여러 곡을 한 번에 처리하려고 만든 배치 버전.
    - songs: [{"title": "...", "artist": "..."}, ...]
    - return: [(song_dict, lyrics_str), ...]
    """
    driver = _new_driver(headless=headless)
    driver.get("https://www.melon.com/")
    time.sleep(1)

    out: List[Tuple[Dict, str]] = []
    try:
        for s in songs:
            title = (s.get("title") or "").strip()
            artist = (s.get("artist") or "").strip()

            if not title:
                out.append((s, ""))  # 빈 입력
                continue

            try:
                q1 = f"{title} {artist}".strip()
                ok = _search_song_open_lyrics(driver, q1)

                if not ok:
                    ok = _search_song_open_lyrics(driver, title)

                if not ok:
                    out.append((s, "(가사를 찾지 못했습니다)"))
                    # 다시 멜론 홈으로 복귀(상태 꼬임 방지)
                    driver.get("https://www.melon.com/")
                    time.sleep(1)
                    continue

                lyrics = _extract_lyrics(driver)
                out.append((s, lyrics))

                # 다음 곡을 위해 홈으로 복귀
                driver.get("https://www.melon.com/")
                time.sleep(1)

            except Exception as e:
                out.append((s, f"(크롤링 실패: {e})"))
                driver.get("https://www.melon.com/")
                time.sleep(1)

        return out
    finally:
        driver.quit()
