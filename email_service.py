# app/email_service.py
import asyncio
import smtplib
import ssl
import socket
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from .config import get_cfg

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.cfg = get_cfg()
    
    async def send_email(self, to_email: str, subject: str, html_content: str):
        """Асинхронная отправка email через SMTP с поддержкой SSL/TLS"""
        
        print("=" * 60)
        print("📧 НАЧАЛО ОТПРАВКИ EMAIL")
        print(f"   Время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Получатель: {to_email}")
        print(f"   Тема: {subject}")
        print("-" * 60)
        
        # Проверка настроек
        if not self.cfg.smtp_user or not self.cfg.smtp_password:
            logger.warning("SMTP не настроен - нет логина или пароля")
            print("❌ SMTP не настроен - отсутствуют логин или пароль")
            print("   Проверьте config.json: smtp_user и smtp_password")
            print("=" * 60)
            return False
        
        if not self.cfg.smtp_server:
            logger.warning("SMTP сервер не указан")
            print("❌ SMTP сервер не указан")
            print("   Проверьте config.json: smtp_server")
            print("=" * 60)
            return False
        
        print(f"✅ SMTP настройки:")
        print(f"   Сервер: {self.cfg.smtp_server}")
        print(f"   Порт: {self.cfg.smtp_port}")
        print(f"   Логин: {self.cfg.smtp_user}")
        print(f"   Пароль: {'*' * len(self.cfg.smtp_password) if self.cfg.smtp_password else 'НЕ УСТАНОВЛЕН'}")
        print(f"   URL сайта: {getattr(self.cfg, 'site_url', 'http://31.57.106.229:8900')}")
        
        # Запускаем SMTP в отдельном потоке
        loop = asyncio.get_event_loop()
        
        def send_sync():
            start_time = time.time()
            try:
                print("📝 Создание письма...")
                # Создаем сообщение
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = formataddr(("torrFLIX", self.cfg.smtp_user))
                msg['To'] = to_email
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                print(f"   Размер письма: {len(html_content)} байт")
                
                # Выбираем тип подключения в зависимости от порта
                port = self.cfg.smtp_port
                server = None
                
                if port == 465:
                    # SSL подключение (для Mail.ru, Yandex, Gmail с SSL)
                    print(f"🔒 Используем SSL подключение на порту {port}")
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(self.cfg.smtp_server, port, context=context, timeout=30)
                    server.ehlo()
                    
                elif port == 587:
                    # TLS подключение (для Mail.ru, Gmail, Yandex)
                    print(f"🔓 Используем TLS подключение на порту {port}")
                    server = smtplib.SMTP(self.cfg.smtp_server, port, timeout=30)
                    server.ehlo()
                    print("   STARTTLS...")
                    server.starttls()
                    server.ehlo()
                    
                elif port == 25:
                    # Стандартный SMTP порт
                    print(f"🔓 Используем обычное SMTP подключение на порту {port}")
                    server = smtplib.SMTP(self.cfg.smtp_server, port, timeout=30)
                    server.ehlo()
                    
                else:
                    print(f"⚠️ Неизвестный порт {port}, пробуем TLS")
                    server = smtplib.SMTP(self.cfg.smtp_server, port, timeout=30)
                    server.ehlo()
                    try:
                        server.starttls()
                        server.ehlo()
                    except:
                        pass
                
                if not server:
                    print("❌ Не удалось создать SMTP соединение")
                    return False
                
                print(f"📡 Подключено к {self.cfg.smtp_server}:{port}")
                
                # Авторизация
                print(f"🔐 Авторизация как {self.cfg.smtp_user}...")
                server.login(self.cfg.smtp_user, self.cfg.smtp_password)
                print("✅ Авторизация успешна")
                
                # Отправка
                print(f"📤 Отправка письма на {to_email}...")
                server.sendmail(self.cfg.smtp_user, [to_email], msg.as_string())
                server.quit()
                
                elapsed = time.time() - start_time
                print(f"✅ Письмо успешно отправлено за {elapsed:.2f} сек")
                logger.info(f"Email отправлен на {to_email} за {elapsed:.2f} сек")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                elapsed = time.time() - start_time
                print(f"❌ Ошибка авторизации (через {elapsed:.2f} сек):")
                print(f"   {e}")
                print("\n   Возможные причины:")
                print("   1. Неправильный логин или пароль")
                print("   2. Для Mail.ru нужно включить 'Доступ по IMAP' в настройках")
                print("   3. Для Gmail нужен пароль приложения, а не обычный")
                print("   4. Для Yandex нужно включить 'Доступ к почте через внешние клиенты'")
                logger.error(f"SMTP Authentication Error: {e}")
                return False
                
            except smtplib.SMTPConnectError as e:
                elapsed = time.time() - start_time
                print(f"❌ Ошибка подключения (через {elapsed:.2f} сек):")
                print(f"   {e}")
                print("\n   Проверьте:")
                print(f"   - Доступен ли сервер {self.cfg.smtp_server}:{port}")
                print("   - Не блокирует ли фаервол порт")
                print("   - Правильный ли порт (для Mail.ru: 465 или 587)")
                logger.error(f"SMTP Connect Error: {e}")
                return False
                
            except smtplib.SMTPException as e:
                elapsed = time.time() - start_time
                print(f"❌ SMTP ошибка (через {elapsed:.2f} сек):")
                print(f"   {e}")
                logger.error(f"SMTP Error: {e}")
                return False
                
            except socket.timeout as e:
                elapsed = time.time() - start_time
                print(f"❌ Таймаут подключения (через {elapsed:.2f} сек):")
                print(f"   {e}")
                print("   Проверьте интернет-соединение и доступность SMTP сервера")
                return False
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Неожиданная ошибка (через {elapsed:.2f} сек):")
                print(f"   Тип: {type(e).__name__}")
                print(f"   Сообщение: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"Unexpected error: {e}")
                return False
        
        # Запускаем синхронную функцию в потоке
        try:
            print("🚀 Запуск отправки в отдельном потоке...")
            result = await loop.run_in_executor(None, send_sync)
            print("=" * 60)
            return result
        except Exception as e:
            print(f"❌ Ошибка при запуске потока: {e}")
            print("=" * 60)
            return False
    
    async def send_verification_email(self, to_email: str, username: str, token: str):
        """Письмо с подтверждением регистрации"""
        site_url = getattr(self.cfg, 'site_url', 'http://31.57.106.229:8900')
        verify_url = f"{site_url}/verify?token={token}"
        
        print(f"🔐 Создание письма подтверждения для {username} ({to_email})")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Подтверждение регистрации в torrFLIX</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #e50914 0%, #b81c0c 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                    margin: -30px -30px 20px -30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #e50914 0%, #b81c0c 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .button:hover {{
                    opacity: 0.9;
                    transform: scale(1.02);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #999;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 12px;
                    margin: 15px 0;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎬 torrFLIX</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{username}</strong>!</p>
                    <p>Спасибо за регистрацию в нашем сервисе. Для завершения регистрации и активации аккаунта, пожалуйста, подтвердите ваш email адрес.</p>
                    
                    <div style="text-align: center;">
                        <a href="{verify_url}" class="button">✅ Подтвердить email</a>
                    </div>
                    
                    <p>Или скопируйте ссылку в браузер:</p>
                    <p style="background: #f0f0f0; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
                        {verify_url}
                    </p>
                    
                    <div class="warning">
                        ⚠️ <strong>Важно:</strong> Ссылка действительна в течение 24 часов.
                    </div>
                    
                    <p>После подтверждения вы сможете:</p>
                    <ul>
                        <li>🔍 Искать и смотреть любые фильмы и сериалы</li>
                        <li>⭐ Добавлять контент в избранное</li>
                        <li>📱 Получать рекомендации на основе ваших предпочтений</li>
                    </ul>
                    
                    <p>Если вы не регистрировались на torrFLIX, просто проигнорируйте это письмо.</p>
                    
                    <p>С уважением,<br>Команда torrFLIX</p>
                </div>
                <div class="footer">
                    <p>© 2026 torrFLIX. Все права защищены.</p>
                    <p>Это автоматическое сообщение, пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, "Подтверждение регистрации в torrFLIX", html)
    
    async def send_reset_email(self, to_email: str, username: str, token: str):
        """Письмо для восстановления пароля"""
        site_url = getattr(self.cfg, 'site_url', 'http://31.57.106.229:8800')
        reset_url = f"{site_url}/reset-password?token={token}"
        
        print(f"🔐 Создание письма восстановления для {username} ({to_email})")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Восстановление пароля - torrFLIX</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #e50914 0%, #b81c0c 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                    margin: -30px -30px 20px -30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #e50914 0%, #b81c0c 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .button:hover {{
                    opacity: 0.9;
                    transform: scale(1.02);
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 12px;
                    margin: 15px 0;
                    font-size: 13px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #999;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 torrFLIX</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{username}</strong>!</p>
                    <p>Мы получили запрос на восстановление пароля для вашего аккаунта.</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">🔄 Сбросить пароль</a>
                    </div>
                    
                    <p>Или скопируйте ссылку в браузер:</p>
                    <p style="background: #f0f0f0; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
                        {reset_url}
                    </p>
                    
                    <div class="warning">
                        ⚠️ <strong>Важно:</strong> Ссылка действительна в течение 1 часа.
                    </div>
                    
                    <p>Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.</p>
                    
                    <p>С уважением,<br>Команда torrFLIX</p>
                </div>
                <div class="footer">
                    <p>© 2026 torrFLIX. Все права защищены.</p>
                    <p>Это автоматическое сообщение, пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, "Восстановление пароля torrFLIX", html)

# Глобальный экземпляр
email_service = EmailService()