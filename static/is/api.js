function getToken() { 
    return localStorage.getItem('token'); 
}

function setToken(token) { 
    localStorage.setItem('token', token); 
}

function clearToken() { 
    localStorage.removeItem('token'); 
}

function authFetch(url, options = {}) {
    const token = getToken();
    if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(url, options);
}
