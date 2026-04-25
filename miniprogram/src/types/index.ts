export type IPOStatus = 'upcoming' | 'subscribing' | 'allotment' | 'listed' | 'withdrawn'

export interface IPO {
  id: number
  stock_code: string
  stock_name: string
  exchange: string
  industry?: string
  ipo_price_min?: string
  ipo_price_max?: string
  lot_size?: number
  subscribe_start?: string
  subscribe_end?: string
  allotment_date?: string
  listing_date?: string
  status: IPOStatus
  market_cap?: string
  description?: string
  data_source?: string
  analysis_count?: number
}

export interface Blogger {
  id: number
  name: string
  channel: string
  description?: string
  follower_count?: string
  avatar_url?: string
}

export interface Analysis {
  id: number
  ipo_id: number
  blogger_id: number
  blogger?: Blogger          // 后端嵌套对象
  title: string
  summary?: string           // 摘要（后端字段名）
  content_url?: string       // 文章链接（后端字段名）
  recommendation?: string
  published_at?: string
  created_at?: string
}

export interface IPOWithAnalyses extends IPO {
  analyses: Analysis[]
}
