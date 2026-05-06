import React, { useMemo, useState, useRef } from 'react'
import { useDrag, UseDragPosition } from '../hooks/useDrag.tsx'
import { PromptInputStage } from './ContentBoxBody/PromptInputStage.tsx'
import ProcessingStage from './ContentBoxBody/ProcessingStage.tsx'
import "../App.css"

interface ContentBoxProps {
  selectPos: {
    start: UseDragPosition
    end: UseDragPosition
  }
  onClose: () => void
  isRefresh?: boolean
}

type StageType = 'PromptInput' | 'Processing'

const GAP = 10

export default function ContentBox({ selectPos, onClose, isRefresh = false }: ContentBoxProps) {
  // 页面状态管理
  const [stage, setStage] = useState<StageType>('PromptInput')
  // 窗口尺寸状态
  const [boxSize, _setBoxSize] = useState({ width: 320, height: 620 })
  const contentRef = useRef<HTMLDivElement>(null)
  // 选中区域内的DOM元素列表
  const [_selectedElements, _setSelectedElements] = useState<Element[]>([])
  // 源码位置列表
  const [_sourceLocations, _setSourceLocations] = useState<string[]>([])

  // 获取选中区域的所有数据：DOM元素列表和源码位置
  const getSelectionData = React.useCallback(() => {
    const { start, end } = selectPos
    const minX = Math.min(start.x, end.x)
    const maxX = Math.max(start.x, end.x)
    const minY = Math.min(start.y, end.y)
    const maxY = Math.max(start.y, end.y)
    
    const elements = new Set<Element>()
    
    // 步长设置为10px，平衡性能和检测精度
    const step = 10
    
    // 遍历矩形区域内的点，收集所有元素
    for (let x = minX; x <= maxX; x += step) {
      for (let y = minY; y <= maxY; y += step) {
        const pointElements = document.elementsFromPoint(x, y)
        pointElements.forEach(el => elements.add(el))
      }
    }
    
    // 计算选框基础参数
    const selectionWidth = maxX - minX
    const selectionHeight = maxY - minY
    const selectionArea = selectionWidth * selectionHeight
    
    // 语义白名单：包含有价值语义的标签
    const semanticWhitelist = new Set([
      'BUTTON', 'P', 'A', 'IMG', 'INPUT', 'TEXTAREA', 'SELECT',
      'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'SPAN', 'LI', 'UL', 'OL',
      'TABLE', 'TR', 'TD', 'TH', 'DIV', 'SECTION', 'ARTICLE', 
      'HEADER', 'FOOTER', 'NAV', 'FORM', 'LABEL', 'VIDEO', 'AUDIO', 'CANVAS'
    ])

    // 转换为数组并过滤掉我们自己添加的选择框和内容窗口元素
    const filteredElements = Array.from(elements).filter(el => 
      !el.classList.contains('selection-rect-final') && 
      !el.classList.contains('content-box') &&
      !el.closest('.content-box')
    )
    // 遴选逻辑：排除无意义元素
    .filter(el => {
      // 1. 语义白名单检查：只保留有价值语义的标签
      const tagName = el.tagName.toUpperCase()
      if (!semanticWhitelist.has(tagName)) return false

      // // 2. 视图检测：中心点(弃)
      const rect = el.getBoundingClientRect()
      // const centerX = rect.left + rect.width / 2
      // const centerY = rect.top + rect.height / 2
      // const isCenterInSelection = centerX >= minX && centerX <= maxX && centerY >= minY && centerY <= maxY
      // if (!isCenterInSelection) return false

      // 3. 面积比例检查：排除极小或极大元素
      const elArea = rect.width * rect.height
      const areaRatio = elArea / selectionArea
      if (areaRatio < 0.01 || areaRatio > 5) return false // 小于1%或大于5倍选框面积则排除

      return true
    })
    
    // 提取源码位置
    const locations = new Set<string>()
    filteredElements.forEach(el => {
      // 提取data-source-loc属性（JSON格式）
      const dataSourceLoc = el.getAttribute('data-source-loc')
      if (dataSourceLoc) {
        try {
          // 解析JSON格式的source-loc，提取path字段
          const locData = JSON.parse(dataSourceLoc)
          if (locData.path && typeof locData.path === 'string') {
            locations.add(locData.path.trim())
          }
        } catch (e) {
          // 解析失败时，如果是直接的路径字符串也直接添加
          if (typeof dataSourceLoc === 'string' && dataSourceLoc.trim() && !dataSourceLoc.startsWith('http') && !dataSourceLoc.startsWith('data:')) {
            locations.add(dataSourceLoc.trim())
          }
        }
      }
      
      // 提取其他常见的源码路径属性
      const otherSourceAttrs = ['data-source', 'data-src', 'data-file', 'data-path', 'src']
      otherSourceAttrs.forEach(attr => {
        const value = el.getAttribute(attr)
        if (value && typeof value === 'string' && value.trim() && !value.startsWith('http') && !value.startsWith('data:')) {
          locations.add(value.trim())
        }
      })
    })
    
    const sourceLocations = Array.from(locations)
    
    // 更新状态
    _setSelectedElements(filteredElements)
    _setSourceLocations(sourceLocations)
    
    // 同时返回元素和位置
    return {
      elements: filteredElements,
      locations: sourceLocations
    }
  }, [selectPos])

  // 组件加载时获取选中区域的元素和源码位置
  React.useEffect(() => {
    const { elements, locations } = getSelectionData()
    
    console.log('选中区域内的DOM元素:', elements)
    console.log('提取到的源码位置:', locations)
  }, [getSelectionData])

  // 如果是刷新模式，直接跳转到处理阶段
  React.useEffect(() => {
    if (isRefresh) {
      switchToProcessing()
    }
  }, [isRefresh])

  // 切换页面函数
  // const switchToPromptInput = () => setStage('PromptInput')// 切换页面函数
  const switchToProcessing = () => setStage('Processing')

  // 处理Prompt提交
  const handleSubmit = async (prompt: string) => {
    console.log('提交的prompt:', prompt)
    try {
      // 带重试机制的消息发送
      let response = null
      let retryCount = 0
      const maxRetries = 3
      
      while (retryCount < maxRetries) {
        try {
          response = await chrome.runtime.sendMessage({
            type: 'START_TASK',
            payload: {
              pipelineId: 'default', // 默认pipeline
              sourcePath: _sourceLocations,
              prompt: prompt
            }
          })
          break
        } catch (err) {
          retryCount++
          if (retryCount >= maxRetries) throw err
          // 重试间隔500ms，等待background初始化
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }
      
      if (response && response.success) {
        console.log('任务启动成功:', response.data)
        // 切换到处理中页面
        switchToProcessing()
      } else {
        console.error('任务启动失败:', response?.error || '未知错误')
        // 可在此处添加错误提示逻辑
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      // 可在此处添加错误提示逻辑
      alert('连接后台失败，请刷新页面后重试或检查扩展是否正确安装')
      switchToProcessing()
    }
  }

  // 处理Checkpoint提交
  const handleCheckpoint = async (prompt: string, isAccept: boolean, checkpointId: string) => {
    console.log('检查点:', isAccept ? '接受' : '拒绝', '提交的prompt:', prompt)
    try {
      // 带重试机制的消息发送
      let response = null
      let retryCount = 0
      const maxRetries = 3
      
      while (retryCount < maxRetries) {
        try {
          response = await chrome.runtime.sendMessage({
            type: 'CHECKPOINT_PROMPT',
            payload: {
              checkpointId: checkpointId,
              action: isAccept ? 'approve' : 'reject',
              prompt: prompt || ''
            }
          })
          break
        } catch (err) {
          retryCount++
          if (retryCount >= maxRetries) throw err
          // 重试间隔500ms，等待background初始化
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }
      
      if (response && response.success) {
        console.log('检查点提交成功:', response.data)
        
      } else {
        console.error('检查点提交失败:', response?.error || '未知错误')
      }
    } catch (error) {
      console.error('检查点提交失败:', error)
      // 可在此处添加错误提示逻辑
      alert('连接后台失败，请刷新页面后重试或检查扩展是否正确安装')
    }
  }

  // 计算最佳显示位置
  const initialPosition = useMemo(() => {
    const { start, end } = selectPos
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const { width, height } = boxSize

    // 计算选中区域中心点
    const selectionCenterX = (start.x + end.x) / 2
    // const selectionCenterY = (start.y + end.y) / 2

    // 动态调整位置优先级：根据选中区域在视口的位置决定优先尝试的位置
    const rightSpace = viewportWidth - end.x - GAP
    const leftSpace = start.x - GAP
    const bottomSpace = viewportHeight - end.y - GAP
    const topSpace = start.y - GAP

    const positions = []

    // 优先选择右侧空间足够的情况
    if (rightSpace >= width) {
      // 右侧有足够空间，优先上半部分显示在右下，下半部分显示在右上
      if (bottomSpace >= height) {
        positions.push({ x: end.x + GAP, y: end.y + GAP }) // 右下
      }
      if (topSpace >= height) {
        positions.push({ x: end.x + GAP, y: start.y - height - GAP }) // 右上
      }
    }

    // 其次选择左侧空间足够的情况
    if (leftSpace >= width) {
      // 左侧有足够空间
      if (bottomSpace >= height) {
        positions.push({ x: start.x - width - GAP, y: end.y + GAP }) // 左下
      }
      if (topSpace >= height) {
        positions.push({ x: start.x - width - GAP, y: start.y - height - GAP }) // 左上
      }
    }

    // 如果左右都没有足够空间，再尝试上下空间
    if (positions.length === 0) {
      // 尝试下方居中
      if (bottomSpace >= height) {
        positions.push({
          x: Math.max(0, Math.min(selectionCenterX - width / 2, viewportWidth - width)),
          y: end.y + GAP
        })
      }
      // 尝试上方居中
      if (topSpace >= height) {
        positions.push({
          x: Math.max(0, Math.min(selectionCenterX - width / 2, viewportWidth - width)),
          y: start.y - height - GAP
        })
      }
    }

    // 找到第一个在视口内的位置
    for (const pos of positions) {
      if (
        pos.x >= 0 &&
        pos.x + width <= viewportWidth &&
        pos.y >= 0 &&
        pos.y + height <= viewportHeight
      ) {
        return pos
      }
    }

    // 如果都不合适，智能定位：优先显示在视口可见区域，尽量靠近选中区域
    return {
      x: Math.max(0, Math.min(
        rightSpace >= width ? end.x + GAP : (leftSpace >= width ? start.x - width - GAP : viewportWidth / 2 - width / 2),
        viewportWidth - width - GAP
      )),
      y: Math.max(0, Math.min(
        bottomSpace >= height ? end.y + GAP : (topSpace >= height ? start.y - height - GAP : viewportHeight / 2 - height / 2),
        viewportHeight - height - GAP
      ))
    }
  }, [selectPos, boxSize])
  
  const { ref, position, isDragging } = useDrag(initialPosition, {
    bounds: 'viewport',
    threshold: 3
  })

  return (
    <>
      {/* 持久显示选中区域 */}
      <div
        className="selection-rect-final"
        style={{
          position: 'fixed',
          left: `${selectPos.start.x}px`,
          top: `${selectPos.start.y}px`,
          width: `${selectPos.end.x - selectPos.start.x + 1}px`,
          height: `${selectPos.end.y - selectPos.start.y + 1}px`
        }}
      />

      {/* 内容窗口 */}
      <div
        ref={ref}
        className="content-box"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
          cursor: isDragging ? 'grabbing' : 'grab',
          width: 'auto',
          height: 'auto'
        }}
      >
        <div className="content-box-header">
          <h3 className="content-box-title">Pipeline Engine</h3>
          <button
            onClick={onClose}
            className="content-box-close"
          >
            ×
          </button>
        </div>
        <div ref={contentRef} className="content-box-body p-0">
          {stage === 'PromptInput' && (
            <PromptInputStage
              onSubmit={handleSubmit}
              placeholder="请输入你的需求..."
              submitText="提交"
            />
          )}
          
          {stage === 'Processing' && (
            <ProcessingStage
              onContinue={(prompt, checkpointId) => handleCheckpoint(prompt, true, checkpointId)}
              onReject={(prompt, checkpointId) => handleCheckpoint(prompt, false, checkpointId)}
              placeholder="请输入检查点建议..."
            />
          )}
        </div>
      </div>
    </>
  )
}