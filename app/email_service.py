import smtplib
import os
import ssl
import socket
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
        
        # Проверка доступности SMTP сервера временно отключена
        # (может блокироваться файрволом, но реальное подключение может работать)
        # Попытка подключения будет выполнена напрямую
        logger.info(f"Attempting to connect to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
        try:
            # Формируем содержимое заказа
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
                            <a href="{self.webapp_url}/static/ra.html?order_id={order_data['id']}&uid={order_data.get('user_id', '')}" class="button">
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
{self.webapp_url}/static/ra.html?order_id={order_data['id']}&uid={order_data.get('user_id', '')}

Это автоматическое уведомление. Не отвечайте на это письмо.
            """
            
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
            
            # Отправляем email
            # Для Yandex может потребоваться более длительный timeout
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
                raise
            finally:
                # Закрываем соединение в любом случае
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
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending order notification email for order #{order_data.get('id', 'unknown')} to {restaurant_email}: {e}", exc_info=True)
            return False

# Создаем глобальный экземпляр сервиса
email_service = EmailService() 