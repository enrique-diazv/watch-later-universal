import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { MediaDetailsPage } from './features/media/MediaDetailsPage'
import { SearchPage } from './features/search/SearchPage'


function App() {
  return (
    <Routes>
      <Route path="/" element={<SearchPage />} />

      <Route
        path="/media/:mediaType/:tmdbId"
        element={<MediaDetailsPage />}
      />

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  )
}

export default App