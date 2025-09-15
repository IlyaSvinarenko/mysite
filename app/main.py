from fastapi import FastAPI
from app.routes import main, auth
from app.database import engine, Base
from app.models import user

# Создаем таблицы в БД (для разработки)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(title="MySite")

# Добавляем обработчик события запуска
@app.on_event("startup")
async def startup_event():
    await create_tables()

app.include_router(main.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Welcome to MySite"}