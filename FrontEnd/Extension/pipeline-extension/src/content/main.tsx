import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'

console.log('[CRXJS] Content script loaded!')

const container = document.createElement('div')
container.id = 'crxjs-app'
container.className = 'crx-root'
document.body.appendChild(container)
createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
