module.exports = {
  env: { NODE_ENV: '"production"' },
  defineConstants: {
    // 上线后替换为你的后端域名（需在小程序后台添加为合法域名）
    TARO_APP_API_URL: '"https://youzi530-xingu-tool-api.hf.space"',
  },
  mini: {
    optimizeMainPackage: { enable: true },
  },
  h5: {},
}
