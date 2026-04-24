import { IPO, IPOWithAnalyses, Blogger, Analysis } from '../types';

// 优先使用环境变量中的 API URL
// 本地开发：改成你电脑的局域网 IP；部署后改成 Render 域名
const BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ||
  'http://192.168.10.199:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${path}`);
  }
  return res.json();
}

export const api = {
  // ── IPO ────────────────────────────────────────────────────────────────
  getIPOs: (status?: string): Promise<IPO[]> => {
    const qs = status ? `?status=${status}` : '';
    return request<IPO[]>(`/ipos/${qs}`);
  },

  getIPODetail: (ipoId: number, bloggerId?: number): Promise<IPOWithAnalyses> => {
    const qs = bloggerId ? `?blogger_id=${bloggerId}` : '';
    return request<IPOWithAnalyses>(`/ipos/${ipoId}${qs}`);
  },

  // ── Bloggers ───────────────────────────────────────────────────────────
  getBloggers: (): Promise<Blogger[]> => {
    return request<Blogger[]>('/bloggers/');
  },

  // ── Analyses ───────────────────────────────────────────────────────────
  getAnalyses: (params?: { ipo_id?: number; blogger_id?: number }): Promise<Analysis[]> => {
    const qs = new URLSearchParams();
    if (params?.ipo_id) qs.set('ipo_id', String(params.ipo_id));
    if (params?.blogger_id) qs.set('blogger_id', String(params.blogger_id));
    const q = qs.toString() ? `?${qs.toString()}` : '';
    return request<Analysis[]>(`/analyses/${q}`);
  },
};

// 离线 Mock 数据（后端不可用时使用）
export const MOCK_BLOGGERS: Blogger[] = [
  { id: 1, name: '量化雨叔', channel: 'wechat', description: '专注港股打新量化分析，数据驱动。', follower_count: '12万+' },
  { id: 2, name: '我爱广州GZ', channel: 'wechat', description: '港股打新老韭菜，分享认购策略与上市套路。', follower_count: '8万+' },
  { id: 3, name: '港股打新日记', channel: 'wechat', description: '记录每只新股的认购过程与盈亏情况。', follower_count: '5万+' },
  { id: 4, name: '新股研究所', channel: 'wechat', description: '深度解析新股基本面，行业对比，估值分析。', follower_count: '15万+' },
];

export const MOCK_IPOS: IPO[] = [
  {
    id: 3, stock_code: '6969', stock_name: '泡泡玛特', exchange: 'HKEX',
    industry: '潮玩零售', ipo_price_min: '38.50', ipo_price_max: '40.00',
    lot_size: 100, subscribe_start: '2025-04-14', subscribe_end: '2025-04-18',
    listing_date: '2025-04-24', status: 'subscribing',
    description: '中国领先的潮流玩具品牌，旗下 MOLLY、LABUBU 等 IP 在全球拥有大量粉丝。',
    analysis_count: 4,
  },
  {
    id: 4, stock_code: '1717', stock_name: '星巴克中国', exchange: 'HKEX',
    industry: '餐饮消费', ipo_price_min: '15.80', ipo_price_max: '18.00',
    lot_size: 200, subscribe_start: '2025-05-05', subscribe_end: '2025-05-09',
    listing_date: '2025-05-14', status: 'upcoming',
    description: '星巴克中国业务分拆上市，覆盖全国6000+门店，独立运营中国市场。',
    analysis_count: 2,
  },
  {
    id: 5, stock_code: '2333', stock_name: '长安汽车H股', exchange: 'HKEX',
    industry: '汽车制造', ipo_price_min: '6.50', ipo_price_max: '7.80',
    lot_size: 500, subscribe_start: '2025-05-19', subscribe_end: '2025-05-23',
    listing_date: '2025-05-28', status: 'upcoming',
    description: '重庆长安汽车港股 H 股上市，旗下深蓝、阿维塔等新能源品牌增速亮眼。',
    analysis_count: 2,
  },
  {
    id: 2, stock_code: '2382', stock_name: '舜宇光学科技', exchange: 'HKEX',
    industry: '精密光学', ipo_price_min: '78.50', ipo_price_max: '82.00',
    lot_size: 100, subscribe_start: '2025-01-06', subscribe_end: '2025-01-10',
    listing_date: '2025-01-16', status: 'listed',
    description: '全球领先的光学零件及产品制造商，主要产品包括手机镜头、车载镜头。',
    analysis_count: 0,
  },
];
