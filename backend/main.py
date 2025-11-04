from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers import (
    auth_controller,
    menu_controller,
    order_controller,
    payment_controller,
    report_controller,
    notification_controller
)

app = FastAPI(title="Sabor Limeño API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router)
app.include_router(menu_controller.router)
app.include_router(order_controller.router)
app.include_router(payment_controller.router)
app.include_router(report_controller.router)
app.include_router(notification_controller.router)

@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Sabor Limeño"}