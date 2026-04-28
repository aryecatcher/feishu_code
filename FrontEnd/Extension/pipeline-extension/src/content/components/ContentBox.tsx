import React, { useMemo } from 'react'
import { useDrag, UseDragPosition } from '../hooks/useDrag.tsx'
import "../App.css"

interface ContentBoxProps {
  selectPos: {
    start: UseDragPosition
    end: UseDragPosition
  }
  onClose: () => void
}

const BOX_WIDTH = 300
const BOX_HEIGHT = 200
const GAP = 10

export default function ContentBox({ selectPos, onClose }: ContentBoxProps) {
  // 计算最佳显示位置
  const initialPosition = useMemo(() => {
    const { start, end } = selectPos
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    // 尝试四个角：右下、左下、右上、左上
    const positions = [
      { x: end.x + GAP, y: end.y + GAP }, // 右下
      { x: start.x - BOX_WIDTH - GAP, y: end.y + GAP }, // 左下
      { x: end.x + GAP, y: start.y - BOX_HEIGHT - GAP }, // 右上
      { x: start.x - BOX_WIDTH - GAP, y: start.y - BOX_HEIGHT - GAP }, // 左上
    ]

    // 找到第一个在视口内的位置
    for (const pos of positions) {
      if (
        pos.x >= 0 &&
        pos.x + BOX_WIDTH <= viewportWidth &&
        pos.y >= 0 &&
        pos.y + BOX_HEIGHT <= viewportHeight
      ) {
        return pos
      }
    }

    // 如果都不合适，默认显示在右下角
    return {
      x: Math.max(0, viewportWidth - BOX_WIDTH - GAP),
      y: Math.max(0, viewportHeight - BOX_HEIGHT - GAP)
    }
  }, [selectPos])
  
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
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
      >
        <div className="content-box-header">
          <h3 className="content-box-title">AI 分析结果</h3>
          <button
            onClick={onClose}
            className="content-box-close"
          >
            ×
          </button>
        </div>
        <div className="content-box-body">
          <p>选中区域信息：</p>
          <ul className="content-box-list">
            <li>位置: ({selectPos.start.x}, {selectPos.start.y})</li>
            <li>结束位置: ({selectPos.end.x}, {selectPos.end.y})</li>
            <li>大小: {selectPos.end.x - selectPos.start.x + 1} × {selectPos.end.y - selectPos.start.y + 1}px</li>
          </ul>
          <p>这里将展示AI对选中内容的分析结果</p>
        </div>
      </div>
    </>
  )
}