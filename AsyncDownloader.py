import asyncio
import re
import time
from abc import ABC, abstractmethod

import aiohttp

RE_MATCH_HTTP = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
DEBUG = False


class AbstactDownoloader(ABC):

    @abstractmethod
    def download(self):
        pass

    @abstractmethod
    def write_file(self):
        pass

    @abstractmethod
    def validate(self):
        pass


class AsyncDownloader(AbstactDownoloader):

    def __init__(self) -> None:
        self.count: int = 0
        self.session: aiohttp.ClientSession
        self.lock = asyncio.Lock()

    async def write_file(self, response: aiohttp.ClientResponse, name: str):
        with open(name, 'wb') as file:
            async for chunk in response.content.iter_chunked(1024):
                file.write(chunk)

    async def download(self, url: str):
        res = await self.session.get(url)
        async with self.lock:
            self.count += 1
            print(f'\r    Started downloading a file from {url}', end='\n> ')
            print(f'\r    Downloading {self.count} files', end='\n> ')

        await self.write_file(res, await self.get_file_name(url))

        async with self.lock:
            self.count -= 1
            print(f'\r    Finished downloading a file from {url}', end='\n> ')
            if self.count:
                print(f'\r    Downloading {self.count} files', end='\n> ')
            else:
                print(f'\r    All files downloaded', end='\n> ')

    async def validate(self, url) -> bool:
        return bool(re.match(RE_MATCH_HTTP, url))

    async def get_file_name(self, url: str) -> str:
        if not DEBUG:
            return url.split('/')[-1]
        else:
            return str(time.time())

    async def main(self):
        loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession()
        while True:

            url = await loop.run_in_executor(None, input, '> ')

            if url == 'exit':
                await self.session.close()
                break

            if await self.validate(url):
                asyncio.create_task(self.download(url))
            else:
                print('Invalid http url')


if __name__ == "__main__":
    downloader = AsyncDownloader()
    asyncio.run(downloader.main())
