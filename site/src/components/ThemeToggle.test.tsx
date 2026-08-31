import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { App } from '../App'

describe('主题切换', () => {
  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme')
    window.localStorage.clear()
  })

  it('默认使用浅色主题，并允许切换到深色主题', () => {
    render(<App />)

    expect(document.documentElement.dataset.theme).toBe('light')
    fireEvent.click(screen.getByRole('button', { name: '切换到深色模式' }))

    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(screen.getByRole('button', { name: '切换到浅色模式' })).toBeInTheDocument()
  })
})
