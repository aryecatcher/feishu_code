import React, { useState, forwardRef, useImperativeHandle, useEffect } from 'react'
import { useDAG, DAGNode, DAGEdge } from '../../hooks/useDAG'
import './ProcessingStage.css'

// 按钮组件Props定义
interface ActionButtonProps {
  children: React.ReactNode
  onClick: () => void
  variant?: 'primary' | 'secondary'
}

// 输入框组件Props定义
interface PromptInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

// DAG渲染区域组件Props定义
interface DagRendererProps {
  className?: string
  onSelectNode?: (nodeId: string | null) => void
}

// 内容区域组件Props定义
interface StageContentProps {
  content: string
  className?: string
}

// 组件对外暴露的方法类型
export interface ProcessingStageRef {
  setIsCheckpoint: (value: boolean) => void
  getIsCheckpoint: () => boolean
}

// 主组件Props定义
interface ProcessingStageProps {
  onContinue: (prompt: string, checkpointId: string) => void
  onReject: (prompt: string, checkpointId: string) => void
  stageContent?: string
  placeholder?: string
  initialIsCheckpoint?: boolean
}

// 按钮组件
const ActionButton: React.FC<ActionButtonProps> = ({ 
  children, 
  onClick, 
  variant = 'primary' 
}) => {
  return (
    <button
      onClick={onClick}
      className={`action-button ${variant}`}
    >
      <span className="action-button-text">{children}</span>
    </button>
  )
}

// 输入框组件
const PromptInput: React.FC<PromptInputProps> = ({ 
  value, 
  onChange, 
  placeholder = '请输入检查点建议提示词' 
}) => {
  return (
    <div className="prompt-input">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="prompt-input-field"
      />
    </div>
  )
}

// DAG渲染区域组件
const DagRenderer: React.FC<DagRendererProps> = ({ className = '', onSelectNode }) => {
  // DAG数据状态
  const [nodes, setNodes] = useState<DAGNode[]>([
    {id: 'loading', label: '加载Pipeline中...', status: 'running'}
  ])
  const [edges, setEdges] = useState<DAGEdge[]>([])
  
  // 选中的DAG节点id状态
  const [selectedDAG, setSelectedDAG] = useState<string | null>(null)

  // 从Message拉取DAG数据
  useEffect(() => {
    chrome.runtime.sendMessage({
      type: 'GET_PIPELINE_CONFIG',
      payload: {
        pipelineId: 'default', // 默认pipeline
      }
    }, (response) => {
      try {
        // 先处理Chrome runtime错误（如后台无响应、消息发送失败等）
        if (chrome.runtime.lastError) {
          console.error('获取Pipeline结构数据失败:', chrome.runtime.lastError.message)
          const errorNodes: DAGNode[] = [{id: 'error', label: '加载失败', status: 'failed'}]
          setNodes(errorNodes)
          setEdges([])
          setSelectedDAG(errorNodes[0].id)
          return
        }

        if (response && response.success) {
          console.log('Pipeline结构数据:', response.data)
          
          // 优先使用后端返回的真实数据
          let fetchedNodes: DAGNode[] = []
          let fetchedEdges: DAGEdge[] = []
          
          if (response.data?.stages?.[0]?.stage_type) {
            // 解析后端返回的真实数据
            // API 返回值不对，因此压根解析不出来
            console.log('天呐！居然有返回值了！API复活！！ProcessingStage组件！')
          } else {
            // 后端API还没好时使用固定数据
            fetchedNodes = [
              {id: 'demand-analysis', label: '需求分析', status: 'pending'},
              {id: 'scheme-design', label: '方案设计', status: 'pending'},
              {id: 'code-generation', label: '代码生成', status: 'pending'},
              {id: 'code-review', label: '代码审核', status: 'pending'},
              {id: 'delivery', label: '交付集成', status: 'pending'}
            ]
            fetchedEdges = [
              {from: 'demand-analysis', to: 'scheme-design'},
              {from: 'scheme-design', to: 'code-generation'},
              {from: 'code-generation', to: 'code-review'},
              {from: 'code-review', to: 'delivery'}
            ]
            console.log('因为API还没有好，所以解析不了Pipeline结构数据，用固定的：', fetchedNodes, fetchedEdges)
          }

          // 更新状态
          setNodes(fetchedNodes)
          setEdges(fetchedEdges)
          // 默认选中第一个节点
          if (fetchedNodes.length > 0) {
            setSelectedDAG(fetchedNodes[0].id)
          }
        } 
        else {
          console.error('获取Pipeline结构数据失败:', response?.error || response)
          const errorNodes: DAGNode[] = [{id: 'error', label: '加载失败', status: 'failed'}]
          setNodes(errorNodes)
          setEdges([])
          // 错误状态也默认选中错误节点
          setSelectedDAG(errorNodes[0].id)
        }
      } catch (err) {
        console.error('处理Pipeline数据处理过程中发生未捕获错误:', err)
        const errorNodes: DAGNode[] = [{id: 'error', label: '加载失败', status: 'failed'}]
        setNodes(errorNodes)
        setEdges([])
        setSelectedDAG(errorNodes[0].id)
      }
    })
  }, []) // 空依赖确保只请求一次

  // 监听selectedDAG变化，通知父组件
  useEffect(() => {
    if (onSelectNode) {
      onSelectNode(selectedDAG)
    }
  }, [selectedDAG, onSelectNode])

  const { DAGComponent } = useDAG(nodes, edges, {
    onNodeClick: (node) => {
      console.log('点击了DAG节点:', node)
      // 更新选中的DAG节点
      setSelectedDAG(node.id)
    }
  })

  return (
    <div className={`dag-renderer ${className}`} onMouseDown={(e) => e.stopPropagation()}>
      <DAGComponent />
    </div>
  )
}

// 内容区域组件
const StageContent: React.FC<StageContentProps> = ({ content, className = '' }) => {
  return (
    <div className={`stage-content ${className}`}>
      <p className="stage-content-text">
        {content || '这里应该显示Stage详情或检查点内容'}
      </p>
    </div>
  )
}

// 主组件
const ProcessingStage = forwardRef<ProcessingStageRef, ProcessingStageProps>(({
  onContinue,
  onReject,
  placeholder = '请输入检查点建议提示词',
  initialIsCheckpoint = false
}, ref) => {
  const [prompt, setPrompt] = useState('')
  const [isCheckpoint, setIsCheckpoint] = useState(initialIsCheckpoint)
  // 当前选中的DAG节点id
  const [selectedDAG, setSelectedDAG] = useState<string | null>(null)
  // 当前需要显示的Content内容
  const [stageContent, setStageContent] = useState('初始化StageContent')
  
  // 拉取检查点信息的通用函数
  const fetchCheckpointInfo = (stageId: string) => {
    console.log(`[刷新检查点] 开始获取节点 ${stageId} 的检查点信息`)
    chrome.runtime.sendMessage({
      type: 'GET_CHECKPOINT',
      payload: {
        stageId
      }
    }, (response) => {
      // 先处理Chrome runtime错误
      if (chrome.runtime.lastError) {
        console.error('获取检查点信息失败:', chrome.runtime.lastError.message)
        setStageContent('获取检查点信息失败，请稍后重试。')
        setIsCheckpoint(false)
        return
      }

      // 处理response为null的情况
      if (!response) {
        console.error('获取检查点信息失败: 后台返回null响应')
        setStageContent('获取检查点信息失败，后台无响应，请稍后重试。')
        setIsCheckpoint(false)
        return
      }

      if (response.success) {
        console.log('检查点反馈数据:', response.data)
        // 更新状态
        setStageContent(response.data?.stage_result?.output?.response as string || response.data?.stage_result?.output as string || '')
        if (response.data?.status==='waiting_approval'){
          setIsCheckpoint(true)
        } else {
          setIsCheckpoint(false)
        }
      } else {
        console.log('没有检查点信息', response)
        setStageContent('没有检查点信息。')
        setIsCheckpoint(false)
      }
    })
  }

  // 监听选中节点变化
  useEffect(() => {
    console.log('当前选中的DAG节点ID:', selectedDAG)
    // 拉取对应Stage的节点信息
    if (selectedDAG) {
      fetchCheckpointInfo(selectedDAG)
    }
  }, [selectedDAG])

  // 自动刷新检查点信息（每5秒刷新一次）
  useEffect(() => {
    if (!selectedDAG) return

    console.log(`[自动刷新] 已开启节点 ${selectedDAG} 的检查点自动刷新，间隔5秒`)
    const intervalId = setInterval(() => {
      fetchCheckpointInfo(selectedDAG)
    }, 5000)

    // 清理定时器
    return () => {
      console.log(`[自动刷新] 已关闭节点 ${selectedDAG} 的检查点自动刷新`)
      clearInterval(intervalId)
    }
  }, [selectedDAG])

  // 对外暴露的方法
  useImperativeHandle(ref, () => ({
    setIsCheckpoint: (value: boolean) => setIsCheckpoint(value),
    getIsCheckpoint: () => isCheckpoint
  }))

  const handleContinue = () => {
    onContinue(prompt, selectedDAG || '')
    setIsCheckpoint(false)
  }

  const handleReject = () => {
    onReject(prompt, selectedDAG || '')
    setIsCheckpoint(false)
  }

  return (
    <div className="processing-stage-container">
      {/* DAG渲染区域 */}
      <DagRenderer onSelectNode={setSelectedDAG} />

      {/* Stage详情区域 */}
      <StageContent content={stageContent} />

      {/* 输入框区域 - 仅检查点模式显示 */}
      {isCheckpoint && (
        <PromptInput
          value={prompt}
          onChange={setPrompt}
          placeholder={placeholder}
        />
      )}

      {/* 按钮区域 - 仅检查点模式显示 */}
      {isCheckpoint && (
        <div className="action-buttons-wrapper">
          <ActionButton onClick={handleContinue}>
            继续
          </ActionButton>
          <ActionButton onClick={handleReject}>
            拒绝
          </ActionButton>
        </div>
      )}
    </div>
  )
})

export default ProcessingStage
