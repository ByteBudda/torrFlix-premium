 
from urllib.parse import unquote, quote
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from .config import get_cfg
from .auth import get_current_user_from_query

router = APIRouter()

@router.get("/api/download")
async def download_torrent(url: str, token: str = None, current_user: dict = Depends(get_current_user_from_query)):
    if not url:
        raise HTTPException(400, "URL required")
    
    target_url = unquote(url)
    is_prowlarr = ":9696" in target_url
    
    if is_prowlarr:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
        async def prowlarr_stream():
            async with httpx.AsyncClient(follow_redirects=True, timeout=40.0, verify=False, headers=headers) as client:
                try:
                    async with client.stream("GET", target_url) as response:
                        if response.status_code >= 400:
                            yield f"Error: {response.status_code}".encode()
                            return
                        async for chunk in response.aiter_bytes():
                            yield chunk
                except Exception as e:
                    print(f"Prowlarr stream error: {e}")
                    yield b"Error during download"
        return StreamingResponse(prowlarr_stream(), media_type="application/x-bittorrent",
                                 headers={"Content-Disposition": 'attachment; filename="file.torrent"'})
    else:
        c = get_cfg()
        referer = c.jack_url if c.jack_url else "http://127.0.0.1:9117"
        filename = "torrent.torrent"
        if "file=" in target_url:
            try:
                filename = unquote(target_url.split("file=")[-1].split("&")[0])
                if not filename.lower().endswith(".torrent"):
                    filename += ".torrent"
            except: pass
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                   "Referer": referer, "Accept": "application/x-bittorrent, */*"}
        async def jackett_stream():
            async with httpx.AsyncClient(follow_redirects=True, timeout=40.0, verify=False, headers=headers) as client:
                try:
                    async with client.stream("GET", target_url) as response:
                        if response.status_code >= 400:
                            yield f"Error: {response.status_code}".encode()
                            return
                        async for chunk in response.aiter_bytes():
                            yield chunk
                except Exception as e:
                    print(f"Jackett stream error: {e}")
                    yield b"Error during download"
        return StreamingResponse(jackett_stream(), media_type="application/x-bittorrent",
                                 headers={"Content-Disposition": f'attachment; filename="{quote(filename)}"'})