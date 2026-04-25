import { useState, useEffect } from 'react'
import Taro from '@tarojs/taro'
import { View, Text, ScrollView } from '@tarojs/components'
import { api } from '../../services/api'
import { IPO, IPOStatus } from '../../types'
import './index.scss'

const STATUS_TABS: { key: string; label: string }[] = [
  { key: '', label: '全部' },
  { key: 'subscribing', label: '认购中' },
  { key: 'upcoming', label: '即将认购' },
  { key: 'allotment', label: '公布结果' },
  { key: 'listed', label: '已上市' },
]

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  upcoming:    { label: '即将认购', color: '#1677FF', bg: '#E8F3FF' },
  subscribing: { label: '认购中',   color: '#00A870', bg: '#E8F8F0' },
  allotment:   { label: '公布结果', color: '#FA8C16', bg: '#FFF3E0' },
  listed:      { label: '已上市',   color: '#666666', bg: '#F0F0F0' },
  withdrawn:   { label: '已撤回',   color: '#C8102E', bg: '#FFF0F0' },
}

function formatDate(dateStr?: string) {
  if (!dateStr) return '—'
  return dateStr.replace(/-/g, '/').slice(0, 10)
}

function formatPrice(min?: string, max?: string) {
  if (!min && !max) return '待公布'
  if (min === max || !max) return `HK$${min}`
  return `HK$${min}–${max}`
}

export default function IndexPage() {
  const [ipos, setIpos] = useState<IPO[]>([])
  const [activeTab, setActiveTab] = useState('')
  const [loading, setLoading] = useState(true)

  const loadIPOs = async (status: string) => {
    setLoading(true)
    try {
      const data = await api.getIPOs(status || undefined)
      setIpos(data)
    } catch (e) {
      Taro.showToast({ title: '加载失败，请检查网络', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadIPOs(activeTab)
  }, [activeTab])

  const goDetail = (ipo: IPO) => {
    Taro.navigateTo({ url: `/pages/ipo-detail/index?id=${ipo.id}&name=${encodeURIComponent(ipo.stock_name)}` })
  }

  const statusConf = (status: IPOStatus) => STATUS_CONFIG[status] || STATUS_CONFIG.listed

  return (
    <View className='page'>
      {/* 状态筛选 Tab */}
      <ScrollView className='tab-bar' scrollX enableFlex>
        {STATUS_TABS.map(tab => (
          <View
            key={tab.key}
            className={`tab-item ${activeTab === tab.key ? 'tab-item--active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <Text className={`tab-text ${activeTab === tab.key ? 'tab-text--active' : ''}`}>{tab.label}</Text>
          </View>
        ))}
      </ScrollView>

      {/* 列表 */}
      <ScrollView className='list' scrollY>
        {loading ? (
          <View className='empty'><Text className='empty-text'>加载中…</Text></View>
        ) : ipos.length === 0 ? (
          <View className='empty'><Text className='empty-text'>暂无新股数据</Text></View>
        ) : (
          ipos.map(ipo => {
            const conf = statusConf(ipo.status)
            return (
              <View key={ipo.id} className='card' onClick={() => goDetail(ipo)}>
                <View className='card-header'>
                  <View className='card-title-group'>
                    <Text className='stock-name'>{ipo.stock_name}</Text>
                    <Text className='stock-code'>{ipo.exchange}:{ipo.stock_code}</Text>
                  </View>
                  <View className='status-badge' style={{ backgroundColor: conf.bg }}>
                    <Text className='status-text' style={{ color: conf.color }}>{conf.label}</Text>
                  </View>
                </View>

                {ipo.industry && (
                  <Text className='industry'>{ipo.industry}</Text>
                )}

                <View className='card-row'>
                  <View className='info-item'>
                    <Text className='info-label'>发行价</Text>
                    <Text className='info-value'>{formatPrice(ipo.ipo_price_min, ipo.ipo_price_max)}</Text>
                  </View>
                  <View className='info-item'>
                    <Text className='info-label'>每手股数</Text>
                    <Text className='info-value'>{ipo.lot_size ? `${ipo.lot_size}股` : '—'}</Text>
                  </View>
                  <View className='info-item'>
                    <Text className='info-label'>认购截止</Text>
                    <Text className='info-value'>{formatDate(ipo.subscribe_end)}</Text>
                  </View>
                </View>

                <View className='card-footer'>
                  <Text className='listing-date'>上市：{formatDate(ipo.listing_date)}</Text>
                  {(ipo.analysis_count ?? 0) > 0 && (
                    <View className='analysis-badge'>
                      <Text className='analysis-text'>{ipo.analysis_count} 篇分析</Text>
                    </View>
                  )}
                </View>
              </View>
            )
          })
        )}
        <View className='list-bottom' />
      </ScrollView>
    </View>
  )
}
