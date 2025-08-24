import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Box, Container, Typography, Paper, Button, AppBar, Toolbar, IconButton, Menu, MenuItem, useMediaQuery, useTheme, Tabs, Tab, Badge } from '@mui/material'
import { Routes, Route, Link, Navigate } from 'react-router-dom'
import { AccountCircle, ChatBubbleOutline, FolderOpen } from '@mui/icons-material'
import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { LoginForm, RegisterForm, ProtectedRoute } from './components/auth'
import { ContentUpload, ContentList, ContentSelector } from './components/content'
import { ChatInterface } from './components/chat'
import api from './services/api'

// Create a theme instance
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
})

function AppContent() {
  const { user, logout } = useAuth()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    handleClose()
    await logout()
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>
              AI Study Architect
            </Link>
          </Typography>
          
          {user && (
            <div>
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircle />
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem disabled>
                  <Typography variant="body2" color="text.secondary">
                    {user.username}
                  </Typography>
                </MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </div>
          )}
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box component="main" sx={{ flex: 1, py: 4 }}>
        <Container maxWidth="lg">
          <Routes>
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/study"
              element={
                <ProtectedRoute>
                  <StudyPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/content"
              element={
                <ProtectedRoute>
                  <ContentPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/practice"
              element={
                <ProtectedRoute>
                  <PracticePage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Container>
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          bgcolor: 'background.paper',
          py: 2,
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            © 2025 AI Study Architect - CS50 Final Project
          </Typography>
        </Container>
      </Box>
    </Box>
  )
}

function App() {
  // Fetch CSRF token on app load
  useEffect(() => {
    api.get('/api/v1/csrf/token').catch(() => {
      // Silently handle CSRF token fetch failure
      // The interceptor will retry on actual API calls
    })
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  )
}

// Placeholder pages
function HomePage() {
  const { user } = useAuth()
  
  return (
    <Paper elevation={3} sx={{ p: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Welcome back, {user?.full_name || user?.username}!
      </Typography>
      <Typography variant="body1" paragraph>
        Your personalized AI-powered learning companion. Get started by uploading
        your study materials or creating a new study session.
      </Typography>
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button variant="contained" component={Link} to="/study" size="large">
          Start AI Study Session
        </Button>
        <Button variant="outlined" component={Link} to="/content">
          Manage Content
        </Button>
      </Box>
    </Paper>
  )
}

function StudyPage() {
  const [selectedContent, setSelectedContent] = useState<{ id: string; title: string }[]>([])
  const [mobileTab, setMobileTab] = useState(1) // Default to Chat tab
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')) // Mobile: < 600px
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md')) // Tablet: 600-960px

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setMobileTab(newValue)
  }

  // Mobile and Tablet layout with tabs
  if (isMobile || isTablet) {
    return (
      <Box sx={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
        {/* Tab navigation for mobile/tablet */}
        <Paper sx={{ borderRadius: 0 }}>
          <Tabs 
            value={mobileTab} 
            onChange={handleTabChange} 
            variant="fullWidth"
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab 
              icon={<Badge badgeContent={selectedContent.length} color="primary"><FolderOpen /></Badge>}
              label="Materials" 
            />
            <Tab 
              icon={<ChatBubbleOutline />}
              label="Chat" 
            />
          </Tabs>
        </Paper>

        {/* Tab content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: isTablet ? 3 : 2 }}>
          {mobileTab === 0 && (
            <Box sx={{ maxWidth: isTablet ? 600 : '100%', mx: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Select Study Materials (Optional)
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Add content to discuss with your AI tutor, or chat freely without materials
              </Typography>
              <ContentSelector 
                onSelectionChange={setSelectedContent} 
                selectedContent={selectedContent}
              />
              {selectedContent.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Button 
                    variant="contained" 
                    fullWidth 
                    onClick={() => setMobileTab(1)}
                    startIcon={<ChatBubbleOutline />}
                  >
                    Back to Chat ({selectedContent.length} file{selectedContent.length !== 1 ? 's' : ''} selected)
                  </Button>
                </Box>
              )}
            </Box>
          )}
          {mobileTab === 1 && (
            <Box sx={{ maxWidth: isTablet ? 800 : '100%', mx: 'auto', height: '100%' }}>
              <ChatInterface selectedContent={selectedContent} />
            </Box>
          )}
        </Box>
      </Box>
    )
  }

  // Desktop layout - side by side
  return (
    <Box sx={{ display: 'flex', gap: 3, height: 'calc(100vh - 200px)' }}>
      {/* Left side - Content Selection */}
      <Paper elevation={3} sx={{ 
        flex: '0 0 350px', 
        p: 2, 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <Typography variant="h6" gutterBottom>
          Study Materials (Optional)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Add content to enhance your chat, or start chatting directly
        </Typography>
        <Box sx={{ flex: 1, minHeight: 0 }}>
          <ContentSelector 
            onSelectionChange={setSelectedContent} 
            selectedContent={selectedContent}
          />
        </Box>
      </Paper>

      {/* Right side - Chat Interface (Primary) */}
      <Box sx={{ flex: 1 }}>
        <ChatInterface selectedContent={selectedContent} />
      </Box>
    </Box>
  )
}

function ContentPage() {
  const [activeTab, setActiveTab] = useState<'upload' | 'list'>('list')
  const [refreshList, setRefreshList] = useState(0)

  const handleUploadComplete = () => {
    setActiveTab('list')
    setRefreshList(prev => prev + 1)
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button
          variant={activeTab === 'list' ? 'contained' : 'outlined'}
          onClick={() => setActiveTab('list')}
        >
          My Content
        </Button>
        <Button
          variant={activeTab === 'upload' ? 'contained' : 'outlined'}
          onClick={() => setActiveTab('upload')}
        >
          Upload New
        </Button>
      </Box>

      {activeTab === 'upload' ? (
        <ContentUpload onUploadComplete={handleUploadComplete} />
      ) : (
        <ContentList key={refreshList} />
      )}
    </Box>
  )
}

function PracticePage() {
  return (
    <Paper elevation={3} sx={{ p: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Practice Problems
      </Typography>
      <Typography variant="body1">
        AI-generated practice problems will be implemented here.
      </Typography>
    </Paper>
  )
}

export default App