# En login
@router.post("/login")
def login(data: dict):
    user = database.authenticate(data["email"], data["password"])
    if not user:
        return JSONResponse(status_code=401, content={"message": "Credenciales incorrectas"})
    
    token = database.create_session(user["id"]) # Nota: user["id"] no user.id
    return {"token": token, "user": user}

# En me
@router.get("/me")
def me(Authorization: Optional[str] = Header(default=None)):
    # ... validación token ...
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=403, content={"message": "Token expirado"})
    return user # Ya es un diccionario