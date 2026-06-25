import { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

let counter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((title, subtitle = '', type = 'info', timeout = 3800) => {
    const id = ++counter
    setToasts((t) => [...t, { id, title, subtitle, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), timeout)
  }, [])

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`}>
            <div>
              <strong>{t.title}</strong>
              {t.subtitle && <small>{t.subtitle}</small>}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast debe usarse dentro de ToastProvider')
  return ctx
}
