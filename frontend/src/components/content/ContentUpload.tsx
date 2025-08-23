import { useState, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Stack,
  useTheme,
  useMediaQuery,
  Grid,
} from '@mui/material'
import {
  CloudUpload,
  Description,
  PictureAsPdf,
  VideoLibrary,
  AudioFile,
  Delete,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import api from '../../services/api'

interface FileUploadStatus {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress?: number
  error?: string
  contentId?: string
}

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'image/*': ['.png', '.jpg', '.jpeg'],
  'video/*': ['.mp4', '.avi', '.mov'],
  'audio/*': ['.mp3', '.wav', '.m4a'],
  'text/*': ['.txt', '.md'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
}

const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB

export function ContentUpload({ onUploadComplete }: { onUploadComplete?: () => void }) {
  const [files, setFiles] = useState<FileUploadStatus[]>([])
  const [contentType, setContentType] = useState<string>('document')
  const [subject, setSubject] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [tags, setTags] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  
  // Responsive design hooks
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  // const isTablet = useMediaQuery(theme.breakpoints.down('md'))

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      status: 'pending' as const,
    }))
    setFiles(prev => [...prev, ...newFiles])
    setError('')
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  })

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const getFileIcon = (file: File) => {
    const type = file.type
    if (type.startsWith('image/')) return <PictureAsPdf color="primary" />
    if (type.startsWith('video/')) return <VideoLibrary color="primary" />
    if (type.startsWith('audio/')) return <AudioFile color="primary" />
    if (type.includes('pdf')) return <PictureAsPdf color="error" />
    return <Description color="action" />
  }

  const getContentTypeFromFile = (file: File): string => {
    const type = file.type.toLowerCase()
    const name = file.name.toLowerCase()
    
    if (type.includes('pdf') || name.endsWith('.pdf')) return 'pdf'
    if (type.includes('image') || name.match(/\.(jpg|jpeg|png|gif)$/)) return 'image'
    if (type.includes('video') || name.match(/\.(mp4|avi|mov|webm)$/)) return 'video'
    if (type.includes('audio') || name.match(/\.(mp3|wav|m4a|ogg)$/)) return 'audio'
    if (type.includes('presentation') || name.match(/\.(ppt|pptx)$/)) return 'presentation'
    if (type.includes('word') || name.match(/\.(doc|docx)$/) || 
        type.includes('text') || name.match(/\.(txt|md)$/)) return 'document'
    
    // Default to document for unknown types
    return 'document'
  }

  const uploadFiles = async () => {
    if (files.length === 0) {
      setError('Please select at least one file')
      return
    }

    setUploading(true)
    setError('')

    // Update all files to uploading status
    setFiles(prev =>
      prev.map(f => ({ ...f, status: 'uploading', progress: 0 }))
    )

    let successfulUploads = 0

    // Upload files sequentially
    for (let i = 0; i < files.length; i++) {
      const fileStatus = files[i]
      const formData = new FormData()
      formData.append('file', fileStatus.file)
      
      // Auto-detect content type from file or use selected type
      const detectedType = getContentTypeFromFile(fileStatus.file)
      formData.append('content_type', detectedType)
      
      formData.append('title', fileStatus.file.name)
      // Always append these fields, even if empty
      formData.append('subject', subject || '')
      formData.append('description', description || '')
      formData.append('tags', tags || '')

      try {
        
        const response = await api.post('/api/v1/content/upload', formData, {
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0
            setFiles(prev =>
              prev.map((f, idx) =>
                idx === i ? { ...f, progress } : f
              )
            )
          },
        })

        setFiles(prev =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: 'success', progress: 100, contentId: response.data.id }
              : f
          )
        )
        successfulUploads++
      } catch (err: any) {
        
        let errorMessage = 'Upload failed'
        
        // Handle different error response formats
        if (err.response?.data?.detail) {
          // Handle array of validation errors
          if (Array.isArray(err.response.data.detail)) {
            errorMessage = err.response.data.detail.map((e: any) => 
              typeof e === 'string' ? e : e.msg || 'Validation error'
            ).join(', ')
          } else if (typeof err.response.data.detail === 'string') {
            errorMessage = err.response.data.detail
          } else if (typeof err.response.data.detail === 'object' && err.response.data.detail.msg) {
            errorMessage = err.response.data.detail.msg
          }
        } else if (err.response?.data?.error) {
          // Handle rate limit error format
          errorMessage = err.response.data.error
        }
        
        // Add specific handling for different error types
        if (err.response?.status === 429) {
          errorMessage = 'Upload limit reached. Please wait a minute before uploading more files.'
        } else if (err.response?.status === 409) {
          errorMessage = 'File already exists in your library'
        }
        
        setFiles(prev =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: 'error', error: errorMessage }
              : f
          )
        )
      }
    }

    setUploading(false)
    
    if (successfulUploads > 0) {
      // Show success message
      setSuccess(`Successfully uploaded ${successfulUploads} file${successfulUploads > 1 ? 's' : ''}`)
      
      // Wait a moment for user to see the success status, then clear
      setTimeout(() => {
        // Clear the file list after successful upload
        setFiles([])
        // Reset form fields
        setSubject('')
        setDescription('')
        setTags('')
        // Reset the content type to default
        setContentType('document')
        // Clear success message
        setSuccess('')
        // Call the parent callback which will switch to content list view
        if (onUploadComplete) {
          onUploadComplete()
        }
      }, 1500) // Wait 1.5 seconds before clearing
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
      <Typography variant={isMobile ? "h6" : "h5"} component="h2" gutterBottom>
        Upload Study Materials
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Content Type</InputLabel>
            <Select
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              label="Content Type"
              size={isMobile ? "small" : "medium"}
            >
              <MenuItem value="pdf">PDF Document</MenuItem>
              <MenuItem value="document">Text Document (Word, TXT, Markdown)</MenuItem>
              <MenuItem value="presentation">Presentation (PowerPoint)</MenuItem>
              <MenuItem value="image">Image (JPG, PNG)</MenuItem>
              <MenuItem value="video">Video Lecture</MenuItem>
              <MenuItem value="audio">Audio Recording</MenuItem>
              <MenuItem value="note">Text Note</MenuItem>
            </Select>
            <FormHelperText>Content type will be auto-detected from file extension</FormHelperText>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Subject (Optional)"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            helperText="e.g., Computer Science, Mathematics, Biology"
            size={isMobile ? "small" : "medium"}
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            rows={isMobile ? 2 : 3}
            helperText="Optional: Describe the content"
            size={isMobile ? "small" : "medium"}
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Tags"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            helperText="Optional: Comma-separated tags (e.g., midterm, chapter3, algorithms)"
            size={isMobile ? "small" : "medium"}
          />
        </Grid>
      </Grid>

      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.400',
          borderRadius: 2,
          p: { xs: 3, sm: 4 },
          textAlign: 'center',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.3s',
          minHeight: { xs: 150, sm: 200 },
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: { xs: 36, sm: 48 }, color: 'action.active', mb: 2 }} />
        <Typography variant={isMobile ? "body1" : "h6"} gutterBottom>
          {isDragActive
            ? 'Drop the files here...'
            : isMobile ? 'Tap to upload files' : 'Drag & drop files here, or click to select'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
          Supported formats: PDF, Images, Videos, Audio, Text, Word, PowerPoint
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Maximum file size: 100MB
        </Typography>
      </Box>

      {files.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Selected Files ({files.length})
          </Typography>
          <List>
            {files.map((fileStatus, index) => (
              <ListItem
                key={index}
                secondaryAction={
                  fileStatus.status === 'pending' && !uploading ? (
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => removeFile(index)}
                    >
                      <Delete />
                    </IconButton>
                  ) : fileStatus.status === 'success' ? (
                    <CheckCircle color="success" />
                  ) : fileStatus.status === 'error' ? (
                    <ErrorIcon color="error" />
                  ) : null
                }
              >
                <ListItemIcon>{getFileIcon(fileStatus.file)}</ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                        {fileStatus.file.name}
                      </Typography>
                      <Chip
                        label={formatFileSize(fileStatus.file.size)}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    fileStatus.status === 'uploading' ? (
                      <LinearProgress
                        variant="determinate"
                        value={fileStatus.progress || 0}
                        sx={{ mt: 1 }}
                      />
                    ) : fileStatus.error ? (
                      <Typography variant="caption" color="error">
                        {fileStatus.error}
                      </Typography>
                    ) : null
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
          onClick={uploadFiles}
          disabled={uploading || files.length === 0}
          fullWidth
        >
          {uploading ? 'Uploading...' : 'Upload Files'}
        </Button>
        {files.length > 0 && !uploading && (
          <Button
            variant="outlined"
            color="error"
            onClick={() => setFiles([])}
          >
            Clear All
          </Button>
        )}
      </Stack>
    </Paper>
  )
}