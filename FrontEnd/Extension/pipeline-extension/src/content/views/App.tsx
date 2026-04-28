import { useState, useRef, useEffect } from 'react'
import './App.css'

type Position = { x: number; y: number }
type SelectionRect = { start: Position; end: Position } | null

function App() {
  // 悬浮窗状态
  const [position, setPosition] = useState<Position>({ x: window.innerWidth - 100, y: window.innerHeight - 100 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState<Position>({ x: 0, y: 0 })
  
  // 圈选状态
  const [isSelecting, setIsSelecting] = useState(false)
  const [selection, setSelection] = useState<SelectionRect>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [finalSelection, setFinalSelection] = useState<SelectionRect>(null) // 保存最终圈选结果，用于保持显示
  
  // 内容盒子状态
  const [showContentBox, setShowContentBox] = useState(false)
  const [contentBoxPosition, setContentBoxPosition] = useState<Position>({ x: 0, y: 0 })

  const floatBoxRef = useRef<HTMLDivElement>(null)

  // 拖拽悬浮窗逻辑
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    })
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return
      const newX = e.clientX - dragOffset.x
      const newY = e.clientY - dragOffset.y
      
      // 限制悬浮窗不超出视口
      const maxX = window.innerWidth - 80
      const maxY = window.innerHeight - 80
      setPosition({
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY)),
      })
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, dragOffset])

  // 点击悬浮窗进入圈选模式
  const handleFloatBoxClick = () => {
    if (!isDragging) {
      setIsSelecting(true)
      setSelection(null)
      setFinalSelection(null) // 新的圈选开始时清空之前的选择框
      setShowContentBox(false)
    }
  }

  // 圈选逻辑
  const handleSelectionMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDrawing(true)
    setSelection({
      start: { x: e.clientX, y: e.clientY },
      end: { x: e.clientX, y: e.clientY },
    })
  }

  const handleSelectionMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !selection) return
    setSelection({
      ...selection,
      end: { x: e.clientX, y: e.clientY },
    })
  }

  const handleSelectionMouseUp = () => {
    if (!isDrawing || !selection) return
    setIsDrawing(false)
    setIsSelecting(false)
    setFinalSelection(selection) // 保存最终选择框，保持显示

    // 计算内容盒子位置（圈选区域右下角）
    const maxX = Math.max(selection.start.x, selection.end.x)
    const maxY = Math.max(selection.start.y, selection.end.y)
    setContentBoxPosition({ x: maxX + 10, y: maxY + 10 })
    setShowContentBox(true)
  }

  // 计算选框样式
  const getSelectionStyle = () => {
    if (!selection) return {}
    const minX = Math.min(selection.start.x, selection.end.x)
    const minY = Math.min(selection.start.y, selection.end.y)
    const width = Math.abs(selection.end.x - selection.start.x)
    const height = Math.abs(selection.end.y - selection.start.y)
    
    return {
      left: minX,
      top: minY,
      width,
      height,
    }
  }

  return (
    <div className="crx-root">
      {/* 悬浮窗 */}
      {!isSelecting && (
        <div
          ref={floatBoxRef}
          className="float-box"
          style={{ left: position.x, top: position.y }}
          onMouseDown={handleMouseDown}
          onClick={handleFloatBoxClick}
        >
          选
        </div>
      )}

      {/* 圈选遮罩和选框 */}
      {isSelecting && (
        <div
          className="selection-overlay"
          onMouseDown={handleSelectionMouseDown}
          onMouseMove={handleSelectionMouseMove}
          onMouseUp={handleSelectionMouseUp}
          onMouseLeave={handleSelectionMouseUp}
        >
          {selection && (
            <div className="selection-rect" style={getSelectionStyle()} />
          )}
        </div>
      )}

      {/* 内容展示盒子 */}
      {showContentBox && (
        <div
          className="content-box"
          style={{ left: contentBoxPosition.x, top: contentBoxPosition.y }}
        >
          内容展示区域
        </div>
      )}

      {/* 最终圈选框保持显示 */}
      {finalSelection && (
        <div
          className="selection-rect-final"
          style={{
            position: 'fixed',
            left: Math.min(finalSelection.start.x, finalSelection.end.x),
            top: Math.min(finalSelection.start.y, finalSelection.end.y),
            width: Math.abs(finalSelection.end.x - finalSelection.start.x),
            height: Math.abs(finalSelection.end.y - finalSelection.start.y),
          }}
        />
      )}
    </div>
  )
}

export default App
