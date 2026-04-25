export default {
  pages: [
    'pages/index/index',
    'pages/bloggers/index',
    'pages/ipo-detail/index',
    'pages/article/index',
  ],
  window: {
    backgroundTextStyle: 'light',
    navigationBarBackgroundColor: '#C8102E',
    navigationBarTitleText: '新股通',
    navigationBarTextStyle: 'white',
    backgroundColor: '#F5F5F5',
  },
  tabBar: {
    color: '#999999',
    selectedColor: '#C8102E',
    backgroundColor: '#FFFFFF',
    borderStyle: 'black' as const,
    list: [
      {
        pagePath: 'pages/index/index',
        text: '新股',
      },
      {
        pagePath: 'pages/bloggers/index',
        text: '博主',
      },
    ],
  },
}
