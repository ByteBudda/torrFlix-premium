// ui.js

// ========== ТЕМЫ ==========
const THEMES = {
    'dark': '🌙 Тёмная',
    'light': '☀️ Светлая',
    'cinemora': '🎥 Кинемора',
    'velvetnight': '🖤 Бархатная ночь',
    'obsidian': '⚫ Обсидиан',
    'aurora': '🌌 Аврора',
    'sunset': '🌅 Закат',
    'ocean': '🌊 Океан',
    'minimal': '◻️ Минимализм',
    'voidglitch': '☢️ Цифровая Бездна',
    'bloodvoid': '🩸 Кровавая Бездна',
    'toxichaze': '☣️ Токсичный Туман',
    'chromefall': '🟠 Ржавый Хром',
    'retro': '📼 Ретро',
    'cyberpunk': '💀 Киберпанк'
};

function setTheme(themeName) {
    const themeLink = document.getElementById('theme-style');
    if (!themeLink) {
        const link = document.createElement('link');
        link.id = 'theme-style';
        link.rel = 'stylesheet';
        link.href = `/static/css/themes/${themeName}.css`;
        document.head.appendChild(link);
    } else {
        themeLink.href = `/static/css/themes/${themeName}.css`;
    }
    localStorage.setItem('theme', themeName);
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) themeSelect.value = themeName;
}

// ========== ЖАНРЫ (ЛОКАЛЬНЫЕ) ==========
window.GENRES_MAP = {
    'movie': [
        {id: 28, name: "🔥 Боевик"},
        {id: 12, name: "🏃 Приключения"},
        {id: 16, name: "🎨 Мультфильм"},
        {id: 35, name: "😂 Комедия"},
        {id: 80, name: "🔫 Криминал"},
        {id: 99, name: "📹 Документальный"},
        {id: 18, name: "🎭 Драма"},
        {id: 10751, name: "👨‍👩‍👧‍👦 Семейный"},
        {id: 14, name: "🧙 Фэнтези"},
        {id: 36, name: "📜 История"},
        {id: 27, name: "😱 Ужасы"},
        {id: 10402, name: "🎵 Музыка"},
        {id: 9648, name: "🔍 Детектив"},
        {id: 10749, name: "💕 Мелодрама"},
        {id: 878, name: "🤖 Фантастика"},
        {id: 10770, name: "📺 ТВ фильм"},
        {id: 53, name: "⏰ Триллер"},
        {id: 10752, name: "⚔️ Военный"},
        {id: 37, name: "🤠 Вестерн"}
    ],
    'tv': [
        {id: 10759, name: "🔥 Боевик и приключения"},
        {id: 16, name: "🎨 Мультфильм"},
        {id: 35, name: "😂 Комедия"},
        {id: 80, name: "🔫 Криминал"},
        {id: 99, name: "📹 Документальный"},
        {id: 18, name: "🎭 Драма"},
        {id: 10751, name: "👨‍👩‍👧‍👦 Семейный"},
        {id: 10762, name: "👶 Детский"},
        {id: 9648, name: "🔍 Детектив"},
        {id: 10763, name: "📰 Новости"},
        {id: 10764, name: "🎤 Реалити-шоу"},
        {id: 10765, name: "🧙 НФ и фэнтези"},
        {id: 10766, name: "💕 Мыльная опера"},
        {id: 10767, name: "🎙️ Ток-шоу"},
        {id: 10768, name: "⚔️ Война и политика"},
        {id: 37, name: "🤠 Вестерн"}
    ]
};

// ========== РЕНДЕР ЖАНРОВ ==========
// ui.js - функция renderGenres

function renderGenres() {
    const s = document.getElementById('gS');
    if (!s) return;
    // Берем текущий тип из window.type
    const currentType = window.type || 'movie';
    const genres = window.GENRES_MAP[currentType] || [];
    
    console.log('renderGenres called, type:', currentType, 'genres count:', genres.length);
    
    let options = '<option value="trending">🔥 Смотрят сейчас</option>';
    options += '<option value="popular">⭐ Популярное</option>';
    options += '<option value="top_rated">🏆 Лучшее</option>';
    options += '<option disabled>──────────</option>';
    options += genres.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
    
    s.innerHTML = options;
    
    if (window.currentCategory === 'trending') s.value = 'trending';
    else if (window.currentCategory === 'popular') s.value = 'popular';
    else if (window.currentCategory === 'top_rated') s.value = 'top_rated';
    else if (window.currentCategory === 'genre' && window.genreId) s.value = window.genreId;
    else s.value = 'popular';
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function getTags(title, tracker) {
    const t = title.toLowerCase();
    let h = `<span class="tag tag-tracker">${escapeHtml(tracker || '')}</span>`;
    const studios = ['lostfilm', 'hdrezka', 'rezka', 'alexfilm', 'anilibria', 'tvshows'];
    studios.forEach(s => { if (t.includes(s)) h += `<span class="tag tag-studio">${s}</span>`; });
    if (t.includes('1080')) h += `<span class="tag tag-res">1080p</span>`;
    if (t.includes('dub') || t.includes('дубляж')) h += `<span class="tag tag-audio">DUB</span>`;
    return h;
}

// ========== ИНИЦИАЛИЗАЦИЯ ==========
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.value = savedTheme;
        themeSelect.addEventListener('change', (e) => setTheme(e.target.value));
    }
    renderGenres();
});

window.renderGenres = renderGenres;
window.getTags = getTags;
window.escapeHtml = escapeHtml;