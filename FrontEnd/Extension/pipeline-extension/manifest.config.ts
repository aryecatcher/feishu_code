import { defineManifest } from '@crxjs/vite-plugin'
import pkg from './package.json'

export default defineManifest({
  manifest_version: 3,
  name: pkg.name,
  version: pkg.version,
  icons: {
    48: 'public/logo.png',
  },
  action: {
    default_icon: {
      48: 'public/logo.png',
    },
    // default_popup: 'src/popup/index.html', // popup配置页面入口
  },
  permissions: [
    'activeTab', // 🟢 推荐添加：访问当前激活标签页权限
    'scripting'  // 🟢 推荐添加：动态注入脚本权限
  ],
  content_scripts: [{
    js: ['src/content/main.tsx'], // 页面注入脚本入口，用于实现悬浮窗
    matches: ['https://*/*', 'http://*/*'], // 匹配需要注入的网站地址，可根据需求调整
    run_at: 'document_end', // 🟢 推荐添加：页面加载完成后注入
  }],
  background: {
    service_worker: 'src/background/main.ts', // background service worker入口
    type: 'module' // 配置为ES Module类型，适配项目模块化方案
  },
  host_permissions: ['https://*/*', 'http://*/*']
})
