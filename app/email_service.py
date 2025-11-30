import smtplib
import os
import ssl
import socket
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "")
        self.webapp_url = os.getenv("WEBAPP_URL", "")
        
        # HTTP API настройки (Resend.com - бесплатный тариф 100 писем/день)
        self.use_http_api = os.getenv("USE_HTTP_API", "false").lower() == "true"
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")
        self.resend_from_email = os.getenv("RESEND_FROM_EMAIL", self.from_email)
        
    def send_order_notification(self, restaurant_email: str, restaurant_name: str, order_data: Dict[str, Any]) -> bool:
        """
        Отправляет уведомление о новом заказе на email ресторана
        """
        if not restaurant_email:
            logger.warning(f"Email notification skipped for order #{order_data.get('id', 'unknown')}: restaurant email is empty")
            return False
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning(f"Email notification skipped for order #{order_data.get('id', 'unknown')}: SMTP credentials are missing (username: {bool(self.smtp_username)}, password: {bool(self.smtp_password)})")
            return False
        
        if not self.from_email:
            logger.warning(f"Email notification skipped for order #{order_data.get('id', 'unknown')}: FROM_EMAIL is not set")
            return False
        
        # Формируем содержимое заказа (нужно для обоих методов)
        order_items = []
        total = 0
        
        for item in order_data.get('items', []):
            item_total = item['price'] * item['qty']
            total += item_total
            order_items.append(f"• {item['name']} × {item['qty']} - {item_total} ₽")
        
        # Формируем email
        subject = f"Новый заказ #{order_data['id']} - {restaurant_name}"
        
        # Создаем HTML версию письма
        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8fafc; padding: 20px; border-radius: 0 0 8px 8px; }}
                    .order-info {{ background: white; padding: 15px; margin: 15px 0; border-radius: 6px; border-left: 4px solid #3b82f6; }}
                    .order-items {{ background: white; padding: 15px; margin: 15px 0; border-radius: 6px; }}
                    .total {{ font-weight: bold; font-size: 18px; color: #1f2937; }}
                    .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
                    .button:hover {{ background: #059669; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Новый заказ #{order_data['id']}</h1>
                        <p>Ресторан: {restaurant_name}</p>
                    </div>
                    
                    <div class="content">
                        <div class="order-info">
                            <h3>Информация о заказе</h3>
                            <p><strong>Статус:</strong> Обрабатывается оператором</p>
                            <p><strong>Дата:</strong> {order_data.get('created_at', 'Не указана')}</p>
                            <p><strong>Адрес доставки:</strong> {order_data.get('delivery_address', 'Не указан')}</p>
                            <p><strong>Способ оплаты:</strong> {order_data.get('payment_method', 'Не указан')}</p>
                        </div>
                        
                        <div class="order-items">
                            <h3>Состав заказа</h3>
                            <ul style="list-style: none; padding: 0;">
                                {''.join([f'<li style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{item}</li>' for item in order_items])}
                            </ul>
                            <hr style="margin: 15px 0;">
                            <p class="total">Итого: {total} ₽</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{self.webapp_url}/static/ra.html?order_id={order_data['id']}&uid={order_data.get('admin_id', '')}&restaurant_id={order_data.get('restaurant_id', '')}" class="button">
                                Открыть заказ в боте
                            </a>
                        </div>
                        
                        <div class="footer">
                            <p>Это автоматическое уведомление. Не отвечайте на это письмо.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
        # Создаем текстовую версию письма
        text_content = f"""
Новый заказ #{order_data['id']} - {restaurant_name}

Статус: Обрабатывается оператором
Дата: {order_data.get('created_at', 'Не указана')}
Адрес доставки: {order_data.get('delivery_address', 'Не указан')}
Способ оплаты: {order_data.get('payment_method', 'Не указан')}

Состав заказа:
{chr(10).join(order_items)}

Итого: {total} ₽

Для обработки заказа перейдите по ссылке:
{self.webapp_url}/static/ra.html?order_id={order_data['id']}&uid={order_data.get('admin_id', '')}&restaurant_id={order_data.get('restaurant_id', '')}

Это автоматическое уведомление. Не отвечайте на это письмо.
        """
        
        # Если включен HTTP API или SMTP недоступен, используем HTTP API
        if self.use_http_api or self.resend_api_key:
            logger.info("Используется HTTP API для отправки email")
            return self._send_via_resend_api(restaurant_email, restaurant_name, order_data, subject, text_content, html_content)
        
        # Пробуем SMTP
        logger.info(f"Attempting to connect to SMTP server: {self.smtp_server}:{self.smtp_port}")
        
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = restaurant_email
            
            # Добавляем части сообщения
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            logger.info(f"Attempting to connect to SMTP server {self.smtp_server}:{self.smtp_port}")
            
            server = None
            try:
                # Для порта 465 используем SSL, для 587 - STARTTLS
                if self.smtp_port == 465:
                    # SSL соединение для порта 465
                    logger.info("Using SSL connection (port 465)")
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30, context=context)
                else:
                    # STARTTLS для порта 587
                    logger.info("Using STARTTLS connection (port 587)")
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                    server.set_debuglevel(0)  # Устанавливаем 0 для продакшена, 1 для отладки
                    # Включаем STARTTLS
                    server.starttls()
                
                # Логинимся
                logger.info(f"Attempting to login as {self.smtp_username}")
                server.login(self.smtp_username, self.smtp_password)
                logger.info("SMTP login successful")
                
                # Отправляем сообщение
                server.send_message(msg)
                logger.info(f"Message sent successfully to {restaurant_email}")
                
            except smtplib.SMTPConnectError as e:
                logger.error(f"SMTP connection error: {e}")
                raise
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication error: {e}")
                raise
            except (ConnectionError, OSError) as e:
                logger.error(f"Network error connecting to SMTP server: {e}")
                raise
            except Exception as e:
                logger.error(f"Error during SMTP operation: {e}")
                if server:
                    try:
                        server.quit()
                    except Exception as e:
                        logger.warning(f"Error closing SMTP connection: {e}")
                        try:
                            server.close()
                        except:
                            pass
            
            logger.info(f"Order notification email sent to {restaurant_email} for order #{order_data['id']}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending order notification email for order #{order_data.get('id', 'unknown')} to {restaurant_email}: {e}", exc_info=True)
            return False
        except (ConnectionError, OSError) as e:
            logger.error(f"Network error sending order notification email for order #{order_data.get('id', 'unknown')} to {restaurant_email}: {e} (SMTP server: {self.smtp_server}:{self.smtp_port})", exc_info=True)
            # Если SMTP недоступен, пробуем HTTP API
            logger.info("SMTP недоступен, пробуем отправить через HTTP API...")
            return self._send_via_resend_api(restaurant_email, restaurant_name, order_data, subject, text_content, html_content)
        except Exception as e:
            logger.error(f"Unexpected error sending order notification email for order #{order_data.get('id', 'unknown')} to {restaurant_email}: {e}", exc_info=True)
            # Пробуем HTTP API как fallback
            logger.info("SMTP ошибка, пробуем отправить через HTTP API...")
            return self._send_via_resend_api(restaurant_email, restaurant_name, order_data, subject, text_content, html_content)
    
    def _send_via_resend_api(self, restaurant_email: str, restaurant_name: str, order_data: Dict[str, Any], 
                             subject: str, text_content: str, html_content: str) -> bool:
        """
        Отправка email через Resend.com HTTP API
        Бесплатный тариф: 100 писем/день, 3000 писем/месяц
        """
        # Проверяем наличие API ключа
        if not self.resend_api_key:
            logger.warning("RESEND_API_KEY не указан, невозможно отправить через HTTP API")
            return False
        
        try:
            # Формируем запрос к Resend API
            api_url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": self.resend_from_email or self.from_email,
                "to": [restaurant_email],
                "subject": subject,
                "text": text_content,
                "html": html_content
            }
            
            logger.info(f"Отправка email через Resend API для заказа #{order_data.get('id', 'unknown')} на {restaurant_email}")
            
            # Используем httpx для асинхронного запроса (но вызываем синхронно)
            response = httpx.post(api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email успешно отправлен через Resend API. ID: {result.get('id', 'unknown')}")
                return True
            else:
                logger.error(f"Ошибка Resend API: {response.status_code} - {response.text}")
                return False
                
        except httpx.RequestError as e:
            logger.error(f"Ошибка сети при отправке через Resend API: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке через Resend API: {e}", exc_info=True)
            return False

# Создаем глобальный экземпляр сервиса
email_service = EmailService() 