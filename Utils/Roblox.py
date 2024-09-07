from roblox import Client
import aiohttp

client = Client()


async def RobloxThumbnail(UserID: int) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://thumbnails.roblox.com/v1/users/avatar?userIds={UserID}&size=420x420&format=png&isCircular=false"
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data and "data" in data:
                    return data["data"][0].get("imageUrl")
            return None
