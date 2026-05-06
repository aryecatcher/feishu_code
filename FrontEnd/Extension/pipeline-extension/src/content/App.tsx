/* 内容脚本主组件 */
import {useState, useEffect} from 'react'
import FloatBox from './components/FloatBox.tsx'
import ContentBox from './components/ContentBox.tsx'
import SelectionOverlay from './components/SelectionOverlay.tsx'
import type {UseDragPosition} from './hooks/useDrag.tsx'

export default function App() {
  const [isSelecting, setIsSelecting] = useState(false)
  const[finalSelection, setFinalSelection] = useState<{startPos: UseDragPosition, endPos: UseDragPosition} | null>(null)
  const[showContent, setShowContent] = useState(false)
  const[isRefresh, setIsRefresh] = useState(false)

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

  // 组件挂载时查询任务状态
  useEffect(() => {
    const fetchTaskState = async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          type: 'GET_TASK_STATE'
        })
        
        if (response && response.success) {
          // 有正在进行的任务，直接进入处理阶段
          console.log('有正在进行的任务，直接进入处理阶段')
          setIsRefresh(true)
          setFinalSelection({
            startPos: { x: 0, y: 0 },
            endPos: { x: 0, y: 0 }
          })
          setShowContent(true)
        } else {
          // 没有进行中的任务，保持原有流程
          console.log('没有进行中的任务，保持原有流程')
          setIsRefresh(false)
        }
      } catch (error) {
        console.error('查询任务状态失败:', error)
        // 出错时保持原有流程
        setIsRefresh(false)
      }
    }
    
    fetchTaskState()
  }, [])

  return (
      <div id="crxjs-app">
        {/* 1. 悬浮球：非圈选状态下显示，内部自己管理拖拽位置 */}
        {!isSelecting && <FloatBox onActivate={handleFloatBoxClick} />}

        {/* 2. 圈选层：全屏遮罩 */}
        {isSelecting && <SelectionOverlay onSelectEnd={handleSelectionComplete} />}

        {/* 3. 内容窗口：基于圈选结果定位，内部自己管理后续拖拽 */}
        {showContent && <ContentBox selectPos={{start: finalSelection!.startPos, end: finalSelection!.endPos}} onClose={() => setShowContent(false)} isRefresh={isRefresh} />}
      </div>
  )
}
