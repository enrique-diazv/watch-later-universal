import {
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  describe,
  expect,
  it,
  vi,
} from 'vitest'

import { StarRatingEditor } from './StarRatingEditor'


describe('StarRatingEditor', () => {
  it('decreases by half a star and saves', async () => {
    const onSave = vi.fn().mockResolvedValue(
      undefined,
    )
    const user = userEvent.setup()

    render(
      <StarRatingEditor
        value={8}
        onSave={onSave}
      />,
    )

    expect(
      screen.getByRole('img', {
        name: '4 de 5 estrellas',
      }),
    ).toBeVisible()

    await user.click(
      screen.getByRole('button', {
        name: 'Editar calificación',
      }),
    )
    await user.click(
      screen.getByRole('button', {
        name: 'Reducir calificación',
      }),
    )

    expect(
      screen.getByRole('group', {
        name: '3.5 de 5 estrellas',
      }),
    ).toBeVisible()

    await user.click(
      screen.getByRole('button', {
        name: 'Guardar calificación',
      }),
    )

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(7)
    })
  })

  it('selects the left half of a star', async () => {
    const onSave = vi.fn().mockResolvedValue(
      undefined,
    )
    const user = userEvent.setup()

    render(
      <StarRatingEditor
        value={null}
        onSave={onSave}
      />,
    )

    await user.click(
      screen.getByRole('button', {
        name: 'Editar calificación',
      }),
    )
    await user.click(
      screen.getByRole('button', {
        name: 'Calificar con 2.5 estrellas',
      }),
    )
    await user.click(
      screen.getByRole('button', {
        name: 'Guardar calificación',
      }),
    )

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(5)
    })
  })
})