# webhook_handler.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import hmac
import hashlib
import base64
from database.db_handler import DatabaseHandler
import os

app = FastAPI()
db = DatabaseHandler()

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        body = await request.body()
        signature = request.headers.get('X-Signature')
        
        hmac_obj = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha1)
        calculated_signature = base64.b64encode(hmac_obj.digest()).decode()
        
        if signature and hmac.compare_digest(calculated_signature, signature):
            notification = await request.json()
            payment_uid = notification['object']['id']
            payment_status = notification['object']['status']
            
            payment_info = db.get_payment_by_uid(payment_uid)
            if payment_info:
                payment_id, amount, telegram_id = payment_info
                
                if payment_status == 'succeeded':
                    db.update_payment_status(payment_id, 'succeeded')
                    bot.send_message(
                        telegram_id,
                        f"Вы оплатили заказ No{payment_id} на сумму {amount} рублей"
                    )
                else:
                    db.delete_payment(payment_id)
                    bot.send_message(
                        telegram_id,
                        f"Заказ No{payment_id} не оплачен. Попробуйте еще раз или свяжитесь с поддержкой."
                    )
            
            return JSONResponse(content={"status": "ok"})
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid signature"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
