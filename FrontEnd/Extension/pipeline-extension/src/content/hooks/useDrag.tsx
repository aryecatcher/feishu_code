/*  拖拽与点击判别逻辑复用 */
import {useState, useRef, useEffect} from 'react'
export interface UseDragPosition {
    x: number
    y: number
}

interface Options {
    threshold?: number              // 拖拽阈值，默认为3px
    bounds?: 'viewport' | 'none'    // 拖拽范围，默认为视口
    onClick?: () => void            // 非拖拽时的点击事件
}

export function useDrag(initial: UseDragPosition, options: Options = {}) {
    const {threshold = 3, bounds = 'viewport', onClick} = options   // 解构赋值，默认值
    const [position, setPosition] = useState(initial)
    const [isDragging, setIsDragging] = useState(false)
    const ref = useRef<HTMLDivElement>(null)                        // 拖拽元素的引用


    const dragState = useRef({
        startX:0, startY:0,     // 拖拽开始时的坐标
        initX:0, initY:0,       // 元素初始位置
        hasMoved:false
    })
    const onClickRef = useRef(onClick)
    onClickRef.current = onClick

    useEffect(() => {
        const handle = ref.current
        if (!handle) return

        const onMouseDown = (e: MouseEvent) => {        // 鼠标按下事件，记录拖拽开始时的坐标
            const target = e.target as HTMLElement
            // 如果点击的是交互元素（输入框、按钮等）或标记为no-drag的区域，不触发拖拽
            if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'BUTTON' || 
                target.closest('input, textarea, button, .no-drag')) {
                return
            }
            e.preventDefault()
            dragState.current.startX = e.clientX
            dragState.current.startY = e.clientY
            dragState.current.initX = handle.getBoundingClientRect().left
            dragState.current.initY = handle.getBoundingClientRect().top
            dragState.current.hasMoved = false
            
            const onMove = (e: MouseEvent) => {        // 鼠标移动事件，判断是否触发拖拽逻辑
                const dx = e.clientX - dragState.current.startX
                const dy = e.clientY - dragState.current.startY
                if (!dragState.current.hasMoved && (Math.abs(dx) > threshold || Math.abs(dy) > threshold)) {
                    dragState.current.hasMoved = true
                    setIsDragging(true)
                }

                // 计算新位置，考虑边界
                let newX = dragState.current.initX + dx
                let newY = dragState.current.initY + dy
                if (bounds ==='viewport') {
                    const maxX = window.innerWidth - handle.offsetWidth
                    const maxY = window.innerHeight - handle.offsetHeight
                    newX = Math.max(0, Math.min(maxX, newX))
                    newY = Math.max(0, Math.min(maxY, newY))
                }
                setPosition({x:newX, y:newY})
            }

            const onUp = () => {                        // 鼠标释放事件，判断是否触发点击事件
                setIsDragging(false)
                if (!dragState.current.hasMoved) {
                    onClickRef.current?.()
                }
                document.removeEventListener('mousemove', onMove)
                document.removeEventListener('mouseup', onUp)
            }
            document.addEventListener('mousemove', onMove)
            document.addEventListener('mouseup', onUp)
        }

        handle.addEventListener('mousedown', onMouseDown)
        // 组件卸载时移除事件监听，避免内存泄漏
        return () => {
            handle.removeEventListener('mousedown', onMouseDown)
        }
    }, [threshold, bounds])
    return { ref, position, isDragging }     // 返回拖拽元素的引用、当前位置、是否正在拖拽
}