import os
import asyncio
import argparse

import aiofiles
from httpx import DigestAuth
from aiopath import AsyncPath

from axis_companionless import Camera, Firmware


AXIS_AUTH = os.environ.get("AXIS_AUTH")


async def upgrade(ip: str, auth: DigestAuth):
    print(f"Connecting to {ip}")

    camera = Camera(ip, auth)

    params = await camera.param_list()

    device = params.Brand.ProdShortName
    version = params.Properties.Firmware.Version

    print(device)
    print(f"Current fw version: {version}")

    fw = Firmware(AXIS_AUTH)

    _device = device.replace("AXIS ", "").replace(" ", "_")

    latest_version = await fw.latest_ver(_device)

    print(f"latest fw version: {latest_version}")

    version_parts = [int(part) for part in version.split(".")]
    latest_version_parts = [int(part) for part in latest_version.split(".")]

    if not version_parts < latest_version_parts:
        print("fw is up to date")
        return

    fw_file = await fw.download(_device, latest_version)

    print(f"Uploading: {fw_file}")

    await camera.fwpugrade(fw_file)


async def setparams(ip: str, file: str, auth: DigestAuth):
    path = AsyncPath(file)

    camera = Camera(ip, auth)

    async with aiofiles.open(path, "rb") as f:
        data = await f.read()

    params = dict(x.split("=", 1) for x in data.decode().strip().split("\n"))

    await camera.setparams(params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AXIS Companionless.")

    parser.add_argument("-u", "--username", type=str, help="Username", default="root")
    parser.add_argument("-p", "--password", type=str, help="Password", default="pass")

    subparsers = parser.add_subparsers(dest="command")

    # upgrade
    parser_upgrade = subparsers.add_parser(
        "upgrade", help="Upgrade the camera at the given IP"
    )
    parser_upgrade.add_argument("ip", type=str, help="The IP address of the camera")

    # setparams
    parser_apply = subparsers.add_parser(
        "setparams", help="Apply the given configuration file"
    )
    parser_apply.add_argument("ip", type=str, help="The IP address of the camera")
    parser_apply.add_argument(
        "-f", "--file", type=str, required=True, help="Path to the configuration file"
    )

    args = parser.parse_args()

    loop = asyncio.new_event_loop()

    auth = DigestAuth(args.username, args.password)

    if args.command == "upgrade":
        loop.run_until_complete(upgrade(args.ip, auth))
    elif args.command == "setparams":
        loop.run_until_complete(setparams(args.ip, args.file, auth))
    else:
        parser.print_help()
