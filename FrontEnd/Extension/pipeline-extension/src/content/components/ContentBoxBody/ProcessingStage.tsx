import React, { useState, forwardRef, useImperativeHandle } from 'react'
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
  onContinue: (prompt: string) => void
  onReject: (prompt: string) => void
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
const DagRenderer: React.FC<DagRendererProps> = ({ className = '' }) => {
  // 模拟DAG数据
  const nodes: DAGNode[] = [
    { id: '1', label: '数据收集', status: 'success' },
    { id: '2', label: '模型处理', status: 'running' },
    { id: '3', label: '结果输出', status: 'pending' },
  ]

  const edges: DAGEdge[] = [
    { from: '1', to: '2' },
    { from: '2', to: '3' },
  ]

  const { DAGComponent } = useDAG(nodes, edges, {
    onNodeClick: (node) => {
      console.log('点击了DAG节点:', node)
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
  stageContent = '',
  placeholder = '请输入检查点建议提示词',
  initialIsCheckpoint = false
}, ref) => {
  const [prompt, setPrompt] = useState('')
  const [isCheckpoint, setIsCheckpoint] = useState(initialIsCheckpoint)

  // 对外暴露的方法
  useImperativeHandle(ref, () => ({
    setIsCheckpoint: (value: boolean) => setIsCheckpoint(value),
    getIsCheckpoint: () => isCheckpoint
  }))

  const handleContinue = () => {
    onContinue(prompt)
  }

  const handleReject = () => {
    onReject(prompt)
  }

  return (
    <div className="processing-stage-container">
      {/* DAG渲染区域 */}
      <DagRenderer />

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
