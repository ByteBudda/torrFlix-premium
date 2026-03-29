```markdown
# 🎬 torrFLIX Premium

## 📝 Описание

torrFLIX — это современный веб-сервис для просмотра фильмов и сериалов через торренты. Приложение интегрируется с TMDB (The Movie Database) для получения метаданных и с Jackett/Prowlarr для поиска торрент-раздач.

### ✨ Основные возможности

- 🔍 **Поиск и каталог** — фильмы, сериалы, популярное, новинки, лучшие по рейтингу
- 🎭 **Жанры** — полный список жанров для фильмов и сериалов (локальные ID)
- 👤 **Пользовательская система** — регистрация, авторизация, подтверждение email
- ⭐ **Избранное** — добавление контента в личную коллекцию
- 👤 **Профиль** — аватар, редактирование данных, смена пароля
- 🎬 **Трейлеры** — встроенный просмотр трейлеров через YouTube в модальном окне
- 📥 **Скачивание торрентов** — прямая загрузка .torrent файлов или magnet-ссылок
- 🔐 **Админ-панель** — управление пользователями и настройками API
- 🎨 **Темы оформления** — 15+ цветовых схем
- 🖼️ **Кэширование изображений** — все постеры кэшируются локально

---

## 🏗️ Архитектура проекта

```
```
torrflix2/
├── server.py                 # Главный файл приложения (FastAPI)
├── config.json               # Настройки API (TMDB, Jackett, SMTP)
├── config.json.example       # Шаблон настроек для GitHub
├── data.db                   # База данных SQLite (создается автоматически)
├── cache_img/                # Кэш изображений постеров
├── static/                   # Фронтенд
│   ├── index.html            # Главная страница
│   ├── css/
│   │   ├── base.css          # Базовые стили
│   │   ├── components.css    # Стили компонентов
│   │   └── themes/           # Папка с темами (15+ вариантов)
│   └── js/
│       ├── api.js            # API хелперы (токен, authFetch)
│       ├── auth.js           # Авторизация (логин, регистрация, восстановление)
│       ├── profile.js        # Личный кабинет
│       ├── favorites.js      # Система избранного
│       ├── ui.js             # UI компоненты (жанры, темы)
│       ├── torrents.js       # Работа с торрентами и трейлерами
│       └── main.js           # Основная логика (загрузка каталога, поиск)
├── app/                      # Бэкенд модули
│   ├── init.py
│   ├── auth.py               # JWT, регистрация, логин
│   ├── config.py             # Загрузка/сохранение config.json
│   ├── database.py           # SQLite (пользователи, избранное, кэш)
│   ├── tmdb.py               # Запросы к TMDB с кэшированием
│   ├── torrents.py           # Поиск торрентов через Jackett/Prowlarr
│   ├── download.py           # Прокси скачивания .torrent файлов
│   ├── email_service.py      # Отправка email (подтверждение, восстановление)
│   ├── models.py             # Pydantic модели
│   ├── static_files.py       # Статические файлы и прокси изображений
│   └── admin.py              # Админ-панель
├── requirements.txt          # Зависимости Python
├── .env                      # Переменные окружения (опционально)
├── .env.example              # Шаблон переменных окружения
└── .gitignore                # Игнорируемые файлы
```
```

---

## 🚀 Полная инструкция по деплою

### 📋 Требования к серверу

- **Операционная система**: Ubuntu 22.04/24.04 LTS (или любой Linux)
- **Минимальные требования**: 1 CPU, 1 GB RAM, 10 GB HDD
- **Рекомендуемые**: 2 CPU, 2 GB RAM, 20 GB SSD
- **Установленные пакеты**: git, python3, python3-pip, python3-venv, nginx, sqlite3

---

### 1. Подготовка сервера

```bash
# 1.1 Обновление системы
sudo apt update && sudo apt upgrade -y

# 1.2 Установка необходимых пакетов
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    sqlite3 \
    curl \
    wget \
    htop

# 1.3 Проверка установки
python3 --version   # Python 3.10+
sqlite3 --version   # SQLite 3.40+
```

2. Настройка фаервола

```bash
# Если ufw активен
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8800/tcp
sudo ufw enable
```

---

3. Получение API ключей

3.1 TMDB API Key

1. Зарегистрируйтесь на TMDB
2. Перейдите в настройки → API → Запросить API ключ
3. Получите ключ (например: f747d78c52f351ec61483b440af85aa7)

3.2 Jackett API Key

1. Установите Jackett (см. раздел 6)
2. Запустите Jackett: systemctl start jackett
3. Откройте http://your-server:9117
4. Скопируйте API Key из интерфейса

3.3 Prowlarr API Key (опционально)

1. Установите Prowlarr (см. раздел 6)
2. Запустите Prowlarr: systemctl start prowlarr
3. Откройте http://your-server:9696
4. Скопируйте API Key из настроек

3.4 Настройка SMTP для email уведомлений

Для Gmail:

· Включите двухфакторную аутентификацию
· Создайте пароль приложения
· SMTP: smtp.gmail.com:587

Для Mail.ru:

· Включите "Доступ по IMAP"
· Создайте пароль для внешних приложений
· SMTP: smtp.mail.ru:465 (SSL) или 587 (TLS)

Для Yandex:

· Включите "Доступ к почте через внешние клиенты"
· SMTP: smtp.yandex.ru:465 (SSL) или 587 (TLS)

---

4. Установка torrFLIX

```bash
# 4.1 Создание директории
cd /opt
sudo git clone https://github.com/your-username/torrflix2.git
sudo chown -R $USER:$USER torrflix2/
cd torrflix2

# 4.2 Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4.3 Создание конфигурации из шаблона
cp config.json.example config.json
nano config.json
```

config.json (заполните своими данными)

```json
{
  "tmdb_key": "ВАШ_TMDB_КЛЮЧ",
  "jack_url": "http://127.0.0.1:9117",
  "jack_key": "ВАШ_JACKETT_КЛЮЧ",
  "prowlarr_url": "http://127.0.0.1:9696",
  "prowlarr_key": "ВАШ_PROWLARR_КЛЮЧ",
  "smtp_server": "smtp.mail.ru",
  "smtp_port": 465,
  "smtp_user": "your-email@mail.ru",
  "smtp_password": "ВАШ_ПАРОЛЬ_ПРИЛОЖЕНИЯ",
  "site_url": "http://your-domain.com:8800"
}
```

4.4 Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

.env (заполните своими данными)

```bash
JWT_SECRET=сгенерируйте-случайную-строку-например-openssl-rand-64
ADMIN_USER=admin
ADMIN_PASS=ваш_сложный_пароль
```

---

5. Настройка systemd сервиса

```bash
sudo nano /etc/systemd/system/kino.service
```

kino.service

```ini
[Unit]
Description=torrFLIX Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/torrflix2
Environment="PATH=/opt/torrflix2/venv/bin"
ExecStart=/opt/torrflix2/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Включение и запуск
sudo systemctl daemon-reload
sudo systemctl enable kino.service
sudo systemctl start kino.service
sudo systemctl status kino.service
```

---

6. Установка Jackett и Prowlarr

6.1 Установка Jackett

```bash
# Скачивание последней версии
wget https://github.com/Jackett/Jackett/releases/latest/download/Jackett.Binaries.LinuxAMDx64.tar.gz
tar -xzf Jackett.Binaries.LinuxAMDx64.tar.gz
sudo mv Jackett /opt/
sudo useradd -r -s /bin/false jackett
sudo chown -R jackett:jackett /opt/Jackett

# Создание сервиса
sudo nano /etc/systemd/system/jackett.service
```

jackett.service

```ini
[Unit]
Description=Jackett
After=network.target

[Service]
Type=simple
User=jackett
Group=jackett
WorkingDirectory=/opt/Jackett
ExecStart=/opt/Jackett/Jackett --NoRestart
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Запуск Jackett
sudo systemctl daemon-reload
sudo systemctl enable jackett
sudo systemctl start jackett
sudo systemctl status jackett
```

6.2 Установка Prowlarr (опционально)

```bash
# Скачивание
wget https://github.com/Prowlarr/Prowlarr/releases/latest/download/Prowlarr.master.linux.tar.gz
tar -xzf Prowlarr.master.linux.tar.gz
sudo mv Prowlarr /opt/
sudo useradd -r -s /bin/false prowlarr
sudo chown -R prowlarr:prowlarr /opt/Prowlarr

# Создание сервиса
sudo nano /etc/systemd/system/prowlarr.service
```

prowlarr.service

```ini
[Unit]
Description=Prowlarr
After=network.target

[Service]
Type=simple
User=prowlarr
Group=prowlarr
WorkingDirectory=/opt/Prowlarr
ExecStart=/opt/Prowlarr/Prowlarr -nobrowser
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable prowlarr
sudo systemctl start prowlarr
```

---

7. Настройка Nginx (для 80/443 порта)

7.1 Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/kino
```

kino (конфигурация Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/torrflix2/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

7.2 Активация и тестирование

```bash
sudo ln -s /etc/nginx/sites-available/kino /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

7.3 Настройка HTTPS (Let's Encrypt)

```bash
sudo certbot --nginx -d your-domain.com
```

После этого обновите site_url в config.json:

```json
{
  "site_url": "https://your-domain.com"
}
```

```bash
sudo systemctl restart kino.service
```

---

8. Проверка работоспособности

```bash
# 8.1 Проверка сервисов
sudo systemctl status kino.service
sudo systemctl status jackett.service
sudo systemctl status nginx

# 8.2 Проверка доступности
curl http://localhost:8800
curl https://your-domain.com

# 8.3 Проверка базы данных
sqlite3 /opt/torrflix2/data.db "SELECT name FROM sqlite_master WHERE type='table';"

# 8.4 Просмотр логов
sudo journalctl -u kino.service -f
sudo journalctl -u jackett.service -f
sudo tail -f /var/log/nginx/access.log
```

---

9. Создание администратора

1. Откройте https://your-domain.com/admin
2. Введите логин: admin, пароль: из .env (по умолчанию password)
3. В настройках сохраните API ключи
4. В списке пользователей одобрите нужных пользователей

---

10. Обновление приложения

```bash
# 10.1 Остановка сервиса
sudo systemctl stop kino.service

# 10.2 Резервное копирование
cd /opt/torrflix2
cp data.db data.db.backup_$(date +%Y%m%d)
cp config.json config.json.backup

# 10.3 Обновление
git pull
source venv/bin/activate
pip install -r requirements.txt

# 10.4 Оптимизация базы данных
sqlite3 data.db "VACUUM;"

# 10.5 Запуск
sudo systemctl start kino.service
```

---

11. Мониторинг и обслуживание

11.1 Автоматическое резервное копирование (crontab)

```bash
sudo crontab -e
```

Добавить:

```cron
# Ежедневное резервное копирование в 3:00
0 3 * * * cp /opt/torrflix2/data.db /backups/data_$(date +\%Y\%m\%d).db
# Еженедельная очистка кэша старше 30 дней
0 4 * * 0 find /opt/torrflix2/cache_img -type f -mtime +30 -delete
```

11.2 Просмотр использования ресурсов

```bash
# Использование диска
df -h
du -sh /opt/torrflix2/cache_img/

# Использование памяти и CPU
htop

# Размер базы данных
du -sh /opt/torrflix2/data.db
```

11.3 Скрипт быстрого деплоя

```bash
nano /opt/torrflix2/deploy.sh
```

deploy.sh

```bash
#!/bin/bash
set -e
echo "🚀 Начинаем деплой torrFLIX..."

cd /opt/torrflix2
git pull
source venv/bin/activate
pip install -r requirements.txt
sqlite3 data.db "VACUUM;"
sudo systemctl restart kino.service

echo "✅ Деплой завершен!"
```

```bash
chmod +x /opt/torrflix2/deploy.sh
/opt/torrflix2/deploy.sh
```

---

🐛 Устранение неполадок

Проблема: 404 Not Found на /api/details/

Решение: Проверьте эндпоинт в server.py

Проблема: Не отправляются email

Решение:

1. Проверьте SMTP настройки в config.json
2. Для Gmail используйте пароль приложения
3. Для Mail.ru включите "Доступ по IMAP"
4. Просмотр логов: sudo journalctl -u kino.service -f

Проблема: Не ищутся торренты

Решение:

```bash
# Проверка Jackett
sudo systemctl status jackett
curl "http://127.0.0.1:9117/api/v2.0/indexers/all/results?apikey=YOUR_KEY&Query=test"
```

Проблема: Не грузятся постеры

Решение:

```bash
# Проверка прав на папку
chmod 755 /opt/torrflix2/cache_img/
# Проверка прокси
curl http://localhost:8800/proxy-img?url=/test.jpg&id=test
```

Проблема: Ошибка базы данных

Решение:

```bash
# Проверка целостности
sqlite3 /opt/torrflix2/data.db "PRAGMA integrity_check;"
# Восстановление из бэкапа
cp data.db.backup data.db
```

---

🔐 Безопасность

Рекомендации:

1. Смените пароль администратора в .env
2. Используйте HTTPS через Let's Encrypt
3. Ограничьте доступ к админ-панели через nginx:

```nginx
location /admin {
    allow YOUR_IP;
    deny all;
    proxy_pass http://127.0.0.1:8800;
}
```

1. Регулярно обновляйте систему и зависимости
2. Настройте автоматическое резервное копирование
3. Используйте сложный JWT_SECRET

---

📦 Файлы для GitHub (без секретов)

config.json.example

```json
{
  "tmdb_key": "YOUR_TMDB_API_KEY",
  "jack_url": "http://127.0.0.1:9117",
  "jack_key": "YOUR_JACKETT_API_KEY",
  "prowlarr_url": "http://127.0.0.1:9696",
  "prowlarr_key": "YOUR_PROWLARR_API_KEY",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your-email@gmail.com",
  "smtp_password": "your-app-password",
  "site_url": "http://localhost:8800"
}
```

.env.example

```bash
JWT_SECRET=your-super-secret-key-change-this
ADMIN_USER=admin
ADMIN_PASS=change-this-password
```

.gitignore

```gitignore
# Python
__pycache__/
venv/
*.pyc

# Database
data.db
data.db-*

# Config with secrets
config.json
.env

# Cache
cache_img/

# IDE
.vscode/
.idea/
```

---

📝 Лицензия

MIT License

---

👥 Контакты

· Документация: GitHub Wiki
· Issues: GitHub Issues

---

© 2026 torrFLIX. Все права защищены.

```
