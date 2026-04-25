# 新股通 — 港股打新分析聚合 App

> 为港股打新投资者而生，将各大博主针对新股的分析文章一站式聚合展示。

## 项目结构

```
xingu-tool/
├── backend/          # Python FastAPI 后端 API
│   ├── main.py       # 入口，路由注册
│   ├── models.py     # SQLAlchemy 数据模型
│   ├── schemas.py    # Pydantic 请求/响应 schema
│   ├── database.py   # SQLite 数据库连接
│   ├── routes/       # 路由模块（ipos / bloggers / analyses）
│   ├── seed_data.py  # 种子数据（博主 + 新股 + 示例分析）
│   └── requirements.txt
└── mobile/           # Expo React Native 移动端
    ├── App.tsx        # 导航根组件
    ├── src/
    │   ├── screens/  # 页面组件
    │   │   ├── IPOListScreen.tsx      # 新股列表
    │   │   ├── IPODetailScreen.tsx    # 新股详情 + 分析列表
    │   │   ├── ArticleDetailScreen.tsx# 文章阅读（WebView）
    │   │   └── BloggersScreen.tsx     # 博主介绍
    │   ├── components/               # 通用 UI 组件
    │   │   ├── IPOCard.tsx
    │   │   ├── AnalysisCard.tsx
    │   │   ├── BloggerFilterBar.tsx
    │   │   ├── IPOStatusBadge.tsx
    │   │   ├── RecommendationTag.tsx
    │   │   └── BloggerAvatar.tsx
    │   ├── services/api.ts           # API 请求封装 + Mock 数据
    │   ├── types/index.ts            # TypeScript 类型定义
    │   └── theme/index.ts            # 设计 Token（颜色/间距/字体）
    └── app.json
```

## 数据模型

| 实体 | 说明 |
|------|------|
| **IPO** | 新股信息：代码、名称、发行价区间、认购期、上市日、状态 |
| **Blogger** | 博主信息：名称、渠道（公众号/小红书/券商）、粉丝数 |
| **Analysis** | 分析文章：标题、摘要、原文链接、发布时间、推荐结论（积极/中性/谨慎） |

## 快速启动

### 后端

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 配置 iTick Token（在 https://itick.org 注册后获取）
cp .env.example .env
# 编辑 .env，将 ITICK_TOKEN=your_itick_token_here 改为真实 Token

python seed_data.py          # 初始化示例数据（可选）
uvicorn main:app --reload --host 0.0.0.0 --port 8000    # 启动在 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

**启动后自动行为：**
- 服务启动 5 秒后自动从 iTick 拉取一次港股新股数据
- 此后每 6 小时自动同步一次（可在 `.env` 调整 `SYNC_INTERVAL_SECONDS`）
- 也可手动触发：`POST http://localhost:8000/sync/ipos`
- 查看同步状态：`GET http://localhost:8000/sync/status`

### 移动端

```bash
cd mobile
npm install
npm start                    # 启动 Expo Dev Server
npx expo start --clear
# 用 Expo Go App 扫码即可在手机上预览
```

> **开发时**：后端 URL 写死在 `src/services/api.ts` 的 `BASE_URL`，
> 需要改为你本机 IP（如 `http://192.168.1.x:8000`）才能在真机上访问。

## V1 功能清单

- [x] **新股列表**：按状态（认购中 / 即将认购 / 即将上市 / 已上市）筛选
- [x] **新股详情**：发行价、每手股数、认购截止日、上市日、公司简介
- [x] **博主分析**：展示各博主针对该新股的分析文章卡片
- [x] **博主筛选**：横向 Tab 筛选指定博主文章
- [x] **推荐结论**：绿色（积极）/ 橙色（中性）/ 红色（谨慎）标签
- [x] **WebView 阅读**：内嵌浏览器打开原文，支持跳外部浏览器
- [x] **博主列表**：所有博主介绍、粉丝数、渠道来源
- [x] **离线 Mock**：后端未启动时自动降级到 Mock 数据

## V2 规划

- [ ] 小红书、券商 App 渠道接入
- [ ] 博主关注 / 新股收藏
- [ ] 新股打分排行榜（综合多博主推荐）
- [ ] Push 通知：新股开始认购提醒
- [ ] 历史胜率统计（博主推荐准确率）

## 博主列表（V1）

| 博主 | 渠道 | 粉丝数 | 风格 |
|------|------|--------|------|
| 量化雨叔 | 微信公众号 | 12万+ | 量化打分，数据驱动 |
| 我爱广州GZ | 微信公众号 | 8万+ | 认购策略，券商比较 |
| 港股打新日记 | 微信公众号 | 5万+ | 实战记录，盈亏公开 |
| 新股研究所 | 微信公众号 | 15万+ | 深度研究，基本面估值 |
