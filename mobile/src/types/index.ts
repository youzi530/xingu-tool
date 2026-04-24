export type IPOStatus = 'upcoming' | 'subscribing' | 'listing' | 'listed';
export type SourceChannel = 'wechat' | 'xhs' | 'broker' | 'other';
export type Recommendation = '积极' | '中性' | '谨慎';

export interface Blogger {
  id: number;
  name: string;
  channel: SourceChannel;
  wechat_id?: string;
  avatar_url?: string;
  description?: string;
  follower_count?: string;
}

export interface IPO {
  id: number;
  stock_code: string;
  stock_name: string;
  exchange: string;
  industry?: string;
  ipo_price_min?: string;
  ipo_price_max?: string;
  lot_size?: number;
  subscribe_start?: string;
  subscribe_end?: string;
  allotment_date?: string;   // 中签结果公布日（iTick）
  listing_date?: string;
  status: IPOStatus;
  market_cap?: string;       // 市值（iTick，如 "10.5B"）
  description?: string;
  data_source?: string;      // "manual" | "itick"
  analysis_count: number;
}

export interface Analysis {
  id: number;
  ipo_id: number;
  blogger_id: number;
  title: string;
  summary?: string;
  content_url?: string;
  cover_image_url?: string;
  source_channel: SourceChannel;
  published_at?: string;
  view_count: number;
  like_count: number;
  recommendation?: string;
  blogger?: Blogger;
}

export interface IPOWithAnalyses extends IPO {
  analyses: Analysis[];
}

export type RootStackParamList = {
  MainTabs: undefined;
  IPODetail: { ipoId: number; stockName: string };
  ArticleDetail: { url: string; title: string };
};
