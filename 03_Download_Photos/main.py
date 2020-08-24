import asyncio


COMMAND = 'zip -r - test/'


async def archivate(chunk_size=100):
    process = await asyncio.create_subprocess_shell(
        COMMAND,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    archive = bytes()

    while True:
        stdout_chunk = await process.stdout.read(chunk_size*1000)
        if not stdout_chunk:
            break

        archive += stdout_chunk

    with open('archive.zip', 'w+b') as file:
        file.write(archive)


def main():
    asyncio.run(archivate())


if __name__ == "__main__":
    main()
