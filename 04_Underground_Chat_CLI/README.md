# Консольная утилита для подключения к чату

Для работы нужен Python версии не ниже 3.7.

## Как установить

```bash
git clone https://github.com/j0hntv/aio.git
cd 04_Underground_Chat_CLI/
python -m venv env
. env/bin/activate
pip install -r requirements.txt
```

## Как запустить

```bash
python listen_minechat.py
```
### Аргументы командной строки

- `--host` - адрес хоста, по умолчанию `minechat.dvmn.org`
- `--port` - номер порта, по умолчанию `5000`
- `--history` - путь к файлу с историей переписки, по умолчанию `messages.log`
### Поддерживаются переменные окружения:
- Создайте файл ```.env``` в корне проекта:
```bash
HOST=minechat.dvmn.org
PORT=5000
HISTORY_PATH=messages.log
```

# Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
