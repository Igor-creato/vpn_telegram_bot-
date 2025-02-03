import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import hmac
import hashlib
import base64
from database.db_handler import DatabaseHandler
import os
from telegram.ext import Application
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()
db = DatabaseHandler()

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
BOT_TOKEN = "7753890665:AAHcwEnhlPkjN2XvBJWbmd1mOEL4Z39hmtM"

async def get_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    await application.initialize()
    return application.bot

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        body = await request.body()
        notification = await request.json()
        logger.info(f"Получен webhook запрос: {notification}")
        
        payment_uid = notification['object']['id']
        payment_status = notification['object']['status']
        
        logger.info(f"Payment UID: {payment_uid}, Status: {payment_status}")
        
        payment_info = db.get_payment_by_uid(payment_uid)
        if payment_info:
            payment_id, amount, telegram_id = payment_info
            bot = await get_bot()
            
            if payment_status == 'succeeded':
                logger.info(f"Обновляем статус платежа {payment_id}")
                db.update_payment_status(payment_id, 'succeeded')
                
                try:
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=f"Вы оплатили заказ No{payment_id} на сумму {amount} рублей"
                    )
                    logger.info(f"Сообщение об оплате отправлено пользователю {telegram_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {str(e)}")
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": str(e)}
                    )
            else:
                db.delete_payment(payment_id)
                try:
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=f"Заказ No{payment_id} не оплачен. Попробуйте еще раз или свяжитесь с поддержкой."
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения об отмене: {str(e)}")
        
        return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        logger.error(f"Ошибка в webhook: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )