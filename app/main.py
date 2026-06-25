import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from .db import insert_metrics, get_recent  # настройте импорт под себя

app = FastAPI(title="Система мониторинга транспортных потоков")

# Создаем папку для сохранения картинок, если её нет
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Монтируем статику, чтобы картинки были доступны по URL (например, http://127.0.0.1:8000/static/uploads/photo.jpg)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {"status": "System Online"}


# Новый POST-эндпоинт, принимающий файл и метрики
@app.post("/api/v1/metrics/with-photo", status_code=201)
async def add_metrics_with_photo(
        camera_id: str = Form(...),
        vehicle_count: int = Form(...),
        average_speed: float = Form(...),
        traffic_jam_level: int = Form(...),
        file: UploadFile = File(...)  # Принимаем файл фото
):
    try:
        # Генерируем уникальное имя файла, чтобы они не перезаписывались
        import uuid
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Сохраняем файл на диск
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Сохраняем в БД путь к файлу (сохраняем web-friendly путь с косыми чертами)
        web_image_path = f"/static/uploads/{unique_filename}"

        insert_metrics(
            camera_id=camera_id,
            vehicle_count=vehicle_count,
            average_speed=average_speed,
            traffic_jam_level=traffic_jam_level,
            image_path=web_image_path
        )

        return {
            "status": "success",
            "message": "Metrics and photo saved",
            "image_url": web_image_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics/recent")
def read_recent(limit: int = 100):
    return get_recent(limit=limit)