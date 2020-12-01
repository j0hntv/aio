# Консольная утилита для подключения к чату

- Адрес чата: [minechat.dvmn.org](minechat.dvmn.org)
- Порт для чтения сообщений: `5000`
- Порт отправки сообщений: `5050`

Для работы нужен Python версии не ниже 3.7.

## Как установить

```bash
git clone https://github.com/j0hntv/aio.git
cd 04_Underground_Chat_CLI/
python -m venv env
. env/bin/activate
pip install -r requirements.txt
```

## Чтение сообщений из чата
```bash
python listen_minechat.py
```
### Аргументы командной строки

- `--host` - адрес хоста, по умолчанию `minechat.dvmn.org`
- `-p`, `--port` - номер порта, по умолчанию `5000`
- `-l`, `--logfile` - путь к файлу с историей переписки, по умолчанию `messages.log`

## Отправка сообщений в чат:

```bash
python write_minechat.py
```
### Аргументы командной строки

- `--host` - адрес хоста, по умолчанию `minechat.dvmn.org`
- `-p`, `--port` - номер порта, по умолчанию `5050`
- `-t`, `--token` - токен для авторизации в чате
- `-m`, `--message` - сообщение
- `-u`, `--username` - логин (для регистрации нового юзера)

### Поддерживаются переменные окружения:
- Создайте файл ```.env``` в корне проекта:
```bash
HOST=minechat.dvmn.org
LISTEN_PORT=5000
WRITE_PORT=5050
TOKEN=...
LOGFILE=messages.log
```

# Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
