"""
手动插入天星医疗第3页文章（从搜狗搜索结果浏览器抓取）
"""
import asyncio
import httpx

IPO_ID = 58
BASE = "http://localhost:8000"

articles = [
    {
        "blogger_name": "划水的姐夫",
        "title": "港股打新 天星医疗",
        "summary": "打新有风险，参与需谨慎。天星医疗是国产运动医学整体解决方案提供商，产品覆盖植入物等，运动医学国产第一股，基本面扎实。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091112&ver=6681&signature=2sNCfRlBHX3nUGt**IQF6IIfhbWYoP-Z5SIrlc5pfeWUMiVjOx9vmcLCeiLi44Dum4kQ-4gu2oOKaHo3uI6K5-qoid6CbxZu2NK6t1ScijhyLu-DrCXX73SSJrmItcwz&new=1",
    },
    {
        "blogger_name": "楼兰时代",
        "title": "港股打新｜天星医疗：国产运动医学一哥，从科创板折戟到港股闯关，值不值得打？",
        "summary": "天星医疗是国产运动医学的好公司：赛道优质、业绩高增、国产替代逻辑硬；但作为港股打新股，科创板折戟、创始人套现、估值偏高是瑕疵。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091173&ver=6681&signature=qpf*hhFZi0gtfPHn5T-hNQsHTNm2NzMINRP4LA-ggxAD9tw08z5RKLqaa7OwnWNA2pobOLPFPDdfrK4-xmvtUdJhHP5n5rJAoYkOpuj7dVwSGKve85rIPoWLymJC23Pn&new=1",
    },
    {
        "blogger_name": "量化Cris笔记",
        "title": "港股打新｜天星医疗：哈工大80后博士带队，运动医学龙头转战港股",
        "summary": "天星医疗基本面不差，收入利润都在涨，赛道也有逻辑，国产替代和出海都能讲。但行业集采压着，专利诉讼挂着，发行结构也只是一般。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=TaGju*r-HxsqxpScsm5NJwa0Tri1MGMIdIdNMAkphi3PXw3CZYMwadpXSNT7l7MuIchsisnxl*97L8IbltLt62Utz5cXGGvU7bwCJMCqafAT5CCt4fhvCgTrMk3x1iLG&new=1",
    },
    {
        "blogger_name": "致知智富",
        "title": "港股打新：天星医疗（1609.HK）港股新股分析",
        "summary": "今天起招股的天星医疗，是近期港股新股里比较少见的一只既有真实盈利、又带细分赛道成长逻辑的医疗器械项目，积极申购。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=B7JkIH3DNRTy7QeU8hohiRQuuAs-IO7U8VxT*028NcuOw6itHS5kjdKA*dh1QD5zVJ7OYcnxzhlmCBDu5f0owHEiEhx16qqJtACUUCGsDJJf9-PqvxeDB0UaL6*lrZy5&new=1",
    },
    {
        "blogger_name": "掘金兔子",
        "title": "港股打新｜天星医疗（1609.HK）今起招股！运动医学医疗器械龙头，入场费4975港元？！",
        "summary": "天星医疗（1609.HK）今起招股，运动医学黄金赛道，34.71%基石占比，入场费4975港元，无绿鞋，博弈属性中等。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=1B1YLmor3Gv9--eY-RKGV0fc1gWLZ02C3XxUyQMq9kfqiISU*8JvwC7XO9u8mO8kxV-zeh50pwOJHXODaoWXeGjvhz84NnzWMTl6yDfVoS8oiN56-oGUad-96ERpETRh&new=1",
    },
    {
        "blogger_name": "雪哥观澜",
        "title": "港股打新 | 天星医疗（01609.HK）:科创板被中金弃保！国产运动医学一哥，能否逆袭成妖？",
        "summary": "曦智资金释放后，要不要打天星医疗？一文扒透真相。国产第一，但估值显著高于港股骨科耗材赛道可比公司的平均水平。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=LvH*nOAKN-WDq1y-rmK*a7jOXtkyqYtMe2bpoHJcDegX5GuGWeKzH8dAHP8r1Sst2HHgLs5sgjwxNhEOzM2xupHwp77DZuMsa9Ljc-CWvJMoMR-TIZNFT-SA*bSymLEQ&new=1",
    },
    {
        "blogger_name": "港美A小院随笔",
        "title": "国产运动医学龙头赴港IPO，天星医疗打新深度分析：高增长赛道的稀缺性与估值博弈",
        "summary": "从赛道景气度、公司核心壁垒、财务三表深度拆解、行业竞争格局、估值合理性五大维度，全面拆解天星医疗的港股打新价值。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=Elhb2sDCy5smqJeuGPvsg1B1UaA2XDuUoR4cy9fabn*roLTXu3CUz9y1D*3udS4YbI8k2RxJKdTchyIDzIquTQIr9eh3vF8zOyg276ntkr0B0-tqqOiLGWr4Gb9bT4eN&new=1",
    },
    {
        "blogger_name": "玖安说新股",
        "title": "商海长研 价值洞察｜天星医疗打新评级：A",
        "summary": "天星医疗不是那种靠情绪硬炒的题材票，而是基本面、赛道属性和发行结构都具备一定支撑的A级申购标的。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=ECCH*ZZPevoVcXYgM9fOHaivF9Y4i*H0EuV1HsY-34LDDelrRD2xuMIgdt94444ln-IeAPMVqik7PuXEAVUR21PgTjM6O5UrPQFaXgVY81HTKyI6SPAbSnsx7OvBfgQ6&new=1",
    },
    {
        "blogger_name": "出海阿良",
        "title": "天星医疗（01609.HK）港股打新分析与申购策略",
        "summary": "综合点评与打新策略结论：可以申购。核心逻辑：天星医疗基本面清晰，利润表经受住了集采降价的考验，实现了营收与净利的同步高增。",
        "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1777091270&ver=6681&signature=aRkUQitiVOlp1MmVbouwdJpghTFCpiV1Cdnn7pzvpyhXfqG04xRudPBRkOlHdmsJIvGGtDroGkix8S8vwbbEuHiIAfom5hhzQzf7k4zNKBDrQmw3dk*OVnnzGmv-g3Ly&new=1",
    },
]


async def get_or_create_blogger(client: httpx.AsyncClient, name: str, cache: dict) -> int:
    if name in cache:
        return cache[name]
    resp = await client.get(f"{BASE}/bloggers/")
    for b in resp.json():
        if b["name"] == name:
            cache[name] = b["id"]
            return b["id"]
    resp = await client.post(f"{BASE}/bloggers/", json={
        "name": name,
        "channel": "wechat",
        "description": "由搜狗搜索自动发现",
    })
    if resp.status_code == 201:
        bid = resp.json()["id"]
        cache[name] = bid
        print(f"    创建新博主: {name} (id={bid})")
        return bid
    raise Exception(f"创建博主失败: {resp.text}")


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 获取已有文章
        resp = await client.get(f"{BASE}/ipos/{IPO_ID}")
        existing_urls = {a["content_url"] for a in resp.json().get("analyses", [])}
        print(f"当前已有 {len(existing_urls)} 篇文章")

        ok = skip = 0
        blogger_cache = {}

        for art in articles:
            if art["url"] in existing_urls:
                print(f"  ⏭️ 跳过(已存在): {art['title'][:40]}")
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
            print(f"  - [{a.get('blogger', {}).get('name', '?')}] {a['title'][:50]}")


asyncio.run(main())
