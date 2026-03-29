import hashlib, json, httpx
from datetime import datetime, timedelta
from .config import get_cfg
from .database import get_db

def get_cache_ttl(url: str) -> int | None:
    if '/discover/' in url or '/category/' in url or '/search/' in url:
        return 604800
    return None

async def tmdb_req(url: str):
    cfg = get_cfg()
    if not cfg.tmdb_key:
        return {"results": []}

    h = hashlib.md5(url.encode()).hexdigest()
    with get_db() as conn:
        cur = conn.execute('SELECT response_json FROM tmdb_cache WHERE url_hash = ? AND (expires_at IS NULL OR expires_at > datetime("now"))', (h,))
        row = cur.fetchone()
        if row:
            data = json.loads(row[0])
            if 'results' in data:
                for i in data['results']:
                    if i.get('poster_path') and 'poster_url' not in i:
                        i['poster_url'] = f"/proxy-img?url={i['poster_path']}&id={i['id']}"
            return data

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url.replace("API_KEY", cfg.tmdb_key))
            data = resp.json()
        except Exception as e:
            print(f"❌ Ошибка TMDB: {e}")
            return {"results": []}

    if 'results' in data:
        for i in data['results']:
            if i.get('poster_path'):
                i['poster_url'] = f"/proxy-img?url={i['poster_path']}&id={i['id']}"

    ttl = get_cache_ttl(url)
    expires = None if ttl is None else (datetime.now() + timedelta(seconds=ttl)).isoformat()
    with get_db() as conn:
        conn.execute('INSERT OR REPLACE INTO tmdb_cache (url_hash, url, response_json, expires_at) VALUES (?, ?, ?, ?)',
                     (h, url, json.dumps(data), expires))
        conn.commit()
    return data