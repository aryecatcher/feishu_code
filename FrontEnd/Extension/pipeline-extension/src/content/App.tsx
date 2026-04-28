/* 内容脚本主组件 */
import {useState} from 'react'
import FloatBox from './components/FloatBox.tsx'
import ContentBox from './components/ContentBox.tsx'
import SelectionOverlay from './components/SelectionOverlay.tsx'
import type {UseDragPosition} from './hooks/useDrag.tsx'

export default function App() {
  const [isSelecting, setIsSelecting] = useState(false)
  const[finalSelection, setFinalSelection] = useState<{startPos: UseDragPosition, endPos: UseDragPosition} | null>(null)
  const[showContent, setShowContent] = useState(false)

  // 处理点击浮动框
  const handleFloatBoxClick = () => {
    setIsSelecting(true)
    setShowContent(false)
    setFinalSelection(null)
  }

  // 圈选完成，显示内容窗口
  const handleSelectionComplete = (startPos: UseDragPosition, endPos: UseDragPosition) => {
    setIsSelecting(false)
    setFinalSelection({startPos: startPos, endPos: endPos})
    setShowContent(true)
  }

  return (
      <div id="crxjs-app">
        {/* 1. 悬浮球：非圈选状态下显示，内部自己管理拖拽位置 */}
        {!isSelecting && <FloatBox onActivate={handleFloatBoxClick} />}

        {/* 2. 圈选层：全屏遮罩 */}
        {isSelecting && <SelectionOverlay onSelectEnd={handleSelectionComplete} />}

        {/* 3. 内容窗口：基于圈选结果定位，内部自己管理后续拖拽 */}
        {showContent && <ContentBox selectPos={{start: finalSelection!.startPos, end: finalSelection!.endPos}} onClose={() => setShowContent(false)} />}
      </div>
  )
}
