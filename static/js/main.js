// main.js

let type = 'movie';
window.type = type;
let query = '';
let genreId = '';
let page = 1;
let loading = false;

let currentCategory = 'popular';
window.filters = window.filters || {};

async function load(isNew = false) {
    if (loading) return;
    loading = true;
    if (isNew) { 
        page = 1; 
        document.getElementById('grid').innerHTML = ''; 
    }
    
    let url;
    
    if (query) {
        url = `/api/search/all?query=${encodeURIComponent(query)}&page=${page}`;
    } 
    else if (genreId) {
        url = `/api/discover/${type}/${genreId}?page=${page}`;
        currentCategory = 'genre';
    }
    else if (currentCategory === 'trending') {
        url = `/api/trending/${type}/day?page=${page}`;
    }
    else if (currentCategory === 'popular') {
        url = `/api/${type}/category?page=${page}`;
    }
    else if (currentCategory === 'top_rated') {
        url = `/api/${type}/category?cat=top_rated&page=${page}`;
    }
    else {
        url = `/api/${type}/category?page=${page}`;
    }
    
    try {
        const r = await fetch(url);
        const d = await r.json();
        
        if (!d.results || d.results.length === 0) {
            if (isNew) {
                document.getElementById('grid').innerHTML = '<div style="text-align:center; padding:50px;">Ничего не найдено</div>';
            }
            loading = false;
            return;
        }
        
        d.results?.forEach(m => {
            if (!m.poster_url) return;
            
            const gNames = (m.genre_ids || []).map(id => {
                const genres = window.GENRES_MAP?.[type] || [];
                const genre = genres.find(g => g.id === id);
                return genre ? genre.name : '';
            }).filter(Boolean).slice(0, 2).join(', ');
            
            const el = document.createElement('div');
            el.className = 'card';
            el.innerHTML = `
                <div class="card-rating">★ ${m.vote_average?.toFixed(1) || '0.0'}</div>
                <img src="${m.poster_url}">
                <div class="card-info">
                    <div class="card-title">${escapeHtml(m.title || m.name)}</div>
                    <div class="card-genres">${escapeHtml(gNames || (type === 'movie' ? 'Кино' : 'Сериал'))}</div>
                </div>
            `;
            el.onclick = () => openM(m);
            document.getElementById('grid').appendChild(el);
        });
    } catch (e) { 
        console.error("Load error:", e); 
        if (isNew) {
            document.getElementById('grid').innerHTML = '<div style="text-align:center; padding:50px;">Ошибка загрузки</div>';
        }
    }
    loading = false; 
    page++;
}

// main.js - исправленная функция setType

function setType(t) { 
    type = t; 
    query = ''; 
    genreId = ''; 
    currentCategory = 'popular';
    
    window.filters = {};
    
    document.querySelectorAll('.nav-item').forEach(b => {
        if (b.id === 'btn-movie' || b.id === 'btn-tv') {
            b.classList.toggle('active', b.id === `btn-${t}`);
        }
    });
    
    // ВАЖНО: сначала обновляем window.type, потом вызываем renderGenres
    window.type = type;
    
    if (typeof renderGenres === 'function') {
        renderGenres();
    }
    
    load(true); 
}

function handleSelectChange(value) {
    if (value === 'trending') {
        genreId = '';
        currentCategory = 'trending';
        load(true);
    } else if (value === 'popular') {
        genreId = '';
        currentCategory = 'popular';
        load(true);
    } else if (value === 'top_rated') {
        genreId = '';
        currentCategory = 'top_rated';
        load(true);
    } else {
        genreId = value;
        currentCategory = 'genre';
        load(true);
    }
}

let searchTimeout;
const searchInput = document.getElementById('sI');
if (searchInput) {
    searchInput.oninput = (e) => { 
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => { 
            query = e.target.value; 
            genreId = ''; 
            currentCategory = 'search';
            load(true); 
        }, 600); 
    };
}

window.onscroll = () => { 
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 800) {
        load(); 
    }
};

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

async function updateFavoriteButtonInModal() {
    const movie = window.currentMovie;
    if (!movie) return;
    const movieType = movie.title ? 'movie' : 'tv';
    if (typeof checkIsFavorite === 'function') {
        const isFav = await checkIsFavorite(movie.id, movieType);
        if (typeof updateFavButton === 'function') updateFavButton(isFav);
    }
}

window.type = type;
window.setType = setType;
window.handleSelectChange = handleSelectChange;
window.currentCategory = currentCategory;
window.genreId = genreId;
window.updateFavoriteButtonInModal = updateFavoriteButtonInModal;
window.loadCatalog = load;
window.escapeHtml = escapeHtml;

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (typeof renderGenres === 'function') renderGenres();
        load(true);
    }, 100);
    if (typeof updateAuthUI === 'function') updateAuthUI();
});