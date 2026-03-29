from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from .auth import authenticate_admin
from .config import get_cfg, save_cfg
from .models import Settings, UserUpdate
from .database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("", response_class=HTMLResponse)
async def admin_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>torrFLIX Admin</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { background: #0a0a0a; color: #fff; font-family: sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: #141414; border-radius: 12px; padding: 20px; margin-bottom: 30px; border: 1px solid #333; }
            h2 { color: #e50914; margin-top: 0; }
            input, button { padding: 10px; margin: 5px 0; border-radius: 6px; border: 1px solid #444; background: #222; color: white; }
            button { cursor: pointer; background: #e50914; border: none; font-weight: bold; }
            button.secondary { background: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { text-align: left; padding: 10px; border-bottom: 1px solid #333; }
            th { background: #1f1f1f; }
            .status-approved { color: #4caf50; }
            .status-pending { color: #ff9800; }
            .action-btn { padding: 5px 10px; margin: 0 3px; font-size: 12px; cursor: pointer; border: none; border-radius: 4px; }
            .delete-btn { background: #d32f2f; color: white; }
            .approve-btn { background: #388e3c; color: white; }
            .block-btn { background: #f57c00; color: white; }
            .message { margin-top: 10px; padding: 10px; border-radius: 6px; background: #2e7d32; display: none; }
            .error { background: #c62828; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h2>Настройки API</h2>
                <input type="text" id="tmdb_key" placeholder="TMDB API Key">
                <input type="text" id="jack_url" placeholder="Jackett URL">
                <input type="text" id="jack_key" placeholder="Jackett API Key">
                <input type="text" id="prowlarr_url" placeholder="Prowlarr URL">
                <input type="text" id="prowlarr_key" placeholder="Prowlarr API Key">
                <hr>
                <h3>Настройки почты</h3>
                <input type="text" id="smtp_server" placeholder="SMTP сервер">
                <input type="text" id="smtp_port" placeholder="Порт">
                <input type="text" id="smtp_user" placeholder="Email отправителя">
                <input type="password" id="smtp_password" placeholder="Пароль">
                <input type="text" id="site_url" placeholder="URL сайта">
                <button onclick="saveConfig()">Сохранить</button>
                <div id="configMsg" class="message"></div>
            </div>
            <div class="card">
                <h2>Управление пользователями</h2>
                <button onclick="loadUsers()" class="secondary">Обновить список</button>
                <div id="usersTable"></div>
                <div id="userMsg" class="message"></div>
            </div>
        </div>
        <script>
            async function loadUsers() {
                try {
                    const r = await fetch('/admin/api/users');
                    if (!r.ok) throw new Error('Ошибка');
                    const users = await r.json();
                    renderUsers(users);
                } catch(e) {
                    showMsg('userMsg', 'Ошибка: ' + e.message, true);
                }
            }
            function renderUsers(users) {
                if (!users.length) {
                    document.getElementById('usersTable').innerHTML = '<p>Нет пользователей</p>';
                    return;
                }
                let html = '<table><thead><tr><th>ID</th><th>Email</th><th>Логин</th><th>Статус</th><th>Email</th><th>Дата</th><th>Действия</th></tr></thead><tbody>';
                for (let u of users) {
                    html += '<tr>';
                    html += '<td>' + u.id + '</td>';
                    html += '<td>' + escapeHtml(u.email) + '</td>';
                    html += '<td>' + escapeHtml(u.username) + '</td>';
                    html += '<td class="' + (u.approved ? 'status-approved' : 'status-pending') + '">' + (u.approved ? 'Одобрен' : 'Ожидает') + '</td>';
                    html += '<td class="' + (u.email_verified ? 'status-approved' : 'status-pending') + '">' + (u.email_verified ? 'Да' : 'Нет') + '</td>';
                    html += '<td>' + new Date(u.created_at).toLocaleString() + '</td>';
                    html += '<td>';
                    if (!u.approved) html += '<button class="action-btn approve-btn" onclick="approveUser(' + u.id + ', true)">Одобрить</button> ';
                    else html += '<button class="action-btn block-btn" onclick="approveUser(' + u.id + ', false)">Блок</button> ';
                    html += '<button class="action-btn delete-btn" onclick="deleteUser(' + u.id + ')">Удалить</button>';
                    html += '</td></tr>';
                }
                html += '</tbody></table>';
                document.getElementById('usersTable').innerHTML = html;
            }
            async function approveUser(userId, approved) {
                try {
                    const r = await fetch('/admin/api/users/' + userId, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ approved: approved })
                    });
                    if (!r.ok) throw new Error('Ошибка');
                    showMsg('userMsg', 'Пользователь ' + (approved ? 'одобрен' : 'заблокирован'));
                    loadUsers();
                } catch(e) {
                    showMsg('userMsg', 'Ошибка: ' + e.message, true);
                }
            }
            async function deleteUser(userId) {
                if (!confirm('Удалить?')) return;
                try {
                    const r = await fetch('/admin/api/users/' + userId, { method: 'DELETE' });
                    if (!r.ok) throw new Error('Ошибка');
                    showMsg('userMsg', 'Пользователь удалён');
                    loadUsers();
                } catch(e) {
                    showMsg('userMsg', 'Ошибка: ' + e.message, true);
                }
            }
            async function saveConfig() {
                const data = {
                    tmdb_key: document.getElementById('tmdb_key').value,
                    jack_url: document.getElementById('jack_url').value,
                    jack_key: document.getElementById('jack_key').value,
                    prowlarr_url: document.getElementById('prowlarr_url').value,
                    prowlarr_key: document.getElementById('prowlarr_key').value,
                    smtp_server: document.getElementById('smtp_server').value,
                    smtp_port: parseInt(document.getElementById('smtp_port').value) || 587,
                    smtp_user: document.getElementById('smtp_user').value,
                    smtp_password: document.getElementById('smtp_password').value,
                    site_url: document.getElementById('site_url').value
                };
                try {
                    const r = await fetch('/admin/api/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    if (!r.ok) throw new Error('Ошибка');
                    showMsg('configMsg', 'Сохранено');
                } catch(e) {
                    showMsg('configMsg', 'Ошибка: ' + e.message, true);
                }
            }
            function showMsg(elementId, text, isError = false) {
                const el = document.getElementById(elementId);
                el.textContent = text;
                el.style.display = 'block';
                el.className = 'message' + (isError ? ' error' : '');
                setTimeout(() => el.style.display = 'none', 3000);
            }
            function escapeHtml(str) {
                if (!str) return '';
                return str.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
            }
            async function loadConfig() {
                try {
                    const r = await fetch('/admin/api/config');
                    if (r.ok) {
                        const d = await r.json();
                        document.getElementById('tmdb_key').value = d.tmdb_key || '';
                        document.getElementById('jack_url').value = d.jack_url || '';
                        document.getElementById('jack_key').value = d.jack_key || '';
                        document.getElementById('prowlarr_url').value = d.prowlarr_url || '';
                        document.getElementById('prowlarr_key').value = d.prowlarr_key || '';
                        document.getElementById('smtp_server').value = d.smtp_server || '';
                        document.getElementById('smtp_port').value = d.smtp_port || 587;
                        document.getElementById('smtp_user').value = d.smtp_user || '';
                        document.getElementById('smtp_password').value = d.smtp_password || '';
                        document.getElementById('site_url').value = d.site_url || '';
                    }
                } catch(e) {}
            }
            loadConfig();
            loadUsers();
        </script>
    </body>
    </html>
    """

@router.get("/api/config")
async def get_config(admin: str = Depends(authenticate_admin)):
    return get_cfg()

@router.post("/api/config")
async def save_config(s: Settings, admin: str = Depends(authenticate_admin)):
    save_cfg(s)
    return {"status": "ok"}

@router.get("/api/users")
async def list_users(admin: str = Depends(authenticate_admin)):
    with get_db() as conn:
        try:
            rows = conn.execute('SELECT id, email, username, approved, email_verified, created_at FROM users').fetchall()
            return [{"id": r[0], "email": r[1], "username": r[2], "approved": bool(r[3]), "email_verified": bool(r[4]) if len(r) > 4 else True, "created_at": r[5]} for r in rows]
        except:
            rows = conn.execute('SELECT id, email, username, approved, created_at FROM users').fetchall()
            return [{"id": r[0], "email": r[1], "username": r[2], "approved": bool(r[3]), "email_verified": True, "created_at": r[4]} for r in rows]

@router.put("/api/users/{uid}")
async def update_user(uid: int, update: UserUpdate, admin: str = Depends(authenticate_admin)):
    with get_db() as conn:
        conn.execute('UPDATE users SET approved = ? WHERE id = ?', (1 if update.approved else 0, uid))
        conn.commit()
        if conn.total_changes == 0:
            raise HTTPException(404, "User not found")
    return {"msg": "Updated"}

@router.delete("/api/users/{uid}")
async def delete_user(uid: int, admin: str = Depends(authenticate_admin)):
    with get_db() as conn:
        conn.execute('DELETE FROM users WHERE id = ?', (uid,))
        conn.commit()
        if conn.total_changes == 0:
            raise HTTPException(404, "User not found")
    return {"msg": "Deleted"}