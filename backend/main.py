from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

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

#--- Registrar routers ---
app.include_router(auth_controller.router)
app.include_router(menu_controller.router)
app.include_router(order_controller.router)
app.include_router(payment_controller.router)
app.include_router(report_controller.router)
app.include_router(notification_controller.router)

@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Sabor Limeño"}


#--- Agregar esquema de seguridad para mostrar el candado en Swagger ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Sabor Limeño API",
        version="1.0.0",
        description="API del restaurante Sabor Limeño",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
#--- Fin de la adición ---