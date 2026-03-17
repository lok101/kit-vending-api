import asyncio
import os

from kit_api import KitVendingAPIClient
from kit_api.client import KitAPIAccount


async def main(account: KitAPIAccount):
    async with KitVendingAPIClient(account=account) as client:
        res = await client.get_vending_machines()
        pass


if __name__ == "__main__":
    kit_account = KitAPIAccount(
        login=os.getenv("KIT_API_LOGIN"),
        password=os.getenv("KIT_API_PASSWORD"),
        company_id=int(os.getenv("KIT_API_COMPANY_ID")),
    )
    asyncio.run(main(kit_account))
