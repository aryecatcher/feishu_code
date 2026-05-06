import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue({
    template: {
      compilerOptions: {
        // 编译时节点转换，最可靠的注入方式
        nodeTransforms: [
          (node, context) => {
            // 只处理元素节点
            if (node.type === 1 /* Element */) {
              // 获取当前文件路径和节点位置
              const filePath = context.filename.replace(/\\/g, '/')
              const line = node.loc.start.line
              const column = node.loc.start.column
              
              // 构造属性值
              const sourceInfo = JSON.stringify({
                path: filePath,
                line,
                column
              })
              
              // 添加自定义属性
              node.props.push({
                type: 6 /* Attribute */,
                name: 'data-source-loc',
                value: {
                  type: 2 /* Text */,
                  content: sourceInfo,
                  loc: node.loc
                },
                loc: node.loc
              })
            }
          }
        ]
      }
    }
  })],
})
