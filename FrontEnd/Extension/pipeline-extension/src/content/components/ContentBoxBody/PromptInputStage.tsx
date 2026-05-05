import React, { useState } from 'react'
import './PromptInputStage.css'

interface PromptInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

const PromptInput: React.FC<PromptInputProps> = ({ value, onChange, placeholder = '这里是提示词输入框' }) => {
  return (
    <div className="prompt-input-wrapper">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="prompt-input-textarea"
      />
    </div>
  )
}

interface SubmitButtonProps {
  onClick: () => void
  disabled?: boolean
  text?: string
}

const SubmitButton: React.FC<SubmitButtonProps> = ({ onClick, disabled = false, text = '确认' }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="submit-btn"
    >
      <span className="submit-btn-text">{text}</span>
    </button>
  )
}

export interface PromptInputStageProps {
  onSubmit?: (prompt: string) => void
  initialValue?: string
  placeholder?: string
  submitText?: string
}

export const PromptInputStage: React.FC<PromptInputStageProps> = ({
  onSubmit,
  initialValue = '',
  placeholder,
  submitText
}) => {
  const [prompt, setPrompt] = useState(initialValue)

  const submitForm = () => {
    if (prompt.trim() && onSubmit) {
      onSubmit(prompt.trim())
    }
  }

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
  }

  return (
    <div className="prompt-input-stage-container">
      <form onSubmit={handleFormSubmit} style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1 }}>
          <PromptInput
            value={prompt}
            onChange={setPrompt}
            placeholder={placeholder}
          />
        </div>
        <div style={{ flexShrink: 0 }}>
          <SubmitButton
            onClick={submitForm}
            disabled={!prompt.trim()}
            text={submitText}
          />
        </div>
      </form>
    </div>
  )
}
