# AIOHTTP API

Этот проект представляет собой REST API для создания, редактирования и удаления объявлений с аутентификацией и авторизацией пользователей. API реализован с использованием библиотеки `aiohttp` и базой данных `SQLite`.

## Основные возможности

- Регистрация и авторизация пользователей
- Создание, получение и удаление объявлений
- Защита маршрутов с помощью JSON Web Token (JWT)
- Только авторизованные пользователи могут создавать объявления
- Только владелец объявления может его удалить

## Установка и запуск

### Предварительные требования

- Python 3.8+
- Виртуальное окружение (рекомендуется)

### Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/leadertv/aiohttp_api.git
   cd aiohttp_api
   ```

2. Создайте виртуальное окружение и активируйте его:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Для Linux/MacOS
   venv\Scripts\activate     # Для Windows
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

### Запуск сервера

Запустите сервер, выполнив следующую команду:

```bash
python main.py
```

Сервер будет доступен по адресу `http://localhost:5000`.

## Примеры запросов

### 1. Регистрация пользователя

```http
POST /register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword"
}
```

### 2. Авторизация пользователя (получение JWT токена)

```http
POST /login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword"
}
```

### 3. Создание объявления

```http
POST /ads
Content-Type: application/json
Authorization: Bearer <ВАШ_ТОКЕН>

{
    "title": "Продажа классного ноутбука",
    "description": "Новый ноутбук, отличное состояние, не ворованныйБ не перекуп! Пишите в ЛС, за звонок ночью будет БАН! Агенствам не беспокоить."
}
```

### 4. Получение объявления по ID

```http
GET /ads/{ad_id}
```

### 5. Удаление объявления по ID

```http
DELETE /ads/{ad_id}
Authorization: Bearer <ВАШ_ТОКЕН>
```

### Примечание

Замените `<ВАШ_ТОКЕН>` на действительный JWT токен из запроса авторизации.


