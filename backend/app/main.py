from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import rag
from .config import config
from .database import Base, SessionLocal, engine
from .routers import admin, chat, payments, public, reservations, voice
from .seed import seed_if_empty
from .services.availability import ServiceError
from .voice.migrate import ensure_voice_columns


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    rag.init_schema(engine)           # knowledge_chunks + FTS5 tabloları
    with SessionLocal() as db:
        seed_if_empty(db)
    ensure_voice_columns(engine)      # settings'e sesli asistan sütunları (eski DB'lerde) + varsayılan karşılama
    rag.start_background_reindex()    # eksik/değişmiş kayıtları sunucuyu bloklamadan indeksle
    yield


app = FastAPI(title="BUNGAi API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list({config.frontend_url.rstrip("/"), "http://localhost:5173", "http://127.0.0.1:5173"}),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


_FIELD_TR = {
    "guest_name": "Ad soyad", "guest_email": "E-posta", "guest_phone": "Telefon", "guests": "Kişi sayısı",
    "check_in": "Giriş tarihi", "check_out": "Çıkış tarihi", "bungalow_id": "Bungalov", "message": "Mesaj",
    "card_number": "Kart numarası", "card_holder": "Kart sahibi", "username": "Kullanıcı adı", "password": "Şifre",
}


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = []
    for err in exc.errors():
        loc = err.get("loc", ())
        name = str(loc[-1]) if loc else "alan"
        fields.append(_FIELD_TR.get(name, name))
    detail = "Geçersiz veya eksik bilgi: " + ", ".join(dict.fromkeys(fields)) + "."
    return JSONResponse(status_code=422, content={"detail": detail})


for r in (public.router, reservations.router, payments.router, chat.router, voice.router, admin.router):
    app.include_router(r)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
