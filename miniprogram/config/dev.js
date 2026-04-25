module.exports = {
  env: { NODE_ENV: '"development"' },
  defineConstants: {
    // 本地开发：改成你电脑的局域网 IP
    TARO_APP_API_URL: '"http://192.168.10.113:8000"',
  },
  mini: {},
  h5: {},
}
