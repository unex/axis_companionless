from typing import TYPE_CHECKING

import aiofiles

from tqdm.asyncio import tqdm
from aiopath import AsyncPath
from httpx import AsyncClient, DigestAuth

from .util.parser import ParamParser


class Camera:
    def __init__(self, host: str, auth: DigestAuth):
        self._host = host
        self._client = AsyncClient(
            auth=auth, headers={"User-Agent": "Axis Companion/4.3.88+1"}, verify=False
        )

    async def param_list(self):
        r = await self._client.post(
            f"https://{self._host}/axis-cgi/param.cgi",
            data={"action": "list", "group": "root", "responseformat": "rfc"},
        )

        parser = ParamParser()
        params = parser.parse_from_string(r.text)

        return params.root

    async def fwpugrade(self, fw_file: AsyncPath):
        file_size = (await fw_file.stat()).st_size

        progress_bar = tqdm(
            total=file_size, unit="B", unit_scale=True, unit_divisor=1024
        )

        async def file_chunker():
            async with aiofiles.open(fw_file, "rb") as f:
                while data := await f.read(2048):
                    progress_bar.update(len(data))
                    yield data

        r = await self._client.post(
            f"https://{self._host}/axis-cgi/firmwareupgrade.cgi",
            data=file_chunker(),
            timeout=None,
            headers={"Content-Length": str(file_size)},
        )

        r.raise_for_status()
        progress_bar.close()

        print(f"File uploaded {r.status_code}")
        print(r.text)

    async def setparams(self, params: dict):
        r = await self._client.post(
            f"https://{self._host}/axis-cgi/param.cgi",
            data={"action": "update", **params},
        )
        r.raise_for_status()

        print(r.status_code, r.text)
