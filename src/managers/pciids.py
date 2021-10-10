import re
import requests
import aiohttp


class PCIIDs:
    async def get_item(self, deviceID: str, ven: str = "any") -> str:
        content = requests.get(
            "https://pci-ids.ucw.cz/read/PC/{}/{}".format(ven, deviceID.upper()))

        data = await self.async_dl(content.url)

        if data:
            out = ""
            for line in data.decode().split('\n'):
                if 'name' in line.lower() and not 'itemname' in line.lower():
                    res = re.search(r'(?<=\<p\>)Name\:\s?.*(?=\<\/.+)', line)
                    if res:
                        out = res.group(0).split(':')[1].strip()
                        break
                elif 'itemname' in line.lower():
                    out = "Name: ".join(line.split("Name: ")[1:]).replace("&amp;","&").replace("&quot;",'"').replace("&apos;","'").replace("&gt;",">").replace("&lt;","<")

            if out:
                return out
            else:
                return None

    async def async_post_text(self, url, data=None, headers=None):
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=data) as response:
                res = await response.read()
                return res.decode("utf-8", "replace")

    async def async_dl(self, url, headers=None):
        total_size = 0
        data = b""
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                assert response.status == 200
                while True:
                    chunk = await response.content.read(4*1024)  # 4k
                    data += chunk
                    total_size += len(chunk)
                    if not chunk:
                        break
                    if total_size > 8000000:
                        # Too big...
                        return None
        return data

    async def async_text(self, url, headers=None):
        data = await self.async_dl(url, headers)
        if data != None:
            return data.decode("utf-8", "replace")
        else:
            return data
