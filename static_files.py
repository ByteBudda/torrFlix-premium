import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
import httpx
import aiofiles

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, 'cache_img')
os.makedirs(CACHE_DIR, exist_ok=True)

@router.get("/")
async def index():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

@router.get("/proxy-img")
async def proxy_img(url: str, id: str):
    path = os.path.join(CACHE_DIR, f"{id}.jpg")
    if os.path.exists(path):
        return FileResponse(path)
    
    async with httpx.AsyncClient() as client:
        try:
            full_url = f"https://image.tmdb.org/t/p/w500{url}"
            r = await client.get(full_url)
            if r.status_code == 200:
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(r.content)
                return FileResponse(path)
        except Exception as e:
            print(f"Proxy error: {e}")
    
    return Response(status_code=404)