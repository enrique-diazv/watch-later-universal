import { useQuery } from '@tanstack/react-query'

import { getHealth } from './services/api'


function App() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: 1,
  })

  return (
    <main>
      <h1>Watch Later Universal</h1>

      {healthQuery.isPending && (
        <p>Conectando con el backend...</p>
      )}

      {healthQuery.isError && (
        <p>
          No fue posible conectar: {healthQuery.error.message}
        </p>
      )}

      {healthQuery.data && (
        <p>
          Backend conectado:{' '}
          <strong>{healthQuery.data.status}</strong>
          {' — '}
          {healthQuery.data.service}
        </p>
      )}
    </main>
  )
}

export default App