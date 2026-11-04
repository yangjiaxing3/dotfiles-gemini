export default {
  site: 'https://www.us3c.com.tw',
  server: {
    port: 5678,
    host: 'localhost',
    // 自動開瀏覽器會再起一個 Chrome，長掃時容易把 Puppeteer page 打掛
    open: false,
  },
  scanner: {
    maxRoutes: 250,
    sitemap: ['https://www.us3c.com.tw/sitemap.xml'],
    crawler: false,
    dynamicSampling: false,
  },
  puppeteerClusterOptions: {
    maxConcurrency: 1,
  },
}
