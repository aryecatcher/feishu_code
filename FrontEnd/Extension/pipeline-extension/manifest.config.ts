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
    default_popup: 'src/popup/index.html', // popup配置页面入口
  },
  permissions: [
    // 'sidePanel', // 🔴 不需要的权限：侧边栏功能，可删除
    // 'contentSettings', // 🔴 不需要的权限：内容设置权限，如不需要可删除
    'activeTab', // 🟢 推荐添加：访问当前激活标签页权限
    'scripting', // 🟢 推荐添加：动态注入脚本权限
  ],
  content_scripts: [{
    js: ['src/content/main.tsx'], // 页面注入脚本入口，用于实现悬浮窗
    matches: ['https://*/*'], // 匹配需要注入的网站地址，可根据需求调整
    run_at: 'document_end', // 🟢 推荐添加：页面加载完成后注入
  }],
  // side_panel: { // 🔴 不需要的配置：侧边栏页面，可删除
  //   default_path: 'src/sidepanel/index.html',
  // },
  host_permissions: ['https://*/*'], // 🟢 推荐添加：允许访问所有网站权限
})
