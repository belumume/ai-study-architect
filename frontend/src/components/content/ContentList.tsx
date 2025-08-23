import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Tooltip,
  Card,
  CardContent,
  CardActions,
  Grid,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  MoreVert,
  Delete,
  Download,
  Search,
  PictureAsPdf,
  VideoLibrary,
  AudioFile,
  Description,
  Image as ImageIcon,
} from '@mui/icons-material'
import { format } from 'date-fns'
import api from '../../services/api'

interface Content {
  id: string
  title: string
  content_type: string
  subject: string
  description?: string
  tags?: string[]
  file_path: string
  file_size: number
  mime_type: string
  created_at: string
  updated_at: string
}

export function ContentList() {
  const [contents, setContents] = useState<Content[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedContent, setSelectedContent] = useState<Content | null>(null)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [contentToDelete, setContentToDelete] = useState<Content | null>(null)
  
  // Responsive design hooks
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  useEffect(() => {
    fetchContents()
  }, [])

  const fetchContents = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/v1/content/')
      // Ensure we have an array
      const data = Array.isArray(response.data) ? response.data : []
      setContents(data)
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch content')
      setContents([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, content: Content) => {
    setAnchorEl(event.currentTarget)
    setSelectedContent(content)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedContent(null)
  }

  const handleDelete = async () => {
    if (!contentToDelete) return

    try {
      await api.delete(`/api/v1/content/${contentToDelete.id}`)
      setContents(prev => prev.filter(c => c.id !== contentToDelete.id))
      setDeleteDialogOpen(false)
      setContentToDelete(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete content')
    }
  }

  const handleDeleteClick = () => {
    setContentToDelete(selectedContent)
    setDeleteDialogOpen(true)
    handleMenuClose()
  }

  const handleDownload = async () => {
    if (!selectedContent) return

    try {
      const response = await api.get(`/api/v1/content/${selectedContent.id}/download`, {
        responseType: 'blob',
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', selectedContent.title)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError('Failed to download file')
    }
    handleMenuClose()
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return <ImageIcon />
    if (mimeType.startsWith('video/')) return <VideoLibrary />
    if (mimeType.startsWith('audio/')) return <AudioFile />
    if (mimeType.includes('pdf')) return <PictureAsPdf />
    return <Description />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const getContentTypeColor = (type: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    const colorMap: Record<string, "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"> = {
      lecture_notes: 'primary',
      textbook: 'secondary',
      assignment: 'error',
      research_paper: 'info',
      video_lecture: 'success',
      audio_recording: 'warning',
      practice_problems: 'default',
    }
    return colorMap[type] || 'default'
  }

  const filteredContents = contents.filter(content => {
    const searchLower = searchTerm.toLowerCase()
    return (
      content.title?.toLowerCase().includes(searchLower) ||
      content.subject?.toLowerCase().includes(searchLower) ||
      content.description?.toLowerCase().includes(searchLower) ||
      content.tags?.some(tag => tag?.toLowerCase().includes(searchLower))
    )
  })

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
      <Box sx={{ 
        mb: 3, 
        display: 'flex', 
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'space-between', 
        alignItems: { xs: 'stretch', sm: 'center' },
        gap: 2 
      }}>
        <Typography variant={isMobile ? "h6" : "h5"} component="h2">
          My Study Materials
        </Typography>
        <TextField
          placeholder="Search content..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
          fullWidth={isMobile}
          sx={{ maxWidth: { xs: '100%', sm: 300 } }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {filteredContents.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No content uploaded yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Start by uploading your study materials
          </Typography>
        </Box>
      ) : (
        <>
          {/* Mobile/Tablet Card Layout */}
          {isTablet ? (
            <Grid container spacing={2}>
              {filteredContents
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((content) => (
                  <Grid item xs={12} sm={6} key={content.id}>
                    <Card 
                      elevation={2}
                      sx={{ 
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        '&:hover': {
                          elevation: 4,
                          transform: 'translateY(-2px)',
                          transition: 'all 0.3s'
                        }
                      }}
                    >
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                          {getFileIcon(content.mime_type)}
                          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                            <Typography variant="h6" noWrap sx={{ fontSize: '1.1rem' }}>
                              {content.title}
                            </Typography>
                            {content.description && (
                              <Typography 
                                variant="body2" 
                                color="text.secondary"
                                sx={{ 
                                  display: '-webkit-box',
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden'
                                }}
                              >
                                {content.description}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                        
                        <Box sx={{ mt: 2 }}>
                          <Chip
                            label={content.content_type.replace('_', ' ')}
                            size="small"
                            color={getContentTypeColor(content.content_type)}
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {formatFileSize(content.file_size)} • {format(new Date(content.created_at), 'MMM d, yyyy')}
                          </Typography>
                          {content.subject && (
                            <Typography variant="body2" color="text.secondary">
                              Subject: {content.subject}
                            </Typography>
                          )}
                        </Box>
                      </CardContent>
                      
                      <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, content)}
                          aria-label="More actions"
                        >
                          <MoreVert />
                        </IconButton>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
            </Grid>
          ) : (
            /* Desktop Table Layout */
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Title</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Subject</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Uploaded</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredContents
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((content) => (
                      <TableRow key={content.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Tooltip title={content.mime_type}>
                              {getFileIcon(content.mime_type)}
                            </Tooltip>
                            <Box>
                              <Typography variant="body2">{content.title}</Typography>
                              {content.description && (
                                <Typography variant="caption" color="text.secondary">
                                  {content.description}
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={content.content_type.replace('_', ' ')}
                            size="small"
                            color={getContentTypeColor(content.content_type)}
                          />
                        </TableCell>
                        <TableCell>{content.subject || '-'}</TableCell>
                        <TableCell>{formatFileSize(content.file_size)}</TableCell>
                        <TableCell>
                          <Tooltip title={format(new Date(content.created_at), 'PPpp')}>
                            <span>{format(new Date(content.created_at), 'MMM d, yyyy')}</span>
                          </Tooltip>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, content)}
                          >
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredContents.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleDownload}>
          <Download sx={{ mr: 1 }} fontSize="small" />
          Download
        </MenuItem>
        <MenuItem onClick={handleDeleteClick}>
          <Delete sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Content?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{contentToDelete?.title}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  )
}