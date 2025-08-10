import { useState, useEffect } from 'react'
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  CircularProgress,
  Alert,
  Typography,
  TextField,
  InputAdornment,
} from '@mui/material'
import {
  PictureAsPdf,
  VideoLibrary,
  AudioFile,
  Description,
  Image as ImageIcon,
  Search,
} from '@mui/icons-material'
import api from '../../services/api'

interface Content {
  id: string
  title: string
  content_type: string
  mime_type: string
  subject?: string
  created_at: string
}

interface ContentSelectorProps {
  onSelectionChange: (selected: { id: string; title: string }[]) => void
  selectedContent: { id: string; title: string }[]
}

export function ContentSelector({ onSelectionChange, selectedContent }: ContentSelectorProps) {
  const [contents, setContents] = useState<Content[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchContents()
  }, [])

  const fetchContents = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/v1/content/')
      const data = Array.isArray(response.data) ? response.data : []
      setContents(data)
      setError('')
    } catch (err: any) {
      setError('Failed to load content')
      setContents([])
    } finally {
      setLoading(false)
    }
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) return <PictureAsPdf color="error" />
    if (mimeType.includes('video')) return <VideoLibrary color="primary" />
    if (mimeType.includes('audio')) return <AudioFile color="secondary" />
    if (mimeType.includes('image')) return <ImageIcon color="success" />
    return <Description color="action" />
  }

  const handleToggle = (content: Content) => {
    const currentIndex = selectedContent.findIndex(item => item.id === content.id)
    const newSelected = [...selectedContent]

    if (currentIndex === -1) {
      newSelected.push({ id: content.id, title: content.title })
    } else {
      newSelected.splice(currentIndex, 1)
    }

    onSelectionChange(newSelected)
  }

  const filteredContents = contents.filter(content =>
    content.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    content.subject?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} />
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  if (contents.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
        No content uploaded yet
      </Typography>
    )
  }

  return (
    <Box>
      <TextField
        fullWidth
        size="small"
        placeholder="Search content..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search fontSize="small" />
            </InputAdornment>
          ),
        }}
      />

      <List dense sx={{ maxHeight: 400, overflow: 'auto' }}>
        {filteredContents.map((content) => {
          const isSelected = selectedContent.some(item => item.id === content.id)
          return (
            <ListItem key={content.id} disablePadding>
              <ListItemButton 
                onClick={() => handleToggle(content)}
                dense
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={isSelected}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {getFileIcon(content.mime_type)}
                </ListItemIcon>
                <ListItemText 
                  primary={content.title}
                  secondary={content.subject}
                  primaryTypographyProps={{
                    variant: 'body2',
                    noWrap: true,
                  }}
                  secondaryTypographyProps={{
                    variant: 'caption',
                    noWrap: true,
                  }}
                />
              </ListItemButton>
            </ListItem>
          )
        })}
      </List>

      {selectedContent.length > 0 && (
        <Typography variant="caption" color="primary" sx={{ mt: 1, display: 'block' }}>
          {selectedContent.length} file{selectedContent.length > 1 ? 's' : ''} selected
        </Typography>
      )}
    </Box>
  )
}