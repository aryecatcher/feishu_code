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
}

type StageType = 'PromptInput' | 'Processing'

const GAP = 10

export default function ContentBox({ selectPos, onClose }: ContentBoxProps) {
  // 页面状态管理
  const [stage, setStage] = useState<StageType>('PromptInput')
  // 窗口尺寸状态
  const [boxSize, setBoxSize] = useState({ width: 320, height: 620 })
  const contentRef = useRef<HTMLDivElement>(null)

  // 切换页面函数
  const switchToPromptInput = () => setStage('PromptInput')
  const switchToProcessing = () => setStage('Processing')

  // 计算最佳显示位置
  const initialPosition = useMemo(() => {
    const { start, end } = selectPos
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const { width, height } = boxSize

    // 计算选中区域中心点
    const selectionCenterX = (start.x + end.x) / 2
    const selectionCenterY = (start.y + end.y) / 2

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
              onSubmit={async (prompt) => {
                console.log('提交的prompt:', prompt)
                switchToProcessing()
                try {
                  // 带重试机制的消息发送，解决background未初始化问题
                  let response = null
                  let retryCount = 0
                  const maxRetries = 3
                  
                  while (retryCount < maxRetries) {
                    try {
                      response = await chrome.runtime.sendMessage({
                        type: 'START_TASK',
                        payload: {
                          pipelineId: 'default', // 默认pipeline，可根据实际需求修改
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
                }
              }}
              placeholder="请输入你的需求..."
              submitText="提交"
            />
          )}
          
          {stage === 'Processing' && (
            <ProcessingStage
              onContinue={(prompt) => {
                console.log('继续处理，prompt:', prompt)
                // 后续可在此处添加继续逻辑
                
              }}
              onReject={(prompt) => {
                console.log('拒绝处理，prompt:', prompt)
                // 后续可在此处添加拒绝逻辑

              }}
              stageContent="这里应该显示Stage或检查点详情"
              placeholder="请输入检查点建议..."
            />
          )}
        </div>
      </div>
    </>
  )
}