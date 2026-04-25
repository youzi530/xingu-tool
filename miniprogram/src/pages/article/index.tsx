import Taro, { useRouter } from '@tarojs/taro'
import { WebView } from '@tarojs/components'

export default function ArticlePage() {
  const router = useRouter()
  const url = decodeURIComponent(router.params.url || '')

  if (!url) {
    Taro.navigateBack()
    return null
  }

  return <WebView src={url} />
}
