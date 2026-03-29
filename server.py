import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import httpx

from app.database import init_db, get_user_by_id, update_user_profile, change_user_password, verify_user_password, get_favorites, add_favorite, remove_favorite, check_favorite, create_verification_token, verify_email_token, create_reset_token, reset_password_with_token
from app.config import get_cfg, save_cfg
from app.auth import authenticate_admin, create_user, get_user_by_username, verify_password, create_access_token, get_current_user
from app.models import Settings, UserRegister, UserLogin, UserUpdate
from app.tmdb import tmdb_req
from app.torrents import router as torrents_router
from app.download import router as download_router
from app.static_files import router as static_router
from app.email_service import email_service
from app.admin import router as admin_router

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")

# TMDB Прокси
@app.get("/tmdb-proxy/{path:path}")
async def tmdb_proxy(path: str):
    cfg = get_cfg()
    full_url = f"https://api.themoviedb.org/3/{path}?api_key={cfg.tmdb_key}&language=ru-RU"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(full_url)
            return resp.json()
        except Exception as e:
            print(f"TMDB Proxy error: {e}")
            return {"results": [], "error": str(e)}

# Подключаем роутеры
app.include_router(static_router)
app.include_router(torrents_router)
app.include_router(download_router)
app.include_router(admin_router)

# Инициализация БД
init_db()

# ========== ПУБЛИЧНЫЕ ЭНДПОИНТЫ ==========
@app.post("/api/register")
async def register(user: UserRegister):
    user_id = create_user(user.email, user.username, user.password)
    if not user_id:
        raise HTTPException(400, "Username or email already exists")
    token = create_verification_token(user_id)
    await email_service.send_verification_email(user.email, user.username, token)
    return {"msg": "User registered. Check your email to verify account."}

@app.post("/api/login")
async def login(user: UserLogin):
    db_user = get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(401, "Incorrect username or password")
    if not db_user["approved"]:
        raise HTTPException(403, "Account not approved by admin")
    if not db_user.get("email_verified", True):
        raise HTTPException(403, "Email not verified")
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/verify")
async def verify_page(token: str):
    user_id = verify_email_token(token)
    if not user_id:
        return HTMLResponse("""
        <html><body style="text-align:center; padding:50px;">
            <h1>❌ Ссылка недействительна</h1>
            <a href="/">Вернуться</a>
        </body></html>
        """)
    return HTMLResponse("""
    <html><body style="text-align:center; padding:50px;">
        <h1>✅ Email подтвержден!</h1>
        <p>Теперь вы можете войти.</p>
        <script>setTimeout(()=>location.href='/',2000)</script>
    </body></html>
    """)

@app.post("/api/forgot-password")
async def forgot_password(email: str):
    result = create_reset_token(email)
    if result:
        token, username = result
        await email_service.send_reset_email(email, username, token)
    return {"msg": "If email exists and verified, instructions sent"}

@app.post("/api/reset-password")
async def reset_password(token: str, new_password: str):
    if len(new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    success = reset_password_with_token(token, new_password)
    if not success:
        raise HTTPException(400, "Invalid or expired token")
    return {"msg": "Password changed"}

@app.get("/reset-password")
async def reset_page(token: str):
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Сброс пароля</title>
    <style>
        body {{ font-family: Arial; text-align: center; padding: 50px; background: #0a0a0a; color: white; }}
        .container {{ max-width: 400px; margin: 0 auto; background: #141414; padding: 30px; border-radius: 10px; }}
        input {{ width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #333; background: #222; color: white; }}
        button {{ width: 100%; padding: 10px; background: #e50914; color: white; border: none; border-radius: 5px; cursor: pointer; }}
    </style>
    </head>
    <body>
    <div class="container">
        <h2>Сброс пароля</h2>
        <input type="password" id="pwd" placeholder="Новый пароль">
        <input type="password" id="pwd2" placeholder="Подтвердите пароль">
        <button onclick="reset()">Сменить пароль</button>
        <div id="msg" style="margin-top:10px;"></div>
    </div>
    <script>
        const token = '{token}';
        async function reset() {{
            const pwd = document.getElementById('pwd').value;
            const pwd2 = document.getElementById('pwd2').value;
            if (pwd.length < 8) {{
                document.getElementById('msg').innerText = 'Пароль должен быть не менее 8 символов';
                return;
            }}
            if (pwd !== pwd2) {{
                document.getElementById('msg').innerText = 'Пароли не совпадают';
                return;
            }}
            const res = await fetch('/api/reset-password', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{token, new_password: pwd}})
            }});
            const data = await res.json();
            if (res.ok) {{
                document.getElementById('msg').style.color = 'green';
                document.getElementById('msg').innerText = 'Пароль изменен! Перенаправление...';
                setTimeout(() => location.href='/', 2000);
            }} else {{
                document.getElementById('msg').innerText = data.detail || 'Ошибка';
            }}
        }}
    </script>
    </body>
    </html>
    """)

# ========== ОСТАЛЬНЫЕ ЭНДПОИНТЫ ==========
@app.get("/api/trailer/{mtype}/{mid}")
async def trailer(mtype: str, mid: int):
    ru = await tmdb_req(f"https://api.themoviedb.org/3/{mtype}/{mid}/videos?api_key=API_KEY&language=ru-RU")
    key = next((i['key'] for i in ru.get('results', []) if i['site'] == 'YouTube'), None)
    if not key:
        en = await tmdb_req(f"https://api.themoviedb.org/3/{mtype}/{mid}/videos?api_key=API_KEY")
        key = next((i['key'] for i in en.get('results', []) if i['site'] == 'YouTube'), None)
    return {"key": key}

@app.get("/api/discover/{mtype}/{gid}")
async def discover(mtype: str, gid: int, page: int = 1, year: str = None, first_air_date_year: str = None, with_origin_country: str = None):
    url = f"https://api.themoviedb.org/3/discover/{mtype}?api_key=API_KEY&language=ru-RU&with_genres={gid}&page={page}&sort_by=popularity.desc"
    if year: url += f"&year={year}"
    if first_air_date_year: url += f"&first_air_date_year={first_air_date_year}"
    if with_origin_country: url += f"&with_origin_country={with_origin_country}"
    return await tmdb_req(url)

@app.get("/api/{mtype}/category")
async def get_cat(mtype: str, cat: str = "popular", page: int = 1, year: str = None, first_air_date_year: str = None, with_origin_country: str = None):
    url = f"https://api.themoviedb.org/3/{mtype}/{cat}?api_key=API_KEY&language=ru-RU&page={page}"
    if year: url += f"&year={year}"
    if first_air_date_year: url += f"&first_air_date_year={first_air_date_year}"
    if with_origin_country: url += f"&with_origin_country={with_origin_country}"
    return await tmdb_req(url)

@app.get("/api/search/all")
async def search_all(query: str, page: int = 1):
    return await tmdb_req(f"https://api.themoviedb.org/3/search/multi?api_key=API_KEY&language=ru-RU&query={query}&page={page}")

@app.get("/api/trending/{mtype}/{time_window}")
async def trending(mtype: str, time_window: str, page: int = 1):
    return await tmdb_req(f"https://api.themoviedb.org/3/trending/{mtype}/{time_window}?api_key=API_KEY&language=ru-RU&page={page}")

@app.get("/api/details/{mtype}/{mid}")
async def get_details(mtype: str, mid: int):
    return await tmdb_req(f"https://api.themoviedb.org/3/{mtype}/{mid}?api_key=API_KEY&language=ru-RU")

# ========== ПРОФИЛЬ ==========
@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.put("/api/profile")
async def update_profile(data: dict, current_user: dict = Depends(get_current_user)):
    email = data.get("email")
    avatar_url = data.get("avatar_url")
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if current_password and new_password:
        if not verify_user_password(current_user["id"], current_password):
            raise HTTPException(400, "Current password is incorrect")
        if len(new_password) < 8:
            raise HTTPException(400, "Password must be at least 8 characters")
        change_user_password(current_user["id"], new_password)
    
    if email:
        update_user_profile(current_user["id"], email=email)
    if avatar_url:
        update_user_profile(current_user["id"], avatar_url=avatar_url)
    
    return {"msg": "Profile updated"}

# ========== ИЗБРАННОЕ ==========
@app.get("/api/favorites")
async def get_favorites_list(current_user: dict = Depends(get_current_user)):
    return get_favorites(current_user["id"])

@app.post("/api/favorites")
async def add_favorite_item(item: dict, current_user: dict = Depends(get_current_user)):
    tmdb_id = item.get("tmdb_id")
    media_type = item.get("media_type")
    title = item.get("title")
    poster_path = item.get("poster_path")
    vote_average = item.get("vote_average")
    year = item.get("year")
    
    if not tmdb_id or not media_type:
        raise HTTPException(400, "tmdb_id and media_type required")
    
    success = add_favorite(current_user["id"], tmdb_id, media_type, title, poster_path, vote_average, year)
    if not success:
        raise HTTPException(400, "Already in favorites")
    return {"msg": "Added to favorites"}

@app.delete("/api/favorites/{tmdb_id}")
async def remove_favorite_item(tmdb_id: int, type: str, current_user: dict = Depends(get_current_user)):
    success = remove_favorite(current_user["id"], tmdb_id, type)
    if not success:
        raise HTTPException(404, "Favorite not found")
    return {"msg": "Removed from favorites"}

@app.get("/api/favorites/check/{tmdb_id}")
async def check_favorite_item(tmdb_id: int, type: str, current_user: dict = Depends(get_current_user)):
    is_fav = check_favorite(current_user["id"], tmdb_id, type)
    return {"is_favorite": is_fav}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)