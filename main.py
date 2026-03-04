import os
import json
import hashlib
import asyncio
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from telegram import Bot
import asyncpg
import redis.asyncio as redis
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64

load_dotenv()

# Конфигурация
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
JWT_SECRET = os.getenv("JWT_SECRET", hashlib.sha256(os.urandom(32)).hexdigest())
CHUNK_SIZE = 50 * 1024 * 1024  # Увеличено с 20MB до 50MB для скорости
MAX_CONCURRENT_UPLOADS = 5  # Максимум 5 файлов одновременно

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Шифрование
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(ENCRYPTION_KEY).digest()))

# Мультипользовательский режим
def load_users_from_env():
    """Загрузка пользователей из .env"""
    users = {
        os.getenv("ADMIN_USERNAME", "admin"): {
            "password": pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin")),
            "role": "admin"
        }
    }

    # Загрузка дополнительных пользователей
    for key, value in os.environ.items():
        if key.startswith("USER_"):
            parts = value.split(":")
            if len(parts) >= 3:
                username, password, role = parts[0], parts[1], parts[2]
                users[username] = {
                    "password": pwd_context.hash(password),
                    "role": role
                }
    return users

USERS = load_users_from_env()

# База данных
class Database:
    def __init__(self):
        self.db_path = Path("data.json")
        self.data = {"users": {}, "files": {}, "folders": {}, "chunks": {}, "api_keys": {}}
        self.load()
    
    def load(self):
        if self.db_path.exists():
            with open(self.db_path) as f:
                self.data.update(json.load(f))
    
    def save(self):
        self.db_path.parent.mkdir(exist_ok=True)
        with open(self.db_path, "w") as f:
            json.dump(self.data, f, indent=2)
    
    async def init_postgres(self):
        if os.getenv("DATABASE_URL"):
            self.pg = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    
    async def init_redis(self):
        if os.getenv("REDIS_URL"):
            self.redis = await redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

db = Database()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Telegram боты
class BotManager:
    def __init__(self):
        self.bots = []
        self.channels = []
        self.load_tokens()
    
    def load_tokens(self):
        for key, value in os.environ.items():
            if key.startswith("BOT_TOKEN_"):
                self.bots.append(Bot(value))
            elif key.startswith("CHANNEL_ID_"):
                self.channels.append(value)
        
        self.bot_load = [0] * len(self.bots)
        self.bot_index = 0
    
    def get_next(self):
        if not self.bots or not self.channels:
            return None, None
        loads = [(i, self.bot_load[i]) for i in range(len(self.bots))]
        bot_idx = min(loads, key=lambda x: x[1])[0]
        channel_idx = self.bot_index % len(self.channels)
        self.bot_index += 1
        self.bot_load[bot_idx] += 1
        asyncio.create_task(self._decrease_load(bot_idx, 3))
        return self.bots[bot_idx], self.channels[channel_idx]
    
    async def _decrease_load(self, idx, seconds):
        await asyncio.sleep(seconds)
        self.bot_load[idx] = max(0, self.bot_load[idx] - 1)

bot_manager = BotManager()

# FastAPI приложение
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Опциональное подключение к БД
    database_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL")
    
    if database_url:
        try:
            await db.init_postgres()
            print("✓ PostgreSQL подключен")
        except Exception as e:
            print(f"⚠ PostgreSQL не подключен: {e}")
    
    if redis_url:
        try:
            await db.init_redis()
            print("✓ Redis подключен")
        except Exception as e:
            print(f"⚠ Redis не подключен: {e}")
    
    if not database_url and not redis_url:
        print("ℹ Работа с локальным хранилищем (data.json)")
    
    yield

app = FastAPI(title="Nimbus File", docs_url="/api/docs", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Функции для работы с файлами
async def save_file_chunks(data: bytes, filename: str, user_id: str, parent: str = "/") -> dict:
    # Шифрование данных (оптимизировано для скорости)
    encrypted_data = cipher.encrypt(data)
    
    # Разбиваем на чанки по 50MB
    chunks = [encrypted_data[i:i+CHUNK_SIZE] for i in range(0, len(encrypted_data), CHUNK_SIZE)]
    file_id = hashlib.sha256(f"{filename}{datetime.now()}{user_id}".encode()).hexdigest()[:16]
    chunk_ids = []

    # Параллельная отправка чанков
    async def send_chunk(i, chunk):
        bot, channel = bot_manager.get_next()
        if not bot:
            db.data["chunks"][f"{file_id}_{i}"] = chunk.hex()
            return f"{file_id}_{i}"
        else:
            await asyncio.sleep(random.uniform(0.3, 1))  # Уменьшена задержка
            msg = await bot.send_document(chat_id=channel, document=chunk, filename=f"{file_id}_part{i}")
            return msg.document.file_id

    # Отправляем чанки параллельно (максимум 3 одновременно)
    semaphore = asyncio.Semaphore(3)
    
    async def send_with_semaphore(i, chunk):
        async with semaphore:
            return await send_chunk(i, chunk)

    tasks = [send_with_semaphore(i, chunk) for i, chunk in enumerate(chunks)]
    chunk_ids = await asyncio.gather(*tasks)

    db.data["files"][file_id] = {
        "id": file_id, "name": filename, "size": len(data),
        "chunks": len(chunks), "chunk_ids": list(chunk_ids),
        "user_id": user_id, "created": datetime.now().isoformat(),
        "type": "file", "parent": parent, "encrypted": True
    }
    db.save()
    return db.data["files"][file_id]

async def get_file_chunks(file_id: str):
    file_info = db.data["files"].get(file_id)
    if not file_info:
        return None

    chunks = []
    for i, chunk_id in enumerate(file_info["chunk_ids"]):
        if chunk_id in db.data["chunks"]:
            chunks.append(bytes.fromhex(db.data["chunks"][chunk_id]))
        else:
            bot = bot_manager.bots[i % len(bot_manager.bots)]
            file = await bot.get_file(chunk_id)
            chunks.append(await file.download_as_bytearray())

    encrypted_data = b"".join(chunks)
    # Дешифрование данных
    try:
        decrypted_data = cipher.decrypt(encrypted_data)
        return decrypted_data
    except:
        return encrypted_data

# Аутентификация
def create_token(username: str) -> str:
    return jwt.encode({"sub": username, "exp": datetime.utcnow() + timedelta(days=30)}, JWT_SECRET)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None

async def get_current_user(request: Request):
    token = request.cookies.get("token")
    if token:
        username = verify_token(token)
        if username:
            return username
    raise HTTPException(401, "Not authenticated")

async def get_optional_user(request: Request):
    token = request.cookies.get("token")
    if token:
        return verify_token(token)
    return None

async def get_admin_user(request: Request):
    """Проверка на администратора"""
    user = await get_current_user(request)
    user_data = USERS.get(user, {})
    if user_data.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return user

# API маршруты
@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # Проверка пользователя
    user_data = USERS.get(username)
    if not user_data:
        raise HTTPException(401, "Invalid credentials")
    
    # Проверка пароля
    if not pwd_context.verify(password, user_data["password"]):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_token(username)
    response = JSONResponse({"success": True, "role": user_data.get("role", "user")})
    response.set_cookie("token", token, httponly=True, max_age=2592000)
    return response

@app.post("/api/logout")
async def logout():
    response = JSONResponse({"success": True})
    response.delete_cookie("token")
    return response

@app.get("/api/me")
async def me(user: str = Depends(get_optional_user)):
    if not user:
        return {"authenticated": False}

    user_data = USERS.get(user, {})
    api_keys = [k for k, v in db.data["api_keys"].items() if v["user"] == user]
    return {
        "authenticated": True,
        "user": user,
        "role": user_data.get("role", "user"),
        "api_keys": api_keys
    }

@app.post("/api/key/create")
async def create_api_key(name: str = Form(...), user: str = Depends(get_current_user)):
    key = hashlib.sha256(f"{user}{name}{datetime.now()}".encode()).hexdigest()[:32]
    db.data["api_keys"][key] = {"user": user, "name": name, "created": datetime.now().isoformat()}
    db.save()
    return {"key": key, "name": name}

@app.delete("/api/key/{key}")
async def delete_api_key(key: str, user: str = Depends(get_current_user)):
    if key in db.data["api_keys"] and db.data["api_keys"][key]["user"] == user:
        del db.data["api_keys"][key]
        db.save()
    return {"success": True}

@app.post("/api/upload")
async def upload_file(
    files: list[UploadFile] = File(...),
    path: str = Form("/"),
    user: str = Depends(get_current_user)
):
    """Загрузка нескольких файлов одновременно с параллелизацией"""
    import asyncio
    
    async def upload_single_file(file: UploadFile):
        data = await file.read()
        return await save_file_chunks(data, file.filename, user, path)
    
    # Параллельная загрузка файлов (максимум 5 одновременно)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)
    
    async def upload_with_semaphore(file: UploadFile):
        async with semaphore:
            return await upload_single_file(file)
    
    tasks = [upload_with_semaphore(file) for file in files]
    uploaded = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Фильтруем успешные загрузки
    success_files = [f for f in uploaded if isinstance(f, dict)]
    
    return {"files": success_files, "count": len(success_files), "total": len(files)}

@app.get("/api/files")
async def list_files(path: str = "/", user: str = Depends(get_current_user)):
    # Исправление: проверяем parent для файлов и папок
    files = [f for f in db.data["files"].values() 
             if (f.get("parent") == path or f.get("path") == path) and f["user_id"] == user]
    folders = [f for f in db.data["folders"].values() 
               if f.get("parent") == path and f["user_id"] == user]
    
    # Исправляем файлы у которых нет parent но есть path
    for file in files:
        if "parent" not in file:
            file["parent"] = file.get("path", "/")
    db.save()
    
    return {"files": files, "folders": folders}

@app.post("/api/folder")
async def create_folder(name: str = Form(...), path: str = Form("/"), user: str = Depends(get_current_user)):
    folder_id = hashlib.sha256(f"{name}{path}{user}".encode()).hexdigest()[:16]
    db.data["folders"][folder_id] = {
        "id": folder_id, "name": name, "path": path,
        "user_id": user, "created": datetime.now().isoformat(),
        "type": "folder", "parent": path
    }
    db.save()
    return db.data["folders"][folder_id]

@app.get("/api/file/{file_id}")
async def get_file(file_id: str, user: str = Depends(get_current_user)):
    file_info = db.data["files"].get(file_id)
    if not file_info or file_info["user_id"] != user:
        raise HTTPException(404, "File not found")
    return file_info

@app.get("/api/file/{file_id}/download")
async def download_file(file_id: str, user: str = Depends(get_current_user)):
    file_info = db.data["files"].get(file_id)
    if not file_info or file_info["user_id"] != user:
        raise HTTPException(404, "File not found")

    data = await get_file_chunks(file_id)
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_info["name"]}"'}
    )

@app.get("/api/file/{file_id}/view")
async def view_file(file_id: str, user: str = Depends(get_current_user)):
    """Предпросмотр файла (изображения, видео, аудио, текст)"""
    file_info = db.data["files"].get(file_id)
    
    # Проверка существования файла
    if not file_info:
        raise HTTPException(404, "File not found")
    
    # Проверка прав доступа
    if file_info.get("user_id") != user:
        raise HTTPException(403, "Access denied")

    try:
        data = await get_file_chunks(file_id)
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")

    # Определяем MIME тип по расширению
    ext = file_info["name"].split(".")[-1].lower() if "." in file_info["name"] else ""
    mime_types = {
        # Изображения
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
        "ico": "image/x-icon", "bmp": "image/bmp",
        # Видео
        "mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime",
        "avi": "video/x-msvideo", "mkv": "video/x-matroska",
        # Аудио
        "mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
        "m4a": "audio/mp4", "ogg": "audio/ogg",
        # Текст
        "txt": "text/plain", "md": "text/markdown", "json": "application/json",
        "xml": "application/xml", "html": "text/html", "css": "text/css",
        "js": "application/javascript", "ts": "application/typescript",
        "py": "text/x-python", "java": "text/x-java", "c": "text/x-c",
        "cpp": "text/x-c++", "go": "text/x-go", "rs": "text/x-rust",
        "php": "text/x-php", "rb": "text/x-ruby", "sh": "text/x-sh",
        "yaml": "text/yaml", "yml": "text/yaml", "csv": "text/csv",
    }

    media_type = mime_types.get(ext, "application/octet-stream")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{file_info["name"]}"'}
    )

@app.delete("/api/file/{file_id}")
async def delete_file(file_id: str, user: str = Depends(get_current_user)):
    file_info = db.data["files"].get(file_id)
    if file_info and file_info["user_id"] == user:
        for chunk_id in file_info["chunk_ids"]:
            if chunk_id in db.data["chunks"]:
                del db.data["chunks"][chunk_id]
        del db.data["files"][file_id]
        db.save()
    return {"success": True}

@app.put("/api/file/{file_id}")
async def rename_file(file_id: str, name: str = Form(...), user: str = Depends(get_current_user)):
    file_info = db.data["files"].get(file_id)
    if file_info and file_info["user_id"] == user:
        file_info["name"] = name
        db.save()
    return file_info

@app.post("/api/share/{file_id}")
async def share_file(file_id: str, user: str = Depends(get_current_user)):
    file_info = db.data["files"].get(file_id)
    if not file_info or file_info["user_id"] != user:
        raise HTTPException(404, "File not found")
    
    share_id = hashlib.sha256(f"{file_id}{datetime.now()}".encode()).hexdigest()[:16]
    db.data["shares"] = db.data.get("shares", {})
    db.data["shares"][share_id] = {"file_id": file_id, "created": datetime.now().isoformat()}
    db.save()
    return {"share_id": share_id, "url": f"/share/{share_id}"}

@app.get("/api/share/{share_id}")
async def get_shared_file(share_id: str):
    share = db.data.get("shares", {}).get(share_id)
    if not share:
        raise HTTPException(404, "Share not found")

    file_info = db.data["files"].get(share["file_id"])
    if not file_info:
        raise HTTPException(404, "File not found")

    data = await get_file_chunks(share["file_id"])
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_info["name"]}"'}
    )

# API ключ аутентификация
@app.post("/api/key/upload")
async def upload_with_key(
    file: UploadFile = File(...),
    path: str = Form("/"),
    api_key: str = Form(...)
):
    key_info = db.data["api_keys"].get(api_key)
    if not key_info:
        raise HTTPException(401, "Invalid API key")
    
    data = await file.read()
    return await save_file_chunks(data, file.filename, key_info["user"])

# Админские эндпоинты
@app.post("/api/admin/create_user")
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    admin: str = Depends(get_admin_user)
):
    """Создание нового пользователя (только для админов)"""
    if username in USERS:
        raise HTTPException(400, "User already exists")
    
    # Сохраняем в USERS (в памяти, для production нужна БД)
    USERS[username] = {
        "password": pwd_context.hash(password),
        "role": role
    }
    
    # Сохраняем в .env файл (опционально)
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "a") as f:
            f.write(f"\nUSER_{username.upper()}={username}:{password}:{role}")
    
    return {"success": True, "username": username, "role": role}

@app.delete("/api/admin/delete_user/{username}")
async def delete_user(username: str, admin: str = Depends(get_admin_user)):
    """Удаление пользователя (только для админов)"""
    if username not in USERS:
        raise HTTPException(404, "User not found")
    
    if username == os.getenv("ADMIN_USERNAME", "admin"):
        raise HTTPException(400, "Cannot delete main admin")
    
    del USERS[username]
    return {"success": True}

@app.get("/api/admin/users")
async def list_users(admin: str = Depends(get_admin_user)):
    """Список всех пользователей (только для админов)"""
    users = []
    for username, data in USERS.items():
        users.append({
            "username": username,
            "role": data.get("role", "user"),
            "api_keys_count": len([k for k, v in db.data["api_keys"].items() if v["user"] == username])
        })
    return {"users": users}

# Веб интерфейс
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: str = Depends(get_optional_user)):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user
    })

@app.get("/share/{share_id}", response_class=HTMLResponse)
async def share_page(request: Request, share_id: str):
    share = db.data.get("shares", {}).get(share_id)
    if not share:
        raise HTTPException(404, "Share not found")
    file_info = db.data["files"].get(share["file_id"])
    if not file_info:
        raise HTTPException(404, "File not found")
    return templates.TemplateResponse("share.html", {
        "request": request,
        "share_id": share_id,
        "file_name": file_info["name"],
        "file_size": file_info["size"]
    })

@app.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request):
    return templates.TemplateResponse("docs.html", {
        "request": request
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))