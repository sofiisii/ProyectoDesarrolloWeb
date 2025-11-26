@router.get("/dashboard")
def get_admin_dashboard(Authorization: Optional[str] = Header(default=None)):
    # ... validación token ...
    
    stats = database.get_stats() # Usamos la función nueva de database.py
    return stats