// auth.js

let authMode = 'login';

function getToken() { 
    return localStorage.getItem('token'); 
}

function setToken(token) { 
    localStorage.setItem('token', token); 
}

function clearToken() { 
    localStorage.removeItem('token'); 
}

function updateAuthUI() {
    const token = getToken();
    const authBtn = document.getElementById('authButton');
    const profileBtn = document.getElementById('profileButton');
    const logoutBtn = document.getElementById('logoutButton');
    
    if (token) {
        if (authBtn) authBtn.style.display = 'none';
        if (profileBtn) profileBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'block';
        loadProfile();
    } else {
        if (authBtn) authBtn.style.display = 'block';
        if (profileBtn) profileBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

function openAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
        setAuthMode('login');
        modal.style.zIndex = '10001';
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.style.display = 'none';
}

function setAuthMode(mode) {
    authMode = mode;
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const forgotForm = document.getElementById('forgotForm');
    const toggleBtn = document.getElementById('authToggleBtn');
    const title = document.getElementById('authTitle');
    
    if (loginForm) loginForm.style.display = 'none';
    if (registerForm) registerForm.style.display = 'none';
    if (forgotForm) forgotForm.style.display = 'none';
    
    if (mode === 'login') {
        if (loginForm) loginForm.style.display = 'block';
        if (title) title.innerText = 'Вход';
        if (toggleBtn) {
            toggleBtn.style.display = 'block';
            toggleBtn.innerText = 'Нет аккаунта? Зарегистрироваться';
        }
    } else if (mode === 'register') {
        if (registerForm) registerForm.style.display = 'block';
        if (title) title.innerText = 'Регистрация';
        if (toggleBtn) {
            toggleBtn.style.display = 'block';
            toggleBtn.innerText = 'Уже есть аккаунт? Войти';
        }
    } else if (mode === 'forgot') {
        if (forgotForm) forgotForm.style.display = 'block';
        if (title) title.innerText = 'Сброс пароля';
        if (toggleBtn) toggleBtn.style.display = 'none';
    }
    
    const msgDiv = document.getElementById('authMessage');
    if (msgDiv) msgDiv.innerText = '';
}

function showForgotPassword() {
    setAuthMode('forgot');
}

function showLogin() {
    setAuthMode('login');
}

function showAuthMessage(msg, isError = false) {
    const msgDiv = document.getElementById('authMessage');
    if (msgDiv) {
        msgDiv.innerText = msg;
        msgDiv.style.color = isError ? '#e50914' : '#4caf50';
        setTimeout(() => { msgDiv.innerText = ''; }, 5000);
    }
}

async function login(username, password) {
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (res.ok) {
            const data = await res.json();
            setToken(data.access_token);
            localStorage.setItem('username', username);
            updateAuthUI();
            closeAuthModal();
            if (window.currentMovie) {
                openMovieModal(window.currentMovie.id, window.currentMovie.type);
            }
            showNotification('Добро пожаловать, ' + username + '!', 'success');
            return true;
        } else {
            const err = await res.json();
            if (err.detail === 'Email not verified') {
                showAuthMessage('Email не подтвержден. Проверьте почту.', true);
            } else {
                showAuthMessage(err.detail || 'Ошибка входа', true);
            }
            return false;
        }
    } catch(e) {
        showAuthMessage('Ошибка соединения', true);
        return false;
    }
}

async function register(username, email, password, passwordConfirm) {
    if (password !== passwordConfirm) {
        showAuthMessage('Пароли не совпадают', true);
        return false;
    }
    
    if (password.length < 8) {
        showAuthMessage('Пароль должен быть минимум 8 символов', true);
        return false;
    }
    
    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        if (res.ok) {
            showAuthMessage('✅ Регистрация успешна! Проверьте email для подтверждения.', false);
            setTimeout(() => setAuthMode('login'), 3000);
            return true;
        } else {
            const err = await res.json();
            showAuthMessage(err.detail || 'Ошибка регистрации', true);
            return false;
        }
    } catch(e) {
        showAuthMessage('Ошибка соединения', true);
        return false;
    }
}

async function forgotPassword(email) {
    try {
        const res = await fetch('/api/forgot-password?email=' + encodeURIComponent(email), {
            method: 'POST'
        });
        if (res.ok) {
            showAuthMessage('📧 Инструкции отправлены на email (если он существует)', false);
            setTimeout(() => setAuthMode('login'), 3000);
            return true;
        } else {
            showAuthMessage('Ошибка отправки', true);
            return false;
        }
    } catch(e) {
        showAuthMessage('Ошибка соединения', true);
        return false;
    }
}

function logout() {
    clearToken();
    localStorage.removeItem('username');
    updateAuthUI();
    showNotification('Вы вышли из системы', 'info');
    if (document.getElementById('modal') && document.getElementById('modal').style.display === 'flex') {
        const mTorr = document.getElementById('mTorr');
        if (mTorr) {
            mTorr.innerHTML = '<div style="text-align:center; padding:40px;">Для просмотра контента <button onclick="openAuthModal()" style="background:none; border:none; color:var(--accent); cursor:pointer;">войдите</button></div>';
        }
    }
    if (typeof loadCatalog === 'function') loadCatalog(true);
}

async function handleAuthSubmit() {
    if (authMode === 'login') {
        const username = document.getElementById('authUsername')?.value;
        const password = document.getElementById('authPassword')?.value;
        if (!username || !password) {
            showAuthMessage('Заполните все поля', true);
            return;
        }
        await login(username, password);
    } else if (authMode === 'register') {
        const username = document.getElementById('regUsername')?.value;
        const email = document.getElementById('regEmail')?.value;
        const password = document.getElementById('regPassword')?.value;
        const confirm = document.getElementById('regPasswordConfirm')?.value;
        
        if (!username || !email || !password || !confirm) {
            showAuthMessage('Заполните все поля', true);
            return;
        }
        await register(username, email, password, confirm);
    } else if (authMode === 'forgot') {
        const email = document.getElementById('forgotEmail')?.value;
        if (!email) {
            showAuthMessage('Введите email', true);
            return;
        }
        await forgotPassword(email);
    }
}

// Инициализация обработчиков
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    
    const submitBtn = document.getElementById('authSubmitBtn');
    if (submitBtn) submitBtn.onclick = handleAuthSubmit;
    
    const regBtn = document.getElementById('regSubmitBtn');
    if (regBtn) regBtn.onclick = handleAuthSubmit;
    
    const forgotBtn = document.getElementById('forgotSubmitBtn');
    if (forgotBtn) forgotBtn.onclick = handleAuthSubmit;
    
    const toggleBtn = document.getElementById('authToggleBtn');
    if (toggleBtn) toggleBtn.onclick = () => {
        if (authMode === 'login') setAuthMode('register');
        else setAuthMode('login');
    };
    
    const closeBtn = document.querySelector('#authModal .close');
    if (closeBtn) closeBtn.onclick = closeAuthModal;
});