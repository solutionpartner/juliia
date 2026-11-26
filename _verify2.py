import asyncio, json, os
from playwright.async_api import async_playwright
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/data/tools/.pw-browsers"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width":1440,"height":900})
        pg = await ctx.new_page()
        await pg.goto("http://localhost:8901/index.html", wait_until="domcontentloaded", timeout=60000)
        # poll readyState for up to 20s
        for i in range(20):
            s = await pg.evaluate("""() => {
              const l=document.getElementById('vid-left'), r=document.getElementById('vid-right');
              return [l.readyState, r.readyState, l.networkState, r.networkState];
            }""")
            print(f"t+{i+1}s readyState L/R={s[0],s[1]} netState L/R={s[2],s[3]}", flush=True)
            if s[0]>=2 and s[1]>=2:
                break
            await pg.wait_for_timeout(1000)
        await b.close()

asyncio.run(main())