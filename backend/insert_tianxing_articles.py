import asyncio
import httpx

IPO_ID = 58
BASE = "http://localhost:8000"

articles = [
    {
        "blogger_name": "珍兴资本",
        "title": "天星医疗港股打新分析，国产运动医学一哥，新股评级—火力试探！",
        "summary": "本周港股打新市场来了一只国产运动医学一哥——天星医疗(01609)，招股截止2026年4月29日中午，5月5日上市。基本面扎实，详细分析基石投资者、估值及申购策略，评级为火力试探。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=XJDye9aFnh0sjhNKr6mnLtHj*krpjPszi3emXAN5NUYX8UHKDXAeGaQrX-bxa8Zz7-yqHAjt3zoUoD9uaCOHX6qmCAqlCswGZSXCxCmIEK7N7Kld5jEI71Ci2lW6FPGq&new=1",
    },
    {
        "blogger_name": "每天打个新",
        "title": "【港股IPO】天星医疗申购情况及打新分析",
        "summary": "北京天星医疗股份有限公司(01609.HK)，机制B，10%，公配16844手。详细分析孖展情况、保荐人及估值。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=pBeEOHeASCbQw4jp4hRfV6lqo2pxoNRoqwcslF915RxYNIDuy*Pd7pQoE2GAgxdAJEH1oZIwQkx6EenSgMTGjOi*6ViOnu8T14aaiQ9FZ5HdGiOFnlU3T5zlX3XQTp1x&new=1",
    },
    {
        "blogger_name": "爱生活的懒懒",
        "title": "港股打新：天星医疗，运动医学设备的国产龙头",
        "summary": "天星医疗是中国运动医学设备领域的国产龙头，专注于运动医学植入物、手术设备及相关耗材。2025年毛利率74.1%，净利率34%，详细分析估值、募资用途及风险。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=onGo-DaeVz1N*SaxZsFy29OMSAUyXgdc5UIaSSr7xN5JWfDClBOd3vePE5SRemak0JHOKY61ZDwdJ2nHwKE1JOqToKxKWWTyJ*SSFtv-6vjzpje9rIL-3DiHaXNfBi5l&new=1",
    },
    {
        "blogger_name": "港盈记",
        "title": "【天星医疗】打新｜运动医学国产龙头，门槛约5,000港元",
        "summary": "天星医疗(1609.HK)，招股价98.50港元，入场费约4,975港元。运动医学国产龙头，基本面扎实、盈利高增长，估值偏贵(PE 33x)，无绿鞋无入通，建议小仓位参与。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=UDg5JwMUluVoHi8SOF8g3mEG2FrPJQQM1BFRxz7C0VPfzyRG0-tykLR4yAV5*2b*q4JRRltx50oBIhAvyRr1bd5g2lMQ7MSJ5zONA9XFUPkcL*5NWHtFs4TGWCSlApav&new=1",
    },
    {
        "blogger_name": "石喜",
        "title": "港股打新天星医疗，最大的国产运动医学植入物及器械提供商",
        "summary": "按2024年销售收入计，天星医疗是中国第四大运动医学植入物及器械提供商，也是最大的国产提供商。详细分析公司简介、发行情况及综合结论，建议梭哈。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=rh5s6jBAfBxb0ft9o1iQSTdPgAQCFGYxkRZHiky8TLZsj80FeP2wG2get3y1n0ZGxwV8uWSWzaukko1Lt1t5E4RcV2FPDOTIwY12UTJDEQGYeqVfPquGHGKWVSMkIi1j&new=1",
    },
    {
        "blogger_name": "大华在书桌前",
        "title": "天星医疗丨港股打新信息",
        "summary": "天星医疗(01609.HK)，2017年成立于北京，专注运动医学临床解决方案。分析公司简介、产品系列、业绩情况及招股信息。天星医疗属于小票手数少，炒的可能性比较大。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=zCCeOTn6YQ4l7sgi*YirjgUDB0HUiloFMlClhWHCQsfaJM1wlwCf*rqQdovI8zwTsmKcGmeh9kJaW-BlRzL3C6LPg11h4MdNHVCXaPLi4tNWqui-gy7goLGpgPV32WCW&new=1",
    },
    {
        "blogger_name": "俞生笔记",
        "title": "港股打新天星医疗：国产运动医学器械第一股，打新局中局？",
        "summary": "中签难、赚不多，打新性价比从发行端就被大幅压缩。分析发行档案、投资基本面、投机博弈面及估值合理性。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=JOdYM-p-qHeJ-CxbDYzkJbqDCIp14qwiw3eQhqvEwQjd3Z2K-T5KSAc1LrtYDugCi*HlxC23lDREIXs-5xsBdqUagL0X8kHxWE-bYt8-XJSfBABVrfuv25iu1SbnpDJ7&new=1",
    },
    {
        "blogger_name": "Kai的费曼学习",
        "title": "港股打新：天星医疗（运动医疗解决方案）",
        "summary": "天星医疗是H股首发，原来是中金保荐的科创板未能冲板成功，转战港交所，这次保荐人里面有中信证券。今年港股打新真的是大年，详细分析打新策略。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=7vMSeHzDeStJbjRFfGH5NWTtODe4uABf5nQHO5lxH4r4Fs9tSKuvTseF4p3bEbIhFSk4h-yjdPMKz9-C*7uo3VnCfQE5tzPY8qIkzIOguWwKOrgNh3sb*VIIXoUKtsFK&new=1",
    },
    {
        "blogger_name": "天威顺势而为",
        "title": "港股打新天星医疗申购分析",
        "summary": "港股打新根据历史经验，也不太会一直很好。天星医疗是一家专注运动医学临床解决方案的医疗器械公司，分析其打新价值及申购建议。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777089601&ver=6681&signature=2rAGtpWCFAibYZbSV0xdWtQV-xTmmChn1AhHvwrAJjO1saEOwCCTcllMUbEvRPxYC2pQw820UWdaWjMQZOdRqpbQQ9EF8CbvtDwbzlHcCIk5vCAZ0fs90JcDhYfiJA9n&new=1",
    },
]

async def get_or_create_blogger(client: httpx.AsyncClient, name: str, blogger_cache: dict) -> int:
    if name in blogger_cache:
        return blogger_cache[name]
    
    # get all bloggers
    resp = await client.get(f"{BASE}/bloggers/")
    bloggers = resp.json()
    for b in bloggers:
        if b["name"] == name:
            blogger_cache[name] = b["id"]
            return b["id"]
    
    # create new blogger
    resp = await client.post(f"{BASE}/bloggers/", json={
        "name": name,
        "channel": "wechat",
        "description": "由搜狗搜索自动发现",
    })
    if resp.status_code == 201:
        bid = resp.json()["id"]
        blogger_cache[name] = bid
        print(f"    创建新博主: {name} (id={bid})")
        return bid
    else:
        raise Exception(f"创建博主失败: {resp.text}")


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BASE}/ipos/{IPO_ID}")
        existing = resp.json()
        existing_titles = {a["title"] for a in existing.get("analyses", [])}
        print(f"当前已有 {len(existing_titles)} 篇文章")
        
        blogger_cache = {}
        ok = 0
        skip = 0
        for art in articles:
            if art["title"] in existing_titles:
                print(f"  跳过（已存在）: {art['title'][:45]}")
                skip += 1
                continue
            
            blogger_id = await get_or_create_blogger(client, art["blogger_name"], blogger_cache)
            
            payload = {
                "ipo_id": IPO_ID,
                "blogger_id": blogger_id,
                "title": art["title"],
                "summary": art["summary"],
                "content_url": art["url"],
                "source_channel": "wechat",
            }
            r = await client.post(f"{BASE}/analyses/", json=payload)
            if r.status_code in (200, 201):
                print(f"  ✅ 已插入: [{art['blogger_name']}] {art['title'][:40]}")
                ok += 1
            else:
                print(f"  ❌ 失败({r.status_code}): {r.text[:150]}")
        
        print(f"\n完成: 新增 {ok} 篇，跳过 {skip} 篇")
        
        resp2 = await client.get(f"{BASE}/ipos/{IPO_ID}")
        d = resp2.json()
        print(f"天星医疗现共 {len(d.get('analyses', []))} 篇分析文章")
        for a in d.get("analyses", []):
            print(f"  - [{a.get('blogger',{}).get('name','?')}] {a['title'][:50]}")

asyncio.run(main())
