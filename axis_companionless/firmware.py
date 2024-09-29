import aiofiles

from tqdm.asyncio import tqdm
from aiopath import AsyncPath
from httpx import AsyncClient


FIRMWARE_BASE = "https://www.axis.com/ftp/pub/axis/software/MPQT"

CACHE_DIR = AsyncPath("./.cache")


class Firmware:
    def __init__(self, axis_auth: str):
        self._client = AsyncClient(
            cookies={"axis_auth": axis_auth},
        )

    async def latest_ver(self, device: str) -> str:
        r = await self._client.get(f"{FIRMWARE_BASE}/{device}/latest/ver.txt")
        return r.text

    async def download(self, device: str, version: str, force=False) -> AsyncPath:
        _version = version.replace(".", "_")

        fw_name = f"{device}_{_version}.bin"

        fw_url = f"{FIRMWARE_BASE}/{device}/{_version}/{fw_name}"

        if not await CACHE_DIR.exists():
            await CACHE_DIR.mkdir()

        fw_file = CACHE_DIR.joinpath(fw_name)

        if await fw_file.exists() and not force:
            print("fw file exists, skipping download")

        else:
            print(f"Downloading {fw_url}")
            async with self._client.stream("GET", fw_url, follow_redirects=True) as r:
                r.raise_for_status()

                total_size = int(r.headers.get("content-length", 0))

                progress_bar = tqdm(
                    total=total_size, unit="B", unit_scale=True, unit_divisor=1024
                )

                async with aiofiles.open(fw_file, "wb") as f:
                    async for chunk in r.aiter_bytes(chunk_size=2048):
                        await f.write(chunk)
                        progress_bar.update(len(chunk))

                progress_bar.close()

        return fw_file
