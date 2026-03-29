// favorites.js

async function toggleFavorite() {
    const movie = window.currentMovie;
    if (!movie) return;
    if (!getToken()) { openAuthModal(); return; }
    
    const type = movie.title ? 'movie' : 'tv';
    const isFav = await checkIsFavorite(movie.id, type);
    
    if (isFav) {
        const r = await authFetch(`/api/favorites/${movie.id}?type=${type}`, { method: 'DELETE' });
        if (r.ok) {
            updateFavButton(false);
            showNotification('Удалено из избранного', 'info');
        }
    } else {
        const item = { 
            tmdb_id: movie.id, 
            media_type: type, 
            title: movie.title || movie.name, 
            poster_path: movie.poster_path, 
            vote_average: movie.vote_average, 
            year: (movie.release_date || movie.first_air_date || '').split('-')[0] 
        };
        const r = await authFetch('/api/favorites', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(item) 
        });
        if (r.ok) {
            updateFavButton(true);
            showNotification('Добавлено в избранное', 'success');
        }
    }
}

async function checkIsFavorite(tmdbId, type) {
    if (!getToken()) return false;
    try {
        const r = await authFetch(`/api/favorites/check/${tmdbId}?type=${type}`);
        const data = await r.json();
        return data.is_favorite;
    } catch(e) { return false; }
}

function updateFavButton(isFavorite) {
    const btn = document.getElementById('btnFav');
    if (!btn) return;
    if (isFavorite) { 
        btn.innerHTML = '❤️ В избранном'; 
        btn.classList.add('active'); 
    } else { 
        btn.innerHTML = '🤍 В избранное'; 
        btn.classList.remove('active'); 
    }
}

async function loadFavorites() {
    if (!getToken()) { 
        document.getElementById('grid').innerHTML = '<div style="text-align:center; padding:50px;">Войдите чтобы видеть избранное</div>'; 
        return; 
    }
    const r = await authFetch('/api/favorites');
    const favorites = await r.json();
    const grid = document.getElementById('grid');
    if (!favorites.length) { 
        grid.innerHTML = '<div style="text-align:center; padding:50px;">У вас пока нет избранного</div>'; 
        return; 
    }
    grid.innerHTML = '';
    favorites.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        card.onclick = () => { 
            if (typeof openMovieModal === 'function') {
                openMovieModal(item.tmdb_id, item.media_type);
            }
        };
        const posterUrl = item.poster_path ? `/proxy-img?url=${item.poster_path}&id=fav_${item.tmdb_id}` : '/static/img/no-poster.jpg';
        card.innerHTML = `
            <div class="card-rating">★ ${item.vote_average?.toFixed(1) || '0.0'}</div>
            <img src="${posterUrl}">
            <div class="card-info">
                <div class="card-title">${escapeHtml(item.title)}</div>
                <div class="card-genres">${item.year || (item.media_type === 'movie' ? 'Фильм' : 'Сериал')}</div>
            </div>
            <button class="remove-fav-btn" onclick="event.stopPropagation(); removeFavorite(${item.tmdb_id}, '${item.media_type}')">✕</button>
        `;
        grid.appendChild(card);
    });
}

async function removeFavorite(tmdbId, type) {
    if (!confirm('Удалить из избранного?')) return;
    const r = await authFetch(`/api/favorites/${tmdbId}?type=${type}`, { method: 'DELETE' });
    if (r.ok) {
        showNotification('Удалено', 'info');
        loadFavorites();
    }
}

function openFavoritesModal() {
    const modal = document.getElementById('favoritesModal');
    if (modal) {
        modal.style.display = 'flex';
        loadFavoritesIntoModal();
    }
}

function closeFavoritesModal() { 
    const modal = document.getElementById('favoritesModal'); 
    if (modal) modal.style.display = 'none'; 
}

async function loadFavoritesIntoModal() {
    const container = document.getElementById('favoritesGrid');
    if (!container) return;
    if (!getToken()) { 
        container.innerHTML = '<div style="text-align:center; padding:40px;">Войдите чтобы видеть избранное</div>'; 
        return; 
    }
    container.innerHTML = '<div style="text-align:center; padding:40px;">Загрузка...</div>';
    const r = await authFetch('/api/favorites');
    const favorites = await r.json();
    if (!favorites.length) { 
        container.innerHTML = '<div style="text-align:center; padding:40px;">У вас пока нет избранного</div>'; 
        return; 
    }
    container.innerHTML = '';
    favorites.forEach(item => {
        const div = document.createElement('div');
        div.className = 'favorite-card';
        div.onclick = () => { 
            closeFavoritesModal(); 
            if (typeof openMovieModal === 'function') {
                openMovieModal(item.tmdb_id, item.media_type);
            }
        };
        const posterUrl = item.poster_path ? `/proxy-img?url=${item.poster_path}&id=fav_modal_${item.tmdb_id}` : '/static/img/no-poster.jpg';
        div.innerHTML = `
            <img src="${posterUrl}">
            <div class="favorite-info">
                <div class="favorite-title">${escapeHtml(item.title)}</div>
                <div class="favorite-year">${item.year || (item.media_type === 'movie' ? 'Фильм' : 'Сериал')}</div>
                <div class="favorite-rating">★ ${item.vote_average?.toFixed(1) || '0.0'}</div>
            </div>
            <button class="remove-fav-modal-btn" onclick="event.stopPropagation(); removeFavoriteFromModal(${item.tmdb_id}, '${item.media_type}')">✕</button>
        `;
        container.appendChild(div);
    });
}

async function removeFavoriteFromModal(tmdbId, type) {
    if (!confirm('Удалить из избранного?')) return;
    await authFetch(`/api/favorites/${tmdbId}?type=${type}`, { method: 'DELETE' });
    loadFavoritesIntoModal();
}

function openFavoritesFromProfile() { 
    closeProfileModal(); 
    setTimeout(() => openFavoritesModal(), 100); 
}

async function updateFavoriteButtonInModal() { 
    if (window.currentMovie) {
        const isFav = await checkIsFavorite(window.currentMovie.id, window.currentMovie.title ? 'movie' : 'tv');
        updateFavButton(isFav);
    }
}

function showNotification(msg, type) {
    let n = document.getElementById('notification');
    if (!n) { 
        n = document.createElement('div'); 
        n.id = 'notification'; 
        n.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;z-index:10001;background:#333;color:#fff;';
        document.body.appendChild(n); 
    }
    n.textContent = msg;
    n.style.background = type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3';
    n.style.display = 'block';
    setTimeout(() => n.style.display = 'none', 3000);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
}

function closeProfileModal() { 
    const m = document.getElementById('profileModal'); 
    if (m) m.style.display = 'none'; 
}

// Стили
const s = document.createElement('style');
s.textContent = `
    .btn-fav.active { background: #e50914; color:#fff; }
    .remove-fav-btn, .remove-fav-modal-btn {
        position:absolute; top:8px; right:8px; width:28px; height:28px; border-radius:50%;
        background:rgba(0,0,0,0.7); color:white; border:none; cursor:pointer;
    }
    .remove-fav-btn:hover, .remove-fav-modal-btn:hover { background:#e50914; }
    .favorite-card {
        display:flex; align-items:center; gap:15px; padding:10px; margin-bottom:10px;
        background:var(--card-bg); border-radius:10px; cursor:pointer; border:1px solid var(--glass-border);
        position:relative;
    }
    .favorite-card:hover { transform:translateX(5px); border-color:var(--accent); }
    .favorite-card img { width:50px; height:75px; object-fit:cover; border-radius:5px; }
    .favorite-info { flex:1; }
    .favorite-title { font-weight:bold; }
    .favorite-year { font-size:12px; opacity:0.7; }
    .favorite-rating { font-size:11px; color:#ffc107; }
    .remove-fav-modal-btn { position:relative; top:auto; right:auto; width:28px; height:28px; flex-shrink:0; }
`;
document.head.appendChild(s);

window.toggleFavorite = toggleFavorite;
window.loadFavorites = loadFavorites;
window.openFavoritesModal = openFavoritesModal;
window.closeFavoritesModal = closeFavoritesModal;
window.openFavoritesFromProfile = openFavoritesFromProfile;
window.updateFavoriteButtonInModal = updateFavoriteButtonInModal;