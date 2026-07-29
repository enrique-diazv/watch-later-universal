import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useDebouncedValue } from './useDebouncedValue'


describe('useDebouncedValue', () => {
  it('updates the value only after the delay', () => {
    vi.useFakeTimers()

    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 400),
      {
        initialProps: {
          value: 'ma',
        },
      },
    )

    expect(result.current).toBe('ma')

    rerender({
      value: 'matrix',
    })

    expect(result.current).toBe('ma')

    act(() => {
      vi.advanceTimersByTime(399)
    })

    expect(result.current).toBe('ma')

    act(() => {
      vi.advanceTimersByTime(1)
    })

    expect(result.current).toBe('matrix')
  })
})
