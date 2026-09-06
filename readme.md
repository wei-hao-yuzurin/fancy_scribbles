# Fancy Scribbles

Возможности
Создание, хранение и чтение заметок онлайн, серверная часть работает на системе Linux

## Стек
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- pytest
- passlib

## Установка 
1. `git clone git@github.com:wei-hao-yuzurin/fancy_scribbles.git` — копирование на ваше устройство (можно загрузить ZIP архив)
2. `cd ...` (перейти в директорию)
3. `cp .env\(Copy\) .env`
4. `nano .env` — задайте собственные переменные окружения
5. `docker compose up --build`

**Необходимый набор software для запуска:** Docker

## Примеры API запросов

```bash
curl -i -X POST http://193.187.93.217/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123"}'
curl -i -X POST http://193.187.93.217/api/register   -H "Content-Type: application/json"   -d '{"email":"test@example.com","password":"testpassword123"}'
```
## Ответ
```http
HTTP/1.1 200 OK
Server: nginx/1.31.4
Date: Sun, 06 Sep 2026 05:23:12 GMT
Content-Type: application/json
Content-Length: 35
Connection: keep-alive
```

```bash
curl -i -X POST http://193.187.93.217/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=test@example.com&password=testpassword123'
```
```http
HTTP/1.1 200 OK
Server: nginx/1.31.4
Date: Sun, 06 Sep 2026 05:24:19 GMT
Content-Type: application/json
Content-Length: 180
Connection: keep-alive

{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzg4NjczMTU5fQ.UbeSMjqJBgcHwyCz3noL5NfWiKHFO1V0DdS3ztkSCrU","token_type":"bearer"}
```

```bash
curl -i -X POST http://193.187.93.217/api/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzg4NjczMTU5fQ.UbeSMjqJBgcHwyCz3noL5NfWiKHFO1V0DdS3ztkSCrU" \
  -d '{"title":"Моя заметка","text":"Текст заметки","tags":["Работа"]}'
```
```http
HTTP/1.1 200 OK
Server: nginx/1.31.4
Date: Sun, 06 Sep 2026 05:25:53 GMT
Content-Type: application/json
Content-Length: 126
Connection: keep-alive

{"id":10,"title":"Моя заметка","text":"Текст заметки","tags":["Работа"],"created_at":"2026-09-06"}
```

```bash
url -i -X GET http://193.187.93.217/api/notes \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzg4NjczMTU5fQ.UbeSMjqJBgcHwyCz3noL5NfWiKHFO1V0DdS3ztkSCrU"
```
```http
HTTP/1.1 200 OK
Server: nginx/1.31.4
Date: Sun, 06 Sep 2026 05:26:30 GMT
Content-Type: application/json
Content-Length: 183
Connection: keep-alive

{"items":[{"id":10,"title":"Моя заметка","text":"Текст заметки","tags":["Работа"],"created_at":"2026-09-06"}],"page":1,"limit":5,"total":1,"total_pages":1}
```