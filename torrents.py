import asyncio, httpx, re
from urllib.parse import quote
from fastapi import APIRouter, Depends
from .config import get_cfg
from .auth import get_current_user

router = APIRouter()

def fix_jack_link(link: str, config_url: str) -> str:
    from urllib.parse import urlparse
    if not link: return link
    p = urlparse(link)
    if p.hostname in ["127.0.0.1", "localhost"]:
        cfg = urlparse(config_url)
        return p._replace(scheme=cfg.scheme, netloc=cfg.netloc).geturl()
    return link

TRASH_REGEXP = re.compile(
    r'\b(repack|pc-games|iso|crack|patch|update|dlc|nintendo|ps4|ps5|xbox|steam|reloaded|fitgirl|multiplayer|nospec|epub|fb2|pdf|mobi|mp3|flac|wav|album|soundtrack|ost|music|ebook)\b', 
    re.IGNORECASE
)

def is_strictly_video(title: str) -> bool:
    t = title.lower()
    if TRASH_REGEXP.search(t):
        return False
    video_markers = ['720p', '1080p', '2160p', '4k', 'itunes', 'hdtv', 'web-dl', 'bluray', 'bdrip', 'avc', 'hevc', 'x264', 'x265']
    if any(m in t for m in video_markers):
        return True
    return True

@router.get("/api/search/torrents")
async def search_torrents(title: str, orig_title: str = "", year: str = "", content_type: str = "movie", current_user: dict = Depends(get_current_user)):
    c = get_cfg()
    
    # Только один запрос - русское или английское название
    search_query = title if title else orig_title
    
    print(f"🔍 Поиск: {search_query}")
    
    # Категории
    cats = [2000, 2010, 2030, 2040, 2045, 5000, 5010, 5030, 5040, 5045]
    cat_params = "".join([f"&Category[]={cat}" for cat in cats])

    async def fetch_jackett():
        if not c.jack_key or not c.jack_url:
            return []
        url = f"{c.jack_url.rstrip('/')}/api/v2.0/indexers/all/results?apikey={c.jack_key}&Query={quote(search_query)}{cat_params}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                r = await client.get(url)
                return r.json().get("Results", [])
            except Exception as e:
                print(f"Jackett error: {e}")
                return []

    async def fetch_prowlarr():
        if not c.prowlarr_key or not c.prowlarr_url:
            return []
        url = f"{c.prowlarr_url.rstrip('/')}/api/v1/search?apikey={c.prowlarr_key}&query={quote(search_query)}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                r = await client.get(url)
                if r.status_code != 200:
                    return []
                data = r.json()
                results = data if isinstance(data, list) else data.get("results", [])
                normalized = []
                for t in results:
                    link = t.get("downloadUrl") or t.get("Link")
                    magnet = t.get("magnetUrl") or t.get("MagnetUri")
                    normalized.append({
                        "Title": t.get("title") or t.get("Title"),
                        "Size": t.get("size") or t.get("Size", 0),
                        "Seeders": t.get("seeders") or t.get("Seeders", 0),
                        "Link": link,
                        "MagnetUri": magnet,
                        "Tracker": t.get("indexer", "Prowlarr"),
                        "Details": t.get("infoUrl") or t.get("Details")
                    })
                return normalized
            except Exception as e:
                print(f"Prowlarr error: {e}")
                return []

    # Параллельный запуск Jackett и Prowlarr
    jackett_task = asyncio.create_task(fetch_jackett())
    prowlarr_task = asyncio.create_task(fetch_prowlarr())
    
    jackett_results, prowlarr_results = await asyncio.gather(jackett_task, prowlarr_task)
    
    # Объединяем результаты
    combined = []
    seen_links = set()

    for t in jackett_results + prowlarr_results:
        t_title = t.get("Title", "")
        link = t.get('MagnetUri') or t.get('Link')
        
        if not link or link in seen_links:
            continue
        
        if not is_strictly_video(t_title):
            continue

        seen_links.add(link)
        combined.append({
            "Title": t_title,
            "Size": t.get("Size", 0),
            "Seeders": t.get("Seeders", 0),
            "Link": fix_jack_link(link, c.jack_url),
            "Magnet": link if link.startswith("magnet:") else None,
            "Tracker": t.get("Tracker", "Unknown"),
            "Desc": t.get("Details", "")
        })

    combined.sort(key=lambda x: x.get('Seeders', 0), reverse=True)
    
    print(f"✅ Найдено: {len(combined)}")
    return combined[:60]