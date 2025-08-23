import { useState, useRef, useEffect } from 'react'
import { api } from '@/services/api'
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Divider,
  CircularProgress,
  Chip,
  Alert,
} from '@mui/material'
import {
  Send,
  SmartToy,
  Person,
  AttachFile,
} from '@mui/icons-material'
import { format } from 'date-fns'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  attachments?: {
    contentId: string
    title: string
  }[]
}

interface ChatInterfaceProps {
  selectedContent?: {
    id: string
    title: string
  }[]
}

export function ChatInterface({ selectedContent = [] }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your AI Study Assistant. I can help you understand your study materials, answer questions, and create practice problems. What would you like to learn today?",
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [attachedContent, setAttachedContent] = useState<typeof selectedContent>([])
  const [conversationContent, setConversationContent] = useState<typeof selectedContent>([])  // Content for entire conversation
  const messagesEndRef = useRef<null | HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const isStreamingRef = useRef(false)
  const userHasScrolledUp = useRef(false)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior })
  }

  // Check if user has scrolled up from the bottom
  const checkUserScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
      // Consider user has scrolled up if they're more than 100px from bottom
      userHasScrolledUp.current = scrollHeight - scrollTop - clientHeight > 100
    }
  }

  useEffect(() => {
    // Only auto-scroll if:
    // 1. User hasn't scrolled up, OR
    // 2. A new user message was sent (not streaming)
    const lastMessage = messages[messages.length - 1]
    const isUserMessage = lastMessage?.role === 'user'
    
    if (isUserMessage) {
      // Always scroll for new user messages
      scrollToBottom()
      userHasScrolledUp.current = false
    } else if (!userHasScrolledUp.current && messages.length > 0) {
      // Only scroll for assistant messages if user hasn't scrolled up
      scrollToBottom('auto')
    }
  }, [messages])

  // Update attached content when selection changes
  useEffect(() => {
    if (selectedContent.length > 0) {
      setAttachedContent(selectedContent)
      // Also set as conversation content if this is the first attachment
      if (conversationContent.length === 0) {
        setConversationContent(selectedContent)
      }
    }
  }, [selectedContent, conversationContent.length])

  // Get CSRF token on component mount (using api instance for consistency)
  useEffect(() => {
    const getCSRFToken = async () => {
      try {
        const response = await api.get('/api/v1/csrf/token')
        if (response.data.csrf_token) {
          localStorage.setItem('csrf_token', response.data.csrf_token)
        }
      } catch (err) {
        // CSRF token fetch failed, will retry on next request
      }
    }
    getCSRFToken()
  }, [])

  const handleSend = async () => {
    if (!input.trim() && attachedContent.length === 0) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      attachments: attachedContent.length > 0 ? attachedContent.map(c => ({ contentId: c.id, title: c.title })) : undefined,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Prepare chat request - use conversation content for context continuity
      const contentToSend = attachedContent.length > 0 ? attachedContent : conversationContent
      const chatRequest = {
        messages: messages
          .filter(m => m.role === 'user' || m.role === 'assistant')
          .map(m => ({
            role: m.role,
            content: m.content
          }))
          .concat([{ role: 'user', content: input }]),
        content_ids: contentToSend.map(c => c.id),
        stream: true,
        temperature: 0.7
      }

      // Get authentication tokens
      const token = localStorage.getItem('access_token')
      const csrfToken = localStorage.getItem('csrf_token')
      
      // Validate authentication before making request
      if (!token) {
        throw new Error('Please log in to use the chat feature')
      }
      
      
      // Build complete headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
      
      // Add CSRF header if available (optional since endpoint is exempt)
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken
      }
      
      // Use fetch for streaming response
      // Note: credentials: 'include' is required for cookies but may strip Authorization header
      // Since the endpoint is CSRF-exempt, we can try without credentials
      const fetchResponse = await fetch(`${api.defaults.baseURL}/api/v1/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(chatRequest),
        credentials: 'omit'  // Try omitting credentials to preserve Authorization header
      })

      if (!fetchResponse.ok) {
        if (fetchResponse.status === 403 || fetchResponse.status === 401) {
          // Check if user is not authenticated
          const token = localStorage.getItem('access_token')
          if (!token) {
            throw new Error('Please log in to use the chat feature')
          } else {
            throw new Error('Session expired. Please log in again')
          }
        }
        throw new Error(`Chat request failed: ${fetchResponse.statusText}`)
      }

      // Handle streaming response
      const reader = fetchResponse.body?.getReader()
      const decoder = new TextDecoder()
      
      // Set streaming flag
      isStreamingRef.current = true
      
      let assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }

      // Add empty message that we'll update as chunks arrive
      setMessages(prev => [...prev, assistantMessage])

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            isStreamingRef.current = false
            break
          }

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                if (data.type === 'content') {
                  // Update the assistant message content
                  assistantMessage.content += data.content
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === assistantMessage.id 
                        ? { ...msg, content: assistantMessage.content }
                        : msg
                    )
                  )
                } else if (data.type === 'error') {
                  throw new Error(data.error)
                }
              } catch (e) {
                // Skip invalid JSON lines
              }
            }
          }
        }
      }

      // Update conversation content if new content was attached
      if (attachedContent.length > 0) {
        setConversationContent(attachedContent)
      }
      // Clear only the attached content display, not the conversation context
      setAttachedContent([])
      
    } catch (error) {
      let errorMsg = 'An error occurred while sending your message. '
      
      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          errorMsg = 'Your session has expired. Please log in again.'
        } else if (error.message.includes('403')) {
          errorMsg = 'CSRF validation failed. Please refresh the page and try again.'
        } else if (error.message.includes('Failed to fetch')) {
          errorMsg = 'Cannot connect to the backend server. Please make sure it is running on http://localhost:8000'
        } else {
          errorMsg += error.message
        }
      }
      
      setError(errorMsg)
      
      // Also add error message to chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I'm having trouble connecting to the AI service. ${errorMsg}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const removeAttachment = (index: number) => {
    setAttachedContent(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        height: '600px', 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Chat Header */}
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToy />
          AI Study Assistant
        </Typography>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ m: 1 }}>
          {error}
        </Alert>
      )}

      {/* Messages Area */}
      <Box
        ref={messagesContainerRef}
        onScroll={checkUserScroll}
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          bgcolor: 'grey.50',
        }}
      >
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              gap: 2,
              mb: 2,
              flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
            }}
          >
            <Avatar
              sx={{
                bgcolor: message.role === 'user' ? 'secondary.main' : 'primary.main',
                width: 36,
                height: 36,
              }}
            >
              {message.role === 'user' ? <Person /> : <SmartToy />}
            </Avatar>
            <Box
              sx={{
                maxWidth: '70%',
                bgcolor: message.role === 'user' ? 'secondary.light' : 'white',
                p: 2,
                borderRadius: 2,
                boxShadow: 1,
              }}
            >
              {message.attachments && message.attachments.length > 0 && (
                <Box sx={{ mb: 1 }}>
                  {message.attachments.map((attachment, index) => (
                    <Chip
                      key={index}
                      label={attachment.title}
                      size="small"
                      icon={<AttachFile />}
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              )}
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {message.content}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {format(message.timestamp, 'h:mm a')}
              </Typography>
            </Box>
          </Box>
        ))}
        
        {isLoading && (
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36 }}>
              <SmartToy />
            </Avatar>
            <Box
              sx={{
                bgcolor: 'white',
                p: 2,
                borderRadius: 2,
                boxShadow: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Thinking...
              </Typography>
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      <Divider />

      {/* Input Area */}
      <Box sx={{ p: 2 }}>
        {/* Attached Content Display */}
        {attachedContent.length > 0 && (
          <Box sx={{ mb: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {attachedContent.map((content, index) => (
              <Chip
                key={content.id}
                label={content.title}
                icon={<AttachFile />}
                onDelete={() => removeAttachment(index)}
                size="small"
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        )}

        {/* Message Input */}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              attachedContent.length > 0
                ? "Ask about the attached content..."
                : "Type your message..."
            }
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={isLoading || (!input.trim() && attachedContent.length === 0)}
            sx={{ 
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'grey.300',
              },
            }}
          >
            <Send />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  )
}