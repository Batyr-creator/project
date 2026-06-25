from ultralytics import YOLO

# Загружаем модель один раз при старте модуля
model = YOLO("yolov8n.pt")


def detect_vehicles(image_path: str):
    # model(image_path) уже делает предсказание, model.predict() отдельно не нужен
    results = model(image_path)

    # Инициализируем счетчики
    counts = {"cars": 0, "buses": 0, "trucks": 0}

    # ID классов в модели COCO: 2 = car, 5 = bus, 7 = truck
    class_map = {2: "cars", 5: "buses", 7: "trucks"}

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])

            # Если объект — это то, что мы ищем
            if cls_id in class_map:
                key = class_map[cls_id]
                counts[key] += 1

    # Считаем общий итог
    total = sum(counts.values())

    # Возвращаем красивый JSON
    return {
        "total": total,
        "details": counts
    }