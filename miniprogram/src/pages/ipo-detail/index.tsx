import { useState, useEffect } from 'react'
import Taro, { useRouter } from '@tarojs/taro'
import { View, Text, ScrollView } from '@tarojs/components'
import { api } from '../../services/api'
import { IPOWithAnalyses, Analysis, Blogger } from '../../types'
import './index.scss'

const RECOMMENDATION_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  strong_buy: { label: '强烈推荐',  color: '#FFFFFF', bg: '#C8102E' },
  buy:        { label: '推荐认购',  color: '#00A870', bg: '#E8F8F0' },
  neutral:    { label: '中性',      color: '#FA8C16', bg: '#FFF3E0' },
  avoid:      { label: '建议回避',  color: '#666666', bg: '#F0F0F0' },
}

function formatDate(d?: string) {
  return d ? d.replace(/-/g, '/').slice(0, 10) : '—'
}

function RowItem({ label, value }: { label: string; value: string }) {
  return (
    <View className='row-item'>
      <Text className='row-label'>{label}</Text>
      <Text className='row-value'>{value}</Text>
    </View>
  )
}

function AnalysisCard({ item, onOpenArticle }: { item: Analysis; onOpenArticle: (id: number, url: string) => void }) {
  const rec = RECOMMENDATION_CONFIG[item.recommendation || '']
  const bloggerName = item.blogger?.name || '未知博主'
  return (
    <View className='analysis-card'>
      <View className='analysis-header'>
        <Text className='blogger-name'>{bloggerName}</Text>
        {rec && (
          <View className='rec-badge' style={{ backgroundColor: rec.bg }}>
            <Text className='rec-text' style={{ color: rec.color }}>{rec.label}</Text>
          </View>
        )}
      </View>
      {item.title && <Text className='analysis-title'>{item.title}</Text>}
      {item.summary && (
        <Text className='analysis-content' numberOfLines={3}>{item.summary}</Text>
      )}
      <View className='analysis-footer'>
        <Text className='analysis-date'>{formatDate(item.published_at || item.created_at)}</Text>
        {item.content_url && (
          <View className='read-btn' onClick={() => onOpenArticle(item.id, item.content_url!)}>
            <Text className='read-btn-text'>阅读原文 →</Text>
          </View>
        )}
      </View>
    </View>
  )
}

export default function IPODetailPage() {
  const router = useRouter()
  const ipoId = Number(router.params.id)
  const ipoName = decodeURIComponent(router.params.name || '')

  const [ipo, setIpo] = useState<IPOWithAnalyses | null>(null)
  const [bloggers, setBloggers] = useState<Blogger[]>([])
  const [selectedBlogger, setSelectedBlogger] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (ipoName) {
      Taro.setNavigationBarTitle({ title: ipoName })
    }
    Promise.all([
      api.getBloggers(),
    ]).then(([bs]) => {
      setBloggers(bs)
    })
  }, [])

  useEffect(() => {
    setLoading(true)
    api.getIPODetail(ipoId, selectedBlogger)
      .then(setIpo)
      .catch(() => Taro.showToast({ title: '加载失败', icon: 'none' }))
      .finally(() => setLoading(false))
  }, [ipoId, selectedBlogger])

  const openArticle = async (analysisId: number, url: string) => {
    // mp.weixin.qq.com 链接永久有效，直接打开
    if (url.includes('mp.weixin.qq.com')) {
      Taro.navigateTo({ url: `/pages/article/index?url=${encodeURIComponent(url)}` })
      return
    }
    // 搜狗链接可能已过期，先调后端刷新，拿到最新永久 URL 再打开
    Taro.showLoading({ title: '获取文章…' })
    try {
      const res = await api.refreshArticleUrl(analysisId)
      Taro.hideLoading()
      Taro.navigateTo({ url: `/pages/article/index?url=${encodeURIComponent(res.url)}` })
    } catch {
      Taro.hideLoading()
      // 刷新失败就直接用原链接兜底
      Taro.navigateTo({ url: `/pages/article/index?url=${encodeURIComponent(url)}` })
    }
  }

  if (loading || !ipo) {
    return (
      <View className='loading-page'>
        <Text className='loading-text'>加载中…</Text>
      </View>
    )
  }

  const priceText = ipo.ipo_price_min
    ? (ipo.ipo_price_min === ipo.ipo_price_max ? `HK$${ipo.ipo_price_min}` : `HK$${ipo.ipo_price_min}–${ipo.ipo_price_max}`)
    : '待公布'

  return (
    <ScrollView scrollY className='detail-page'>
      {/* 基本信息卡片 */}
      <View className='info-card'>
        <View className='info-header'>
          <Text className='info-stock-name'>{ipo.stock_name}</Text>
          <Text className='info-stock-code'>{ipo.exchange}:{ipo.stock_code}</Text>
          {ipo.industry && <Text className='info-industry'>{ipo.industry}</Text>}
        </View>

        <View className='divider' />

        <RowItem label='发行价格' value={priceText} />
        <RowItem label='每手股数' value={ipo.lot_size ? `${ipo.lot_size} 股` : '—'} />
        <RowItem label='认购开始' value={formatDate(ipo.subscribe_start)} />
        <RowItem label='认购截止' value={formatDate(ipo.subscribe_end)} />
        <RowItem label='公布结果' value={formatDate(ipo.allotment_date)} />
        <RowItem label='上市日期' value={formatDate(ipo.listing_date)} />
        {ipo.market_cap && <RowItem label='市值' value={ipo.market_cap} />}

        {ipo.description && (
          <>
            <View className='divider' />
            <Text className='description'>{ipo.description}</Text>
          </>
        )}
      </View>

      {/* 博主筛选 */}
      <View className='section-title-row'>
        <Text className='section-title'>博主分析</Text>
        <Text className='analysis-count'>{ipo.analyses.length} 篇</Text>
      </View>

      {bloggers.length > 0 && (
        <ScrollView scrollX className='blogger-filter' enableFlex>
          <View
            className={`blogger-chip ${!selectedBlogger ? 'blogger-chip--active' : ''}`}
            onClick={() => setSelectedBlogger(undefined)}
          >
            <Text className={`blogger-chip-text ${!selectedBlogger ? 'blogger-chip-text--active' : ''}`}>全部</Text>
          </View>
          {bloggers.map(b => (
            <View
              key={b.id}
              className={`blogger-chip ${selectedBlogger === b.id ? 'blogger-chip--active' : ''}`}
              onClick={() => setSelectedBlogger(b.id)}
            >
              <Text className={`blogger-chip-text ${selectedBlogger === b.id ? 'blogger-chip-text--active' : ''}`}>{b.name}</Text>
            </View>
          ))}
        </ScrollView>
      )}

      {/* 分析列表 */}
      <View className='analyses-list'>
        {ipo.analyses.length === 0 ? (
          <View className='no-analysis'>
            <Text className='no-analysis-text'>暂无博主分析</Text>
          </View>
        ) : (
          ipo.analyses.map(item => (
            <AnalysisCard key={item.id} item={item} onOpenArticle={(id, url) => openArticle(id, url)} />
          ))
        )}
        <View style={{ height: '40px' }} />
      </View>
    </ScrollView>
  )
}
