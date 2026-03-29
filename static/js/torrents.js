// torrents.js

let currentId = null;
let currentType = 'movie';

function renderTorrents(ts) {
    const container = document.getElementById('mTorr');
    if (!container) return;
    
    if (!ts || ts.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:40px;">Раздач не найдено</div>';
        return;
    }

    container.innerHTML = ts.map(t => {
        const encodedLink = encodeURIComponent(t.Link);
        const token = getToken();
        const actionBtn = t.Magnet ? 
            `<a href="${t.Magnet}" target="_blank" class="btn-act btn-watch">Magnet</a>` : 
            `<a href="/api/download?url=${encodedLink}&token=${encodeURIComponent(token)}" target="_blank" class="btn-act btn-info">.torrent</a>`;

        return `
            <div class="t-row">
                <div class="t-name">${escapeHtml(t.Title)}</div>
                <div class="t-actions">
                    <span>${(t.Size/1024/1024/1024).toFixed(1)} GB</span>
                    <span>▲ ${t.Seeders}</span>
                    ${actionBtn}
                </div>
            </div>
        `;
    }).join('');
}

async function openM(m) {
    window.currentMovie = m;
    currentId = m.id;
    currentType = window.type || (m.title ? 'movie' : 'tv');
    
    document.getElementById('modal').style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    const posterUrl = m.poster_path ? `/proxy-img?url=${m.poster_path}&id=poster_${m.id}` : '/static/img/no-poster.jpg';
    document.getElementById('mPoster').src = posterUrl;
    
    const year = m.release_date ? m.release_date.split('-')[0] : (m.first_air_date ? m.first_air_date.split('-')[0] : '');
    document.getElementById('mTitle').innerText = `${m.title || m.name}${year ? ` (${year})` : ''}`;
    document.getElementById('mRating').innerText = `★ ${m.vote_average?.toFixed(1) || '0.0'} / 10`;
    document.getElementById('mDesc').innerHTML = m.overview || 'Описание отсутствует.';
    
    const gNames = (m.genre_ids || []).map(id => {
        const genres = window.GENRES_MAP?.[currentType] || [];
        const genre = genres.find(g => g.id === id);
        return genre ? genre.name : '';
    }).filter(Boolean).join(' • ');
    document.getElementById('mGenreLabel').innerText = gNames;

    document.getElementById('mTorr').innerHTML = '<div style="padding:40px; text-align:center;">Поиск раздач...</div>';
    
    const token = getToken();
    if (!token) {
        document.getElementById('mTorr').innerHTML = '<div style="text-align:center; padding:40px;"><button onclick="openAuthModal()" style="background:#e50914; color:white; border:none; padding:10px 20px; border-radius:20px;">Войти</button></div>';
        return;
    }
    
    try {
        const r = await authFetch(`/api/search/torrents?title=${encodeURIComponent(m.title || m.name)}&orig_title=${encodeURIComponent(m.original_title || m.original_name || '')}&year=${year}`);
        const ts = await r.json();
        if (!ts || ts.length === 0) {
            document.getElementById('mTorr').innerHTML = '<div style="text-align:center; padding:40px;">Раздач не найдено</div>';
            return;
        }
        renderTorrents(ts);
    } catch (e) {
        document.getElementById('mTorr').innerHTML = '<div style="text-align:center; padding:40px;">Ошибка поиска</div>';
    }
}

async function openMovieModal(tmdbId, mediaType) {
    showNotification('Загрузка...', 'info');
    try {
        const r = await fetch(`/api/details/${mediaType}/${tmdbId}`);
        const data = await r.json();
        const movieObj = {
            id: data.id,
            title: data.title || data.name,
            name: data.name || data.title,
            original_title: data.original_title || data.original_name,
            overview: data.overview,
            poster_path: data.poster_path,
            backdrop_path: data.backdrop_path,
            vote_average: data.vote_average,
            release_date: data.release_date,
            first_air_date: data.first_air_date,
            genre_ids: data.genres?.map(g => g.id) || []
        };
        window.type = mediaType;
        openM(movieObj);
        setTimeout(() => {
            if (typeof updateFavoriteButtonInModal === 'function') updateFavoriteButtonInModal();
        }, 100);
    } catch (e) { 
        console.error(e);
        showNotification('Ошибка загрузки', 'error'); 
    }
}

function closeM() { 
    document.getElementById('modal').style.display = 'none'; 
    document.body.style.overflow = 'auto'; 
    closeTrailerModal();
    delete window.currentMovie;
}

// ========== ТРЕЙЛЕР ==========
async function showTrailer() {
    const token = getToken();
    if (!token) { 
        openAuthModal(); 
        return; 
    }
    
    showNotification('Загрузка трейлера...', 'info');
    
    try {
        const r = await authFetch(`/api/trailer/${currentType}/${currentId}`);
        const d = await r.json();
        if (d.key) {
            openTrailerModal(d.key);
        } else {
            showNotification('Трейлер не найден', 'error');
        }
    } catch(e) {
        console.error(e);
        showNotification('Ошибка загрузки трейлера', 'error');
    }
}

function openTrailerModal(videoKey) {
    const modal = document.getElementById('trailerModal');
    const player = document.getElementById('trailerModalPlayer');
    if (!modal || !player) return;
    
    player.innerHTML = `<iframe src="https://www.youtube.com/embed/${videoKey}?autoplay=1&rel=0" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    const closeOnEscape = (e) => {
        if (e.key === 'Escape') {
            closeTrailerModal();
            document.removeEventListener('keydown', closeOnEscape);
        }
    };
    document.addEventListener('keydown', closeOnEscape);
    
    modal.onclick = (e) => {
        if (e.target === modal) closeTrailerModal();
    };
}

function closeTrailerModal() {
    const modal = document.getElementById('trailerModal');
    const player = document.getElementById('trailerModalPlayer');
    if (modal) modal.style.display = 'none';
    if (player) player.innerHTML = '';
    document.body.style.overflow = 'auto';
}

// ========== ВСПОМОГАТЕЛЬНЫЕ ==========
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

// ========== ЭКСПОРТ ==========
window.openM = openM;
window.closeM = closeM;
window.showTrailer = showTrailer;
window.closeTrailerModal = closeTrailerModal;
window.openMovieModal = openMovieModal;