# ☁️ Nimbus File

**Безлимитное облачное хранилище на базе Telegram с шифрованием AES-256**

Загружай любые файлы любого размера — они будут разделены на чанки, зашифрованы и распределены по Telegram каналам через ботов.

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 📁 **Безлимитное хранилище** | Используй Telegram как бесплатный бэкенд без ограничений |
| 🔐 **Шифрование AES-256** | Все файлы шифруются перед отправкой в Telegram |
| 🚀 **Балансировка нагрузки** | Автоматическое распределение между ботами и каналами |
| 👥 **Мультипользовательский режим** | Поддержка нескольких аккаунтов с ролями |
| 🌓 **Темная тема** | Автоматически сохраняется в cookie |
| 📱 **Адаптивный дизайн** | Работает на ПК, планшетах и телефонах |
| 🔑 **API ключи** | Для интеграции с другими сервисами |
| 📤 **Шеринг файлов** | Делись файлами по публичной ссылке |
| 📁 **Папки** | Организуй файлы как хочешь |
| ✏️ **Редактирование** | Переименовывай файлы |
| 🎬 **Медиаплеер** | Просмотр изображений, видео, аудио прямо на сайте |
| 📝 **Текстовый редактор** | Редактирование кода и текстовых файлов онлайн |
| 📊 **Прогресс загрузки** | Визуальный индикатор для больших файлов |

---

## 🚀 Быстрый старт

### 1. Установка

```bash
git clone https://github.com/hakeroneh1/nimbus-file.git
cd nimbus-file
pip install -r requirements.txt
```

### 2. Создаем ботов в Telegram

1. Напиши **@BotFather** в Telegram
2. Создай нужное количество ботов командой `/newbot`
3. Сохрани токены вида `123456:ABCdef...`

### 3. Создаем каналы

1. Создай приватные каналы в Telegram
2. Добавь ботов как администраторов
3. Получи ID каналов через **@getidsbot** (формат `-1001234567890`)

### 4. Настройка .env

Создай файл `.env` в корне проекта:

```env
# Админка
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET=supersecretkeychangeinproduction123

# Шифрование (сохрани этот ключ!)
ENCRYPTION_KEY=your-secret-encryption-key-here

# Telegram боты (можно несколько)
BOT_TOKEN_1=123456:ABCdef...
BOT_TOKEN_2=123456:ABCdef...

# Telegram каналы (можно несколько)
CHANNEL_ID_1=-1001234567890
CHANNEL_ID_2=-1001234567891

# База данных (для production)
DATABASE_URL=postgresql://user:pass@ep-cool.aws.neon.tech/db?sslmode=require
REDIS_URL=redis://localhost:6379

# Сервер
PORT=8000
BASE_URL=https://your-domain.com

# Дополнительные пользователи (опционально)
USER_ALICE=alice:password123:admin
USER_BOB=bob:password456:user
```

### 5. Запуск

```bash
python main.py
```

Открой браузер: **http://localhost:8000**  
Войди с логином/паролем из `.env`

---

## 👥 Пользователи и роли

### Добавление пользователей через .env

В файле `.env` можно добавить пользователей в формате:
```
USER_<ИМЯ>=<логин>:<пароль>:<роль>
```

**Роли:**
- `admin` — полный доступ, управление всеми файлами
- `user` — доступ только к своим файлам

**Пример:**
```env
USER_ALICE=alice:securepass:admin
USER_BOB=bob:password123:user
USER_CHARLIE=charlie:mypassword:user
```

### Создание пользователей через API

```bash
curl -X POST http://localhost:8000/api/admin/create_user \
  -d "username=newuser" \
  -d "password=securepass" \
  -d "role=user" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🌐 Настройка домена

### Для локальной сети

В `.env`:
```env
BASE_URL=http://192.168.1.100:8000
```

### Для Render / Vercel / Heroku

В `.env`:
```env
BASE_URL=https://nimbus-file.onrender.com
```

### Для своего домена

```env
BASE_URL=https://cloud.yourdomain.com
```

---

## 🚀 Деплой на Render

### 1. Создай аккаунт на render.com

Зайди на [render.com](https://render.com) и зарегистрируйся через GitHub

### 2. Создай Web Service

1. Нажми **"New +"** → **"Web Service"**
2. Подключи репозиторий: `https://github.com/hakeroneh1/nimbus-file`
3. Настройки:
   - **Name:** `nimbus-file`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** `Free`

### 3. Добавь переменные окружения

В разделе **Environment Variables** добавь:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET=supersecretkey
ENCRYPTION_KEY=your-secret-key
BOT_TOKEN_1=...
CHANNEL_ID_1=...
DATABASE_URL=postgresql://...
BASE_URL=https://nimbus-file.onrender.com
```

### 4. Подключи базу данных

**Neon DB** (бесплатно):

1. Зайди на [neon.tech](https://neon.tech)
2. Создай новый проект
3. Получи строку подключения
4. Добавь в переменные: `DATABASE_URL=postgresql://...`

### 5. Задеплой

Нажми **"Create Web Service"**  
Через 2-3 минуты сервер будет доступен по адресу `https://nimbus-file.onrender.com`

---

## 📚 API Документация

После запуска доступна по адресу **/api/docs**

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/login` | Вход в систему |
| `POST` | `/api/logout` | Выход |
| `GET` | `/api/me` | Информация о пользователе |

### Управление файлами

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/upload` | Загрузить файл |
| `GET` | `/api/files?path=/` | Список файлов и папок |
| `GET` | `/api/file/{id}` | Информация о файле |
| `GET` | `/api/file/{id}/download` | Скачать файл |
| `GET` | `/api/file/{id}/view` | **Просмотр файла онлайн** |
| `DELETE` | `/api/file/{id}` | Удалить файл |
| `PUT` | `/api/file/{id}` | Переименовать файл |

### Папки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/folder` | Создать папку |

### Шеринг

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/share/{file_id}` | Создать ссылку |
| `GET` | `/api/share/{share_id}` | Скачать по ссылке |

### API ключи

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/key/create` | Создать API ключ |
| `DELETE` | `/api/key/{key}` | Удалить API ключ |
| `POST` | `/api/key/upload` | Загрузить файл по API ключу |

### Администрирование

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/admin/create_user` | Создать пользователя |
| `DELETE` | `/api/admin/delete_user/{username}` | Удалить пользователя |
| `GET` | `/api/admin/users` | Список всех пользователей |

---

## 🔧 Примеры использования

### Python

```python
import requests

API_URL = "https://your-domain.com"
API_KEY = "ваш_api_ключ"

# ===== ЗАГРУЗКА ФАЙЛА =====
files = {"file": open("video.mp4", "rb")}
data = {"api_key": API_KEY, "path": "/"}
response = requests.post(f"{API_URL}/api/key/upload", files=files, data=data)
file_id = response.json()["id"]
print(f"Файл загружен: {file_id}")

# ===== СКАЧИВАНИЕ ФАЙЛА =====
response = requests.get(f"{API_URL}/api/file/{file_id}/download")
with open("downloaded.mp4", "wb") as f:
    f.write(response.content)

# ===== ПРОСМОТР ФАЙЛА (онлайн) =====
response = requests.get(f"{API_URL}/api/file/{file_id}/view")
# Открывается в браузере или плеере

# ===== СОЗДАНИЕ ПАПКИ =====
response = requests.post(
    f"{API_URL}/api/folder",
    data={"name": "Мои видео", "path": "/"}
)

# ===== ПЕРЕИМЕНОВАНИЕ ФАЙЛА =====
response = requests.put(
    f"{API_URL}/api/file/{file_id}",
    data={"name": "new_name.mp4"}
)

# ===== СОЗДАНИЕ ССЫЛКИ =====
response = requests.post(f"{API_URL}/api/share/{file_id}")
share_url = response.json()["url"]
print(f"Ссылка: {API_URL}{share_url}")

# ===== УДАЛЕНИЕ ФАЙЛА =====
response = requests.delete(f"{API_URL}/api/file/{file_id}")
```

### JavaScript

```javascript
const API_URL = "https://your-domain.com";
const API_KEY = "ваш_api_ключ";

// ===== ЗАГРУЗКА ФАЙЛА =====
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("api_key", API_KEY);
formData.append("path", "/");

fetch(`${API_URL}/api/key/upload`, {
    method: "POST",
    body: formData
})
.then(res => res.json())
.then(data => console.log("Файл загружен:", data.id));

// ===== ПРОСМОТР ИЗОБРАЖЕНИЯ =====
const img = document.createElement('img');
img.src = `${API_URL}/api/file/${fileId}/view`;
document.body.appendChild(img);

// ===== ПРОСМОТР ВИДЕО =====
const video = document.createElement('video');
video.controls = true;
video.src = `${API_URL}/api/file/${fileId}/view`;
document.body.appendChild(video);

// ===== СОЗДАНИЕ ПАПКИ =====
fetch(`${API_URL}/api/folder`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ name: "Новая папка", path: "/" })
});

// ===== СКАЧИВАНИЕ =====
window.open(`${API_URL}/api/file/${fileId}/download`);
```

### cURL

```bash
# ===== ЗАГРУЗКА ФАЙЛА =====
curl -X POST http://localhost:8000/api/key/upload \
  -F "file=@video.mp4" \
  -F "api_key=ваш_api_ключ" \
  -F "path=/"

# ===== ПРОСМОТР ФАЙЛА =====
curl -O http://localhost:8000/api/file/FILE_ID/view

# ===== СКАЧИВАНИЕ ФАЙЛА =====
curl -OJ http://localhost:8000/api/file/FILE_ID/download

# ===== СОЗДАНИЕ ПАПКИ =====
curl -X POST http://localhost:8000/api/folder \
  -d "name=Моя папка" \
  -d "path=/"

# ===== ПЕРЕИМЕНОВАНИЕ =====
curl -X PUT http://localhost:8000/api/file/FILE_ID \
  -d "name=новое_имя.txt"

# ===== УДАЛЕНИЕ =====
curl -X DELETE http://localhost:8000/api/file/FILE_ID

# ===== СОЗДАНИЕ ССЫЛКИ =====
curl -X POST http://localhost:8000/api/share/FILE_ID
```

### Node.js (с axios)

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

const API_URL = 'http://localhost:8000';
const API_KEY = 'ваш_api_ключ';

// Загрузка файла
async function uploadFile(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('api_key', API_KEY);
    form.append('path', '/');

    const response = await axios.post(`${API_URL}/api/key/upload`, form, {
        headers: form.getHeaders()
    });
    
    return response.data;
}

// Просмотр файла (получение данных)
async function viewFile(fileId) {
    const response = await axios.get(`${API_URL}/api/file/${fileId}/view`, {
        responseType: 'arraybuffer'
    });
    
    return response.data;
}

// Использование
uploadFile('./test.pdf')
    .then(data => console.log('Загружен:', data.id))
    .catch(console.error);
```

---

## ⚙️ Конфигурация

### Переменные окружения

|   Переменная     |        Описание               |         Пример           |
|------------------|-------------------------------|--------------------------|
| `ADMIN_USERNAME` | Логин администратора          | `admin`                  |
| `ADMIN_PASSWORD` | Пароль администратора         | `admin123`               |
| `JWT_SECRET`     | Секретный ключ JWT            | `supersecretkey`         |
| `ENCRYPTION_KEY` | Ключ шифрования AES           | `your-secret-key`        |
| `BOT_TOKEN_*`    | Токены Telegram ботов         | `123456:ABCdef...`       |
| `CHANNEL_ID_*`   | ID Telegram каналов           | `-1001234567890`         |
| `DATABASE_URL`   | PostgreSQL connection string  | `postgresql://...`       |
| `REDIS_URL`      | Redis connection string       | `redis://localhost:6379` |
| `PORT`           | Порт сервера                  | `8000`                   |
| `BASE_URL`       | URL сервера                   | `https://domain.com`     |
| `USER_*`         | Дополнительные пользователи   | `username:pass:role`     |

### Базы данных

**Локально** — данные хранятся в `data.json`

**На Render (production)** — обязательно используй Neon DB или аналог:
```env
DATABASE_URL=postgresql://user:pass@ep-cool.aws.neon.tech/db?sslmode=require
```

**Redis** (опционально, для кэширования):
```env
REDIS_URL=redis://default:pass@host:port
```

---

## 📦 Масштабирование

### Добавление ботов и каналов

Просто добавь новые переменные в `.env`:

```env
BOT_TOKEN_1=...
BOT_TOKEN_2=...
BOT_TOKEN_3=...
BOT_TOKEN_4=...

CHANNEL_ID_1=...
CHANNEL_ID_2=...
CHANNEL_ID_3=...
```

Система автоматически балансирует нагрузку между всеми ботами и каналами.

### Поддержка нескольких пользователей

```env
USER_ALICE=alice:password123:admin
USER_BOB=bob:password456:user
USER_CHARLIE=charlie:secret789:user
```

---

## 📁 Структура проекта

```
nimbus-file/
├── main.py                 # Основной файл приложения
├── .env                    # Конфигурация
├── requirements.txt        # Зависимости Python
└── templates/
    ├── index.html          # Веб-интерфейс
    ├── share.html          # Страница шаринга
    └── docs.html           # Документация API
```

---

## 🔐 Безопасность

- **JWT аутентификация** — токены с истечением срока
- **AES-256 шифрование** — все файлы шифруются перед отправкой
- **Изоляция пользователей** — каждый видит только свои файлы
- **Ролевая модель** — разделение прав доступа
- **HTTPS** — рекомендуется для production

---

## 📄 Лицензия

**MIT License** — Свободно используй, модифицируй и распространяй.

---

## 🤝 Поддержка

- **GitHub:** [hakeroneh1/nimbus-file](https://github.com/hakeroneh1/nimbus-file)
- **Issues:** [Сообщить о проблеме](https://github.com/hakeroneh1/nimbus-file/issues)

---

**Nimbus File** — Твои файлы. Твои правила. Без лимитов. ☁️

##**by haker_one**
