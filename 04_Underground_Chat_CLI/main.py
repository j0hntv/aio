import asyncio


async def tcp_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        while True:
            data = await reader.readline()
            print(data.decode().strip())

    except KeyboardInterrupt:
        print('[*] Exit.')

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    HOST = 'minechat.dvmn.org'
    PORT = 5000

    asyncio.run(tcp_client(HOST, PORT))
