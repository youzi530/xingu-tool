import { useState, useEffect } from 'react'
import Taro from '@tarojs/taro'
import { View, Text, ScrollView } from '@tarojs/components'
import { api } from '../../services/api'
import { Blogger } from '../../types'
import './index.scss'

const CHANNEL_LABEL: Record<string, string> = {
  wechat:   '微信公众号',
  weibo:    '微博',
  xhs:      '小红书',
  bilibili: 'B站',
}

const AVATAR_COLORS = ['#C8102E', '#1677FF', '#00A870', '#FA8C16', '#722ED1', '#13C2C2']

function getColor(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash += name.charCodeAt(i)
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}

export default function BloggersPage() {
  const [bloggers, setBloggers] = useState<Blogger[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getBloggers()
      .then(setBloggers)
      .catch(() => Taro.showToast({ title: '加载失败', icon: 'none' }))
      .finally(() => setLoading(false))
  }, [])

  return (
    <View className='page'>
      <ScrollView scrollY className='list'>
        {loading ? (
          <View className='empty'><Text className='empty-text'>加载中…</Text></View>
        ) : bloggers.length === 0 ? (
          <View className='empty'><Text className='empty-text'>暂无博主数据</Text></View>
        ) : (
          bloggers.map(blogger => (
            <View key={blogger.id} className='card'>
              <View className='avatar' style={{ backgroundColor: getColor(blogger.name) }}>
                <Text className='avatar-text'>{blogger.name.slice(0, 1)}</Text>
              </View>
              <View className='info'>
                <View className='name-row'>
                  <Text className='name'>{blogger.name}</Text>
                  <View className='channel-badge'>
                    <Text className='channel-text'>{CHANNEL_LABEL[blogger.channel] || blogger.channel}</Text>
                  </View>
                </View>
                {blogger.description && (
                  <Text className='desc'>{blogger.description}</Text>
                )}
                {blogger.follower_count && (
                  <Text className='follower'>粉丝 {blogger.follower_count}</Text>
                )}
              </View>
            </View>
          ))
        )}
        <View style={{ height: '40px' }} />
      </ScrollView>
    </View>
  )
}
