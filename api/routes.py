from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import logging
import uuid
from pathlib import Path
from typing import Dict, Any

# Все импорты строго вверху и один раз!
from app.db import get_recent_detections, insert_detection
from core.detector import detect_vehicles

logger = logging.getLogger(__name__)
router = APIRouter()

# Константы
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
TEMP_DIR = Path("temp_uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

# Создаем папку для временных файлов
TEMP_DIR.mkdir(exist_ok=True)


@router.get("/detections/recent")
def read_recent_detections(limit: int = 100) -> Dict[str, Any]:
    if not 1 <= limit <= 1000:
        raise HTTPException(status_code=422, detail="limit должен быть от 1 до 1000")
    return {"items": get_recent_detections(limit=limit)}


@router.post("/analyze")
async def analyze_traffic(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze traffic from uploaded image.
    Detects cars, buses, and trucks using YOLO model.
    """
    # Генерируем уникальное имя файла для безопасности
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    temp_filepath = TEMP_DIR / unique_filename
    
    try:
        # Проверяем расширение файла
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимый формат файла. Допустимые: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Проверяем размер файла
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой. Максимум: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
            )
        
        # 1. Сохраняем входящий файл во временную папку
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Считаем машины (вызываем импортированную функцию)
        result = detect_vehicles(str(temp_filepath))
        total = result.get("total", 0)
        details = result.get("details", {})
        
        # 3. Записываем в базу только типы объектов
        for obj_type, count in details.items():
            if count > 0:  # Пишем только то, что нашли
                insert_detection(count, obj_type)
        
        return {
            "traffic_count": total,
            "details": details,
            "filename": file.filename
        }

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Файл не найден при обработке: {e}")
        raise HTTPException(status_code=400, detail="Ошибка при обработке файла")
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Не удалось обработать изображение"
        )
    
    finally:
        # 4. Этот блок выполнится ВСЕГДА и удалит временный файл
        try:
            if temp_filepath.exists():
                temp_filepath.unlink()
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {temp_filepath}: {e}")