import asyncio
import aiofiles
from datetime import datetime


async def tcp_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        while True:
            data = await reader.readline()
            time = datetime.now().strftime('[%Y.%m.%d %H:%M]')
            
            print(data.decode().strip())
            
            async with aiofiles.open('log.txt', 'a') as file:
                await file.write(f'{time} {data.decode()}')

    except KeyboardInterrupt:
        print('[*] Exit.')

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    HOST = 'minechat.dvmn.org'
    PORT = 5000

    asyncio.run(tcp_client(HOST, PORT))
