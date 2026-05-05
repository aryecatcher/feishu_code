import React, { useState, useRef, useEffect } from 'react'
import '../App.css'
import type { UseDragPosition } from '../hooks/useDrag.tsx'

interface SelectionOverlayProps {
  onSelectEnd: (startPos: UseDragPosition, endPos: UseDragPosition) => void
}

export default function SelectionOverlay({ onSelectEnd }: SelectionOverlayProps) {
  const [isSelecting, setIsSelecting] = useState(false)
  const [selectionRect, setSelectionRect] = useState({
    left: 0,
    top: 0,
    right: 0,
    bottom: 0
  })
  const startPosRef = useRef<UseDragPosition>({ x: 0, y: 0 })

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      e.preventDefault()
      startPosRef.current = { x: e.clientX, y: e.clientY }
      setIsSelecting(true)
      setSelectionRect({
        left: e.clientX,
        top: e.clientY,
        right: e.clientX,
        bottom: e.clientY
      })
    }

    const onMouseMove = (e: MouseEvent) => {
      if (!isSelecting) return
      const currentX = e.clientX
      const currentY = e.clientY
      setSelectionRect({
        left: Math.min(startPosRef.current.x, currentX),
        top: Math.min(startPosRef.current.y, currentY),
        right: Math.max(startPosRef.current.x, currentX),
        bottom: Math.max(startPosRef.current.y, currentY)
      })
    }

    const onMouseUp = () => {
      if (!isSelecting) return
      setIsSelecting(false)
      const { left, top, right, bottom } = selectionRect
      if (right - left > 5 && bottom - top > 5) {
        onSelectEnd({ x: left, y: top }, { x: right, y: bottom })
      }
    }

    document.addEventListener('mousedown', onMouseDown)
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)

    return () => {
      document.removeEventListener('mousedown', onMouseDown)
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }
  }, [isSelecting, selectionRect, onSelectEnd])

  return (
    <div className="selection-overlay">
      {isSelecting && (
        <div
          className="selection-rect"
          style={{
            left: `${selectionRect.left}px`,
            top: `${selectionRect.top}px`,
            width: `${selectionRect.right - selectionRect.left}px`,
            height: `${selectionRect.bottom - selectionRect.top}px`
          }}
        />
      )}
    </div>
  )
}
