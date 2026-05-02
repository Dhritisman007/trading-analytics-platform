import { useState, useEffect } from 'react'

export const useTheme = () => {
  const [isDark, setIsDark] = useState(() => {
    // Check localStorage first, then system preference
    const saved = localStorage.getItem('theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.setAttribute('data-theme', 'dark')
      localStorage.setItem('theme', 'dark')
    } else {
      root.setAttribute('data-theme', 'light')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  const toggle = () => setIsDark((prev) => !prev)

  return { isDark, toggle }
}
