import React from 'react'
import { useDrag, UseDragPosition } from '../hooks/useDrag.tsx'
import "../App.css"

interface FloatBoxProps {
  onActivate: () => void
}

export default function FloatBox({ onActivate }: FloatBoxProps) {
  const initialPosition: UseDragPosition = { x: window.innerWidth - 180, y: window.innerHeight - 180 }
  const { ref, position, isDragging } = useDrag(initialPosition, {
    onClick: onActivate,
    threshold: 3,
    bounds: 'viewport'
  })

  return (
    <div 
      ref={ref} 
      className="float-box"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
    >
      AI
    </div>
  )
}
