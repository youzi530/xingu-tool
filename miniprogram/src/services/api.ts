import Taro from '@tarojs/taro'
import { IPO, IPOWithAnalyses, Blogger } from '../types'

declare const TARO_APP_API_URL: string
const BASE_URL = (typeof TARO_APP_API_URL !== 'undefined' ? TARO_APP_API_URL : '') || 'http://192.168.10.199:8000'

function request<T>(path: string): Promise<T> {
  return new Promise((resolve, reject) => {
    Taro.request({
      url: `${BASE_URL}${path}`,
      header: { 'Content-Type': 'application/json' },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject(new Error(`API ${res.statusCode}: ${path}`))
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

function post<T>(path: string): Promise<T> {
  return new Promise((resolve, reject) => {
    Taro.request({
      url: `${BASE_URL}${path}`,
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject(new Error(`API ${res.statusCode}: ${path}`))
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

export const api = {
  getIPOs(status?: string): Promise<IPO[]> {
    const qs = status ? `?status=${status}` : ''
    return request<IPO[]>(`/ipos/${qs}`)
  },

  getIPODetail(ipoId: number, bloggerId?: number): Promise<IPOWithAnalyses> {
    const qs = bloggerId ? `?blogger_id=${bloggerId}` : ''
    return request<IPOWithAnalyses>(`/ipos/${ipoId}${qs}`)
  },

  getBloggers(): Promise<Blogger[]> {
    return request<Blogger[]>('/bloggers/')
  },

  /** 按需刷新文章链接：若是过期搜狗链接，后端会重新解析/搜索后返回永久微信 URL */
  refreshArticleUrl(analysisId: number): Promise<{ url: string; refreshed: boolean }> {
    return post(`/analyses/${analysisId}/refresh-url`)
  },
}
