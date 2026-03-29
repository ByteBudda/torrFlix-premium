// profile.js

let currentProfile = null;

async function loadProfile() {
    try {
        const r = await authFetch('/api/profile');
        if (!r.ok) throw new Error('Failed to load profile');
        currentProfile = await r.json();
        updateProfileUI();
        return currentProfile;
    } catch (e) {
        console.error('Load profile error:', e);
        return null;
    }
}

function updateProfileUI() {
    if (!currentProfile) return;
    
    document.getElementById('profileUsername').textContent = currentProfile.username;
    document.getElementById('profileEmail').textContent = currentProfile.email;
    document.getElementById('profileStatus').textContent = currentProfile.approved ? '✅ Активен' : '⏳ Ожидает подтверждения';
    document.getElementById('profileDate').textContent = new Date(currentProfile.created_at).toLocaleDateString('ru-RU');
    
    const avatar = document.getElementById('profileAvatar');
    if (currentProfile.avatar_url) {
        avatar.src = currentProfile.avatar_url;
    } else {
        avatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(currentProfile.username)}&background=e50914&color=fff&size=128`;
    }
}

function openProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) {
        loadProfile();
        modal.style.display = 'flex';
        modal.style.zIndex = '10001';
    }
}

function closeProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) modal.style.display = 'none';
}

function showEditProfile() {
    closeProfileModal();
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        document.getElementById('editEmail').value = currentProfile?.email || '';
        modal.style.display = 'flex';
        modal.style.zIndex = '10001';
    }
}

function closeEditProfileModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) modal.style.display = 'none';
    openProfileModal();
}

async function saveProfile() {
    const email = document.getElementById('editEmail').value;
    const currentPass = document.getElementById('editCurrentPassword').value;
    const newPass = document.getElementById('editNewPassword').value;
    const confirmPass = document.getElementById('editConfirmPassword').value;
    
    const msgDiv = document.getElementById('editProfileMessage');
    
    if (newPass && newPass !== confirmPass) {
        msgDiv.textContent = 'Пароли не совпадают';
        msgDiv.style.color = '#e50914';
        return;
    }
    
    if (newPass && newPass.length < 8) {
        msgDiv.textContent = 'Пароль должен быть минимум 8 символов';
        msgDiv.style.color = '#e50914';
        return;
    }
    
    const updateData = {};
    if (email && email !== currentProfile.email) updateData.email = email;
    if (newPass) {
        updateData.current_password = currentPass;
        updateData.new_password = newPass;
    }
    
    try {
        const r = await authFetch('/api/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        if (r.ok) {
            msgDiv.textContent = '✅ Профиль обновлен!';
            msgDiv.style.color = '#4caf50';
            setTimeout(() => {
                closeEditProfileModal();
                loadProfile();
            }, 1500);
        } else {
            const err = await r.json();
            msgDiv.textContent = err.detail || 'Ошибка обновления';
            msgDiv.style.color = '#e50914';
        }
    } catch (e) {
        msgDiv.textContent = 'Ошибка соединения';
        msgDiv.style.color = '#e50914';
    }
}

document.getElementById('avatarUpload')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (event) => {
        const base64 = event.target.result;
        try {
            const r = await authFetch('/api/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ avatar_url: base64 })
            });
            if (r.ok) {
                loadProfile();
                showNotification('Аватар обновлен', 'success');
            }
        } catch (e) {
            console.error('Avatar upload error:', e);
            showNotification('Ошибка загрузки аватара', 'error');
        }
    };
    reader.readAsDataURL(file);
});

function showNotification(message, type) {
    let n = document.getElementById('notification');
    if (!n) {
        n = document.createElement('div');
        n.id = 'notification';
        n.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;z-index:10001;background:#333;color:#fff;';
        document.body.appendChild(n);
    }
    n.textContent = message;
    n.style.background = type === 'success' ? '#4caf50' : '#f44336';
    n.style.display = 'block';
    setTimeout(() => n.style.display = 'none', 3000);
}

window.openProfileModal = openProfileModal;
window.closeProfileModal = closeProfileModal;
window.showEditProfile = showEditProfile;
window.closeEditProfileModal = closeEditProfileModal;
window.saveProfile = saveProfile;
window.loadProfile = loadProfile;