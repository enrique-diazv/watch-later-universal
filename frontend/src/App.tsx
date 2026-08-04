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
import { ForgotPasswordPage } from './features/auth/ForgotPasswordPage'
import { ResetPasswordPage } from './features/auth/ResetPasswordPage'
function App() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/forgot-password"
        element={<ForgotPasswordPage />}
      />
      <Route
        path="/reset-password"
        element={<ResetPasswordPage />}
      />
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