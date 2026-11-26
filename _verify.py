import asyncio, json, os
from playwright.async_api import async_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/data/tools/.pw-browsers"
URL = "http://localhost:8901/index.html"

async def check():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width":1440,"height":900})
        pg = await ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        pg.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type=="error" else None)
        await pg.goto(URL, wait_until="load", timeout=60000)
        await pg.wait_for_timeout(3500)

        out = await pg.evaluate("""() => {
          const rs = [document.getElementById('vid-left').readyState,
                      document.getElementById('vid-right').readyState];
          const dl = getComputedStyle(document.getElementById('vid-left')).display;
          const dr = getComputedStyle(document.getElementById('vid-right')).display;
          const sl = document.getElementById('vid-left').src;
          const sr = document.getElementById('vid-right').src;
          const bg = getComputedStyle(document.body).backgroundColor;
          const rise = document.querySelectorAll('[data-rise]');
          const animStates = Array.from(document.querySelectorAll('[data-rise]'))
            .map(e=>e.style.animation);
          const over = getComputedStyle(document.getElementById('overlay-layer')).mixBlendMode;
          const curs = getComputedStyle(document.getElementById('prmpt-cursor')).display;
          const accent = getComputedStyle(document.getElementById('accent-layer')).height;
          return {
            title: document.title,
            lang: document.documentElement.lang,
            readyStates: rs,
            displayLeft: dl, displayRight: dr,
            srcLeft: sl, srcRight: sr,
            bodyBg: bg, canvasOpacity: getComputedStyle(document.getElementById('main-canvas')).opacity,
            riseCount: rise.length, animStates: animStates,
            rootOverflow: getComputedStyle(document.documentElement).overflow,
            bodyOverflow: getComputedStyle(document.body).overflow,
            bodyScrollH: document.body.scrollHeight, winH: window.innerHeight,
            bodyScrollW: document.body.scrollWidth, winW: window.innerWidth,
            overlayBlend: over, cursorDisplay: curs, accentHeight: accent,
            logoColor: getComputedStyle(document.querySelector('.logo')).color,
            navOffset: getComputedStyle(document.querySelector('.nav')).right,
            wordmarkVisible: !!document.querySelector('.logo').offsetParent,
            introText: document.querySelector('.intro').textContent.slice(0,40),
            captionTitle: document.querySelector('.caption-title').textContent.replace(/\\n/g,' '),
            badge: document.querySelector('.caption-badge span').textContent,
            ariaCart: document.querySelector('button[aria-label="Open cart"]').outerHTML.slice(0,60),
            ariaMenuExpanded: document.querySelector('button[aria-label="Open menu"]').getAttribute('aria-expanded'),
          };
        }""")

        # pointer scrub test: move to far left, wait, check a video display + seek activity
        bbox = await pg.evaluate("""() => {
          const v=document.getElementById('vid-left');
          return {dur:v.duration, builtins:[v.loop,v.autoplay,v.muted]} ;
        }""")
        await pg.mouse.move(10, 450)
        await pg.wait_for_timeout(1200)
        scrub = await pg.evaluate("""() => {
          const l=document.getElementById('vid-left'), r=document.getElementById('vid-right');
          return {disL:getComputedStyle(l).display, disR:getComputedStyle(r).display,
                  curL:l.currentTime, durL:l.duration, curR:r.currentTime, durR:r.duration,
                  cursOp:getComputedStyle(document.getElementById('prmpt-cursor')).opacity};
        }""")
        # far right
        await pg.mouse.move(1430, 450)
        await pg.wait_for_timeout(1200)
        scrubR = await pg.evaluate("""() => {
          const l=document.getElementById('vid-left'), r=document.getElementById('vid-right');
          return {disL:getComputedStyle(l).display, disR:getComputedStyle(r).display,
                  cursOp:getComputedStyle(document.getElementById('prmpt-cursor')).opacity};
        }""")
        # over wordmark -> cursor hides, system cursor auto
        await pg.mouse.move(120, 120)
        await pg.wait_for_timeout(300)
        hit = await pg.evaluate("""() => {
          const c=getComputedStyle(document.getElementById('prmpt-cursor')).opacity;
          const s=document.getElementById('stage').style.cursor;
          return {cursorOp:c, stageCursor:s};
        }""")
        # src unchanged check
        src_after = await pg.evaluate("""() => [document.getElementById('vid-left').src,
                                               document.getElementById('vid-right').src]""")

        await b.close()
        return json.dumps({"out":out,"bbox":bbox,"scrub":scrub,"scrubR":scrubR,"hit":hit,
                           "src_after":src_after,"errors":errors}, indent=2)

result = asyncio.run(check())
print(result)