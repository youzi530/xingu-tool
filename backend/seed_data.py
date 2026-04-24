"""
初始化种子数据：博主 + 示例新股 + 示例分析文章
运行：python seed_data.py
"""
from datetime import date, datetime
from database import engine, SessionLocal, Base
import models

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def seed():
    if db.query(models.Blogger).count() > 0:
        print("数据已存在，跳过 seed。")
        return

    # ── 博主 ────────────────────────────────────────────────────────────────
    bloggers = [
        models.Blogger(
            name="量化雨叔",
            channel=models.SourceChannel.wechat,
            wechat_id="quant_yushu",
            description="专注港股打新量化分析，数据驱动，每只新股出详细评分报告。",
            follower_count="12万+",
        ),
        models.Blogger(
            name="我爱广州GZ",
            channel=models.SourceChannel.wechat,
            wechat_id="ilove_gz_hkipo",
            description="港股打新老韭菜，分享认购策略与上市首日套路。",
            follower_count="8万+",
        ),
        models.Blogger(
            name="港股打新日记",
            channel=models.SourceChannel.wechat,
            wechat_id="hkipo_diary",
            description="记录每只新股的认购过程与盈亏情况，真实收益公开。",
            follower_count="5万+",
        ),
        models.Blogger(
            name="新股研究所",
            channel=models.SourceChannel.wechat,
            wechat_id="ipo_research_hk",
            description="深度解析新股基本面，行业对比，估值分析。",
            follower_count="15万+",
        ),
    ]
    db.add_all(bloggers)
    db.commit()
    for b in bloggers:
        db.refresh(b)

    # ── 新股 ────────────────────────────────────────────────────────────────
    ipos = [
        models.IPO(
            stock_code="9888",
            stock_name="百度集团",
            exchange="HKEX",
            industry="互联网科技",
            ipo_price_min="252.00",
            ipo_price_max="252.00",
            lot_size=10,
            subscribe_start=date(2024, 3, 18),
            subscribe_end=date(2024, 3, 22),
            listing_date=date(2024, 3, 26),
            status=models.IPOStatus.listed,
            description="百度是全球最大中文搜索引擎，旗下拥有文心一言AI大模型、Apollo自动驾驶等业务。",
        ),
        models.IPO(
            stock_code="2382",
            stock_name="舜宇光学科技",
            exchange="HKEX",
            industry="精密光学",
            ipo_price_min="78.50",
            ipo_price_max="82.00",
            lot_size=100,
            subscribe_start=date(2025, 1, 6),
            subscribe_end=date(2025, 1, 10),
            listing_date=date(2025, 1, 16),
            status=models.IPOStatus.listed,
            description="全球领先的光学零件及产品制造商，主要产品包括手机镜头、车载镜头、VR/AR光学模组。",
        ),
        models.IPO(
            stock_code="6969",
            stock_name="泡泡玛特",
            exchange="HKEX",
            industry="潮玩零售",
            ipo_price_min="38.50",
            ipo_price_max="40.00",
            lot_size=100,
            subscribe_start=date(2025, 4, 14),
            subscribe_end=date(2025, 4, 18),
            listing_date=date(2025, 4, 24),
            status=models.IPOStatus.subscribing,
            description="中国领先的潮流玩具品牌，旗下 MOLLY、LABUBU 等 IP 在全球拥有大量粉丝。",
        ),
        models.IPO(
            stock_code="1717",
            stock_name="星巴克中国",
            exchange="HKEX",
            industry="餐饮消费",
            ipo_price_min="15.80",
            ipo_price_max="18.00",
            lot_size=200,
            subscribe_start=date(2025, 5, 5),
            subscribe_end=date(2025, 5, 9),
            listing_date=date(2025, 5, 14),
            status=models.IPOStatus.upcoming,
            description="星巴克中国业务分拆上市，覆盖全国6000+门店，独立运营中国市场。",
        ),
        models.IPO(
            stock_code="2333",
            stock_name="长安汽车H股",
            exchange="HKEX",
            industry="汽车制造",
            ipo_price_min="6.50",
            ipo_price_max="7.80",
            lot_size=500,
            subscribe_start=date(2025, 5, 19),
            subscribe_end=date(2025, 5, 23),
            listing_date=date(2025, 5, 28),
            status=models.IPOStatus.upcoming,
            description="重庆长安汽车港股 H 股上市，旗下深蓝、阿维塔等新能源品牌增速亮眼。",
        ),
    ]
    db.add_all(ipos)
    db.commit()
    for i in ipos:
        db.refresh(i)

    # ── 分析文章 ─────────────────────────────────────────────────────────────
    yushu = bloggers[0]
    gz = bloggers[1]
    diary = bloggers[2]
    research = bloggers[3]

    popmart = ipos[2]   # 泡泡玛特
    starbucks = ipos[3] # 星巴克中国
    changan = ipos[4]   # 长安汽车

    analyses = [
        # 泡泡玛特 - 量化雨叔
        models.Analysis(
            ipo_id=popmart.id,
            blogger_id=yushu.id,
            title="【量化打分】泡泡玛特港股新股：LABUBU带飞估值，认购价值几何？",
            summary="从量化角度分析泡泡玛特此次 IPO，PE 约 35x 对比同类潮玩公司略贵，但 LABUBU 出海逻辑强劲，IP 扩张速度超预期。综合打分 82/100，建议积极参与。",
            content_url="https://mp.weixin.qq.com/s/example_popmart_yushu",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 4, 12, 10, 30),
            view_count=48200,
            like_count=2341,
            recommendation="积极",
        ),
        # 泡泡玛特 - 我爱广州GZ
        models.Analysis(
            ipo_id=popmart.id,
            blogger_id=gz.id,
            title="泡泡玛特打新攻略：孖展杠杆选哪家券商最划算？",
            summary="详细对比富途、老虎、华泰国际、中信里昂孖展利率和保证金比例。当前热度预测超购 500 倍，一手中签率约 20%，建议中资大行孖展博稳，预计首日弹 15%-25%。",
            content_url="https://mp.weixin.qq.com/s/example_popmart_gz",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 4, 13, 20, 15),
            view_count=35600,
            like_count=1876,
            recommendation="积极",
        ),
        # 泡泡玛特 - 港股打新日记
        models.Analysis(
            ipo_id=popmart.id,
            blogger_id=diary.id,
            title="打新日记 | 我为什么重仓申请泡泡玛特10手",
            summary="从个人持仓角度分享为何对泡泡玛特下重注：海外收入占比超 40%、IP 授权模式轻资产、管理层执行力强。风险点：消费品牌估值受情绪影响大，破发概率约 15%。",
            content_url="https://mp.weixin.qq.com/s/example_popmart_diary",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 4, 14, 8, 0),
            view_count=22100,
            like_count=1203,
            recommendation="积极",
        ),
        # 泡泡玛特 - 新股研究所
        models.Analysis(
            ipo_id=popmart.id,
            blogger_id=research.id,
            title="泡泡玛特深度报告：潮玩第一股的全球化路径与估值锚定",
            summary="从基本面拆解泡泡玛特业务：国内营收增速放缓（+18% YoY），海外高增长（+112% YoY）成为核心驱动力。以 DCF 模型测算合理价值区间 36-44 港元，发行价处于合理中枢。",
            content_url="https://mp.weixin.qq.com/s/example_popmart_research",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 4, 11, 14, 0),
            view_count=61400,
            like_count=3892,
            recommendation="中性",
        ),
        # 星巴克中国 - 量化雨叔
        models.Analysis(
            ipo_id=starbucks.id,
            blogger_id=yushu.id,
            title="【量化打分】星巴克中国拆分上市：分割价值还是估值陷阱？",
            summary="星巴克中国独立 IPO，当前门店超 6000 家但同店销售增速转负（-3% YoY）。对比瑞幸、霸王茶姬竞争压力大，量化综合评分 61/100，建议保守参与或观望。",
            content_url="https://mp.weixin.qq.com/s/example_starbucks_yushu",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 5, 2, 10, 0),
            view_count=39800,
            like_count=1654,
            recommendation="谨慎",
        ),
        # 星巴克中国 - 新股研究所
        models.Analysis(
            ipo_id=starbucks.id,
            blogger_id=research.id,
            title="星巴克中国 IPO 研究：消费降级背景下的品牌溢价能否延续？",
            summary="深度分析星巴克中国的竞争格局变化：瑞幸以价格战蚕食中端市场，茶饮赛道崛起分流用户。但星巴克品牌心智、第三空间定位仍具差异化，中长期价值可期。建议理性参与。",
            content_url="https://mp.weixin.qq.com/s/example_starbucks_research",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 5, 1, 15, 30),
            view_count=55200,
            like_count=2780,
            recommendation="中性",
        ),
        # 长安汽车 - 我爱广州GZ
        models.Analysis(
            ipo_id=changan.id,
            blogger_id=gz.id,
            title="长安汽车H股打新：新能源转型加速，AH股折价是机会吗？",
            summary="长安A股对应H股折价约 18%，历史上 A/H 折价收窄往往发生在港股上市初期。深蓝 S07 爆款验证了长安新能源产品力，建议积极认购，目标首日涨幅 10%-20%。",
            content_url="https://mp.weixin.qq.com/s/example_changan_gz",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 5, 16, 21, 0),
            view_count=28700,
            like_count=1432,
            recommendation="积极",
        ),
        # 长安汽车 - 量化雨叔
        models.Analysis(
            ipo_id=changan.id,
            blogger_id=yushu.id,
            title="【量化打分】长安汽车H股：传统车企新能源转型的估值重构",
            summary="对标比亚迪、吉利、长城 H 股估值体系，长安当前定价 PB 仅 0.9x，处于历史低位。新能源渗透率超 35% 后盈利拐点可期，量化评分 75/100，建议适量参与。",
            content_url="https://mp.weixin.qq.com/s/example_changan_yushu",
            source_channel=models.SourceChannel.wechat,
            published_at=datetime(2025, 5, 15, 9, 30),
            view_count=31500,
            like_count=1678,
            recommendation="积极",
        ),
    ]
    db.add_all(analyses)
    db.commit()
    print(f"✅ 种子数据写入完成：{len(bloggers)} 位博主，{len(ipos)} 只新股，{len(analyses)} 篇分析。")


if __name__ == "__main__":
    seed()
    db.close()
