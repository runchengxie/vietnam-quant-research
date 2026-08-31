import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

const storageKey = 'quant-showcase-theme'

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = window.localStorage.getItem(storageKey)
    return saved === 'dark' ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem(storageKey, theme)
    window.dispatchEvent(new Event('themechange'))
  }, [theme])

  const nextTheme = theme === 'light' ? 'dark' : 'light'
  return (
    <button
      className="theme-toggle"
      type="button"
      aria-label={`切换到${nextTheme === 'dark' ? '深色' : '浅色'}模式`}
      onClick={() => setTheme(nextTheme)}
    >
      <span aria-hidden="true">{theme === 'light' ? '☾' : '☀'}</span>
      {theme === 'light' ? '深色模式' : '浅色模式'}
    </button>
  )
}
