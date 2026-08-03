import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'
import { LibraryPage } from './features/library/LibraryPage'
import { MediaDetailsPage } from './features/media/MediaDetailsPage'
import { SearchPage } from './features/search/SearchPage'
import { AuthPage } from './features/auth/AuthPage'
import { VerifyEmailPage } from './features/auth/VerifyEmailPage'

function App() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/verify-email"
        element={<VerifyEmailPage />}
      />
      <Route path="/" element={<SearchPage />} />

      <Route
        path="/media/:mediaType/:tmdbId"
        element={<MediaDetailsPage />}
      />

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />

      <Route
        path="/library"
        element={<LibraryPage />}
      />
    </Routes>
  )
}

export default App