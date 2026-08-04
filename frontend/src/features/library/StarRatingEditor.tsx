import {
  useEffect,
  useId,
  useState,
} from 'react'

import styles from './StarRatingEditor.module.css'


const STAR_INDEXES = [0, 1, 2, 3, 4]

const STAR_PATH = (
  'M12 2.5 14.9 8.38 21.39 9.32 ' +
  '16.7 13.9 17.8 20.37 12 17.32 ' +
  '6.2 20.37 7.31 13.9 2.61 9.32 ' +
  '9.1 8.38 12 2.5Z'
)

interface StarRatingEditorProps {
  value: number | null
  disabled?: boolean
  onSave: (
    value: number | null,
  ) => Promise<void>
}


function toStarRating(
  value: number | null,
): number {
  if (value === null) {
    return 0
  }

  return Math.min(
    Math.max(Math.round(value) / 2, 0),
    5,
  )
}


function getRatingLabel(rating: number): string {
  if (rating === 0) {
    return 'Sin calificación'
  }

  return `${rating} de 5 estrellas`
}


export function StarRatingEditor({
  value,
  disabled = false,
  onSave,
}: StarRatingEditorProps) {
  const instanceId = useId().replace(
    /:/g,
    '',
  )
  const storedRating = toStarRating(value)
  const [isEditing, setIsEditing] = useState(false)
  const [draftRating, setDraftRating] = useState(
    storedRating,
  )

  useEffect(() => {
    if (!isEditing) {
      setDraftRating(storedRating)
    }
  }, [isEditing, storedRating])

  const displayedRating = (
    isEditing
      ? draftRating
      : storedRating
  )

  function startEditing() {
    setDraftRating(storedRating)
    setIsEditing(true)
  }

  function decreaseRating() {
    setDraftRating((currentRating) =>
      Math.max(0, currentRating - 0.5),
    )
  }

  function increaseRating() {
    setDraftRating((currentRating) =>
      Math.min(5, currentRating + 0.5),
    )
  }

  async function saveRating() {
        const newValue = (
            draftRating === 0
            ? null
            : draftRating * 2
        )

        try {
            await onSave(newValue)
            setIsEditing(false)
        } catch {
            // El componente padre mostrará el error.
        }
    }

  return (
    <section
      className={styles.editor}
      aria-label="Tu calificación"
    >
      <p className={styles.label}>
        Tu calificación
      </p>

      <div
        className={styles.ratingRow}
        data-editing={isEditing}
      >
        {isEditing && (
          <button
            className={styles.arrowButton}
            type="button"
            disabled={
              disabled || draftRating === 0
            }
            aria-label="Reducir calificación"
            onClick={decreaseRating}
          >
            <span aria-hidden="true">◀</span>
          </button>
        )}

        <div
          className={styles.stars}
          role={isEditing ? 'group' : 'img'}
          aria-label={getRatingLabel(
            displayedRating,
          )}
        >
          {STAR_INDEXES.map((starIndex) => {
            const starValue = (
              displayedRating - starIndex
            )
            const fillPercentage = (
              Math.min(
                Math.max(starValue, 0),
                1,
              ) * 100
            )

            const clipId = (
                `${instanceId}-star-${starIndex}`
            )

            return (
                <span
                    className={styles.star}
                    key={starIndex}
                >
                    <svg
                    className={styles.starGraphic}
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                    >
                    <defs>
                        <clipPath id={clipId}>
                        <rect
                            x="0"
                            y="0"
                            width={
                            24 * fillPercentage / 100
                            }
                            height="24"
                        />
                        </clipPath>
                    </defs>

                    <path
                        className={styles.emptyStar}
                        d={STAR_PATH}
                    />
                    <path
                        className={styles.filledStar}
                        d={STAR_PATH}
                        clipPath={`url(#${clipId})`}
                    />
                    </svg>

                    {isEditing && (
                    <>
                        <button
                        className={
                            `${styles.starButton} ` +
                            styles.leftHalf
                        }
                        type="button"
                        disabled={disabled}
                        aria-label={
                            `Calificar con ` +
                            `${starIndex + 0.5} estrellas`
                        }
                        onClick={() =>
                            setDraftRating(
                            starIndex + 0.5,
                            )
                        }
                        />
                        <button
                        className={
                            `${styles.starButton} ` +
                            styles.rightHalf
                        }
                        type="button"
                        disabled={disabled}
                        aria-label={
                            `Calificar con ` +
                            `${starIndex + 1} estrellas`
                        }
                        onClick={() =>
                            setDraftRating(
                            starIndex + 1,
                            )
                        }
                        />
                    </>
                    )}
                </span>
            )
          })}
        </div>

        {isEditing && (
          <button
            className={styles.arrowButton}
            type="button"
            disabled={
              disabled || draftRating === 5
            }
            aria-label="Aumentar calificación"
            onClick={increaseRating}
          >
            <span aria-hidden="true">▶</span>
          </button>
        )}

        <button
          className={styles.actionButton}
          type="button"
          disabled={disabled}
          aria-label={
            isEditing
              ? 'Guardar calificación'
              : 'Editar calificación'
          }
          onClick={
            isEditing
                ? () => void saveRating()
                : startEditing
           }
        >
          {isEditing ? (
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M5 4h12l2 2v14H5V4Zm3 0v6h8V4M8 20v-6h8v6" />
            </svg>
          ) : (
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="m4 16-1 5 5-1L19 9l-4-4L4 16Zm9-9 4 4M15 5l2-2 4 4-2 2" />
            </svg>
          )}
        </button>
      </div>

      <span
        className={styles.screenReaderStatus}
        aria-live="polite"
      >
        {getRatingLabel(displayedRating)}
      </span>
    </section>
  )
}