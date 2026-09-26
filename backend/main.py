from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importación de Routers
from app.entrypoints.api.auth_router import router as auth_router
from app.entrypoints.api.pacientes_router import router as pacientes_router
from app.entrypoints.api.analisis_router import router as analisis_router

# Intentar importar el router de enmiendas si ya fue creado
try:
    from app.entrypoints.api.enmiendas_router import router as enmiendas_router
    HAS_ENMIENDAS = True
except ImportError:
    HAS_ENMIENDAS = False

app = FastAPI(
    title="LIS - Hospital Metodista API",
    version="1.0.0",
    description="Sistema de Información de Laboratorio (LIS)"
)

# Configurar CORS para React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de rutas
app.include_router(auth_router)
app.include_router(pacientes_router)
app.include_router(analisis_router)

if HAS_ENMIENDAS:
    app.include_router(enmiendas_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API LIS Hospital Metodista funcionando"}