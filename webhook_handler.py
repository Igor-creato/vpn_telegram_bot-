from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import hmac
import hashlib
import base64
from database.db_handler import DatabaseHandler
import os

app = FastAPI()
db = DatabaseHandler()

# Получаем секретный ключ из переменной окружения
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        body = await request.body()
        signature = request.headers.get('X-Signature')
        
        # Используем ключ из переменной окружения
        hmac_obj = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha1)
        calculated_signature = base64.b64encode(hmac_obj.digest()).decode()
        
        if signature and hmac.compare_digest(calculated_signature, signature):
            notification = await request.json()
            
            if notification['event'] == 'payment.succeeded':
                payment_id = notification['object']['id']
                db.update_payment_status(payment_id, 'succeeded')
            
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
