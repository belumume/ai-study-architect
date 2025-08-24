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
  useTheme,
  useMediaQuery,
  Fab,
  Badge,
  Zoom,
} from '@mui/material'
import {
  Send,
  SmartToy,
  Person,
  AttachFile,
  Stop,
  KeyboardArrowDown,
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
  const scrollAnimationFrame = useRef<number | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  
  // Mobile and tablet detection
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'))

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (!userHasScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior })
    }
  }

  // Check if user has scrolled up from the bottom
  const checkUserScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight
      
      // More sensitive detection during streaming
      const threshold = isStreamingRef.current ? 30 : 50
      
      // If user scrolled up, set the flag
      if (distanceFromBottom > threshold) {
        userHasScrolledUp.current = true
        setShowScrollToBottom(true)
        // Don't increment unread count here - only when new content arrives
      }
      // Only clear the flag if very close to bottom and not streaming
      else if (distanceFromBottom < 5 && !isStreamingRef.current) {
        userHasScrolledUp.current = false
        setShowScrollToBottom(false)
        setUnreadCount(0)
      }
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

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    isStreamingRef.current = false
    setIsLoading(false)
  }

  const handleScrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
      setShowScrollToBottom(false)
      setUnreadCount(0)
      userHasScrolledUp.current = false
    }
  }

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

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController()

    // Declare assistantMessage here so it's accessible in catch block
    let assistantMessage: Message | null = null

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
        stream: true,  // Re-enable streaming for better UX
        temperature: 0.7
      }

      // Get CSRF token (authentication is handled by httpOnly cookies)
      const csrfToken = localStorage.getItem('csrf_token')
      
      
      // Build complete headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      
      // Add CSRF header if available (optional since endpoint is exempt)
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken
      }
      
      // Use fetch for streaming response with abort signal
      // credentials: 'include' is required to send httpOnly cookies
      const chatUrl = api.defaults.baseURL ? `${api.defaults.baseURL}/api/v1/chat/` : '/api/v1/chat/'
      const fetchResponse = await fetch(chatUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(chatRequest),
        credentials: 'include',  // Send cookies with request
        signal: abortControllerRef.current.signal
      })

      if (!fetchResponse.ok) {
        if (fetchResponse.status === 403 || fetchResponse.status === 401) {
          // Authentication or CSRF error
          if (fetchResponse.status === 401) {
            throw new Error('Your session has expired. Please log in again.')
          } else {
            throw new Error('CSRF validation failed. Please refresh the page.')
          }
        }
        throw new Error(`Chat request failed: ${fetchResponse.statusText}`)
      }

      // Check if response is streaming or not
      const contentType = fetchResponse.headers.get('content-type')
      const isStreaming = contentType?.includes('text/event-stream')
      
      if (!isStreaming) {
        // Handle non-streaming response
        const data = await fetchResponse.json()
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.message.content,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage as Message])
        userHasScrolledUp.current = false
      } else {
        // Handle streaming response
        const reader = fetchResponse.body?.getReader()
        const decoder = new TextDecoder()
        
        // Set streaming flag and reset user scroll flag for new response
        isStreamingRef.current = true
        userHasScrolledUp.current = false  // Reset for new message
        
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '',
          timestamp: new Date(),
        }

        // Add empty message that we'll update as chunks arrive
        setMessages(prev => [...prev, assistantMessage as Message])

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
                
                if (data.type === 'content' && assistantMessage) {
                  // Update the assistant message content
                  const isFirstChunk = assistantMessage.content === ''
                  assistantMessage.content += data.content
                  const currentMessage = assistantMessage
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === currentMessage.id 
                        ? { ...msg, content: currentMessage.content }
                        : msg
                    )
                  )
                  
                  // Only increment unread count once per message when first content arrives
                  if (userHasScrolledUp.current && isFirstChunk && data.content.trim()) {
                    setUnreadCount(prev => Math.min(prev + 1, 99))
                  }
                  
                  // Only scroll if user hasn't manually scrolled up
                  if (!userHasScrolledUp.current && messagesContainerRef.current) {
                    const container = messagesContainerRef.current
                    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
                    
                    // Only auto-scroll if already near bottom (within 150px)
                    if (distanceFromBottom < 150) {
                      // Cancel any pending scroll animation
                      if (scrollAnimationFrame.current) {
                        cancelAnimationFrame(scrollAnimationFrame.current)
                      }
                      
                      // Use smooth, minimal scrolling
                      scrollAnimationFrame.current = requestAnimationFrame(() => {
                        if (messagesContainerRef.current && !userHasScrolledUp.current) {
                          // Double-check user hasn't scrolled during the frame
                          const container = messagesContainerRef.current
                          const currentDistanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
                          
                          // Only proceed if still near bottom
                          if (currentDistanceFromBottom < 150) {
                            // Smooth scroll to bottom
                            container.scrollTop = container.scrollHeight
                          }
                        }
                      })
                    }
                  }
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
      }

      // Update conversation content if new content was attached
      if (attachedContent.length > 0) {
        setConversationContent(attachedContent)
      }
      // Clear only the attached content display, not the conversation context
      setAttachedContent([])
      
    } catch (error) {
      // Handle abort separately - not an error
      if (error instanceof Error && error.name === 'AbortError') {
        const cancelMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: assistantMessage?.content || '(Response cancelled)',
          timestamp: new Date(),
        }
        if (assistantMessage?.content && assistantMessage) {
          const messageId = assistantMessage.id
          setMessages(prev => 
            prev.map(msg => 
              msg.id === messageId ? cancelMessage : msg
            )
          )
        }
        return
      }

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

  // Global keyboard shortcuts
  useEffect(() => {
    const handleGlobalKeyPress = (e: KeyboardEvent) => {
      // Ctrl/Cmd + End: Scroll to bottom
      if ((e.ctrlKey || e.metaKey) && e.key === 'End') {
        e.preventDefault()
        handleScrollToBottom()
      }
      // Escape: Stop streaming
      if (e.key === 'Escape' && isStreamingRef.current) {
        e.preventDefault()
        handleStop()
      }
    }

    window.addEventListener('keydown', handleGlobalKeyPress)
    return () => window.removeEventListener('keydown', handleGlobalKeyPress)
  }, [])

  const removeAttachment = (index: number) => {
    setAttachedContent(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
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
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
        sx={{
          flex: 1,
          overflow: 'auto',
          overflowAnchor: 'none', // Disable browser's scroll anchoring
          p: 2,
          bgcolor: 'grey.50',
          position: 'relative',
          // Optimize scrolling performance
          willChange: 'scroll-position',
          WebkitOverflowScrolling: 'touch', // Smooth scrolling on iOS
        }}
      >
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              gap: isMobile ? 1 : isTablet ? 1.5 : 2,
              mb: isMobile ? 1 : isTablet ? 1.5 : 2,
              flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
            }}
          >
            <Avatar
              sx={{
                bgcolor: message.role === 'user' ? 'secondary.main' : 'primary.main',
                width: isMobile ? 28 : 36,
                height: isMobile ? 28 : 36,
                display: isMobile && message.role === 'user' ? 'none' : 'flex',
              }}
            >
              {message.role === 'user' ? <Person /> : <SmartToy />}
            </Avatar>
            <Box
              sx={{
                maxWidth: isMobile ? '85%' : '70%',
                bgcolor: message.role === 'user' ? 'secondary.light' : 'white',
                p: isMobile ? 1.5 : 2,
                borderRadius: 2,
                boxShadow: 1,
                // Prevent layout shift during streaming
                minHeight: '40px',
                transition: 'none', // Disable transitions during streaming
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
              <Typography 
                variant={isMobile ? "body2" : "body1"} 
                sx={{ whiteSpace: 'pre-wrap' }}
              >
                {message.content}
              </Typography>
              {!isMobile && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {format(message.timestamp, 'h:mm a')}
                </Typography>
              )}
            </Box>
          </Box>
        ))}
        
        {isLoading && (
          <Box sx={{ display: 'flex', gap: isMobile ? 1 : 2, mb: isMobile ? 1 : 2 }}>
            <Avatar sx={{ 
              bgcolor: 'primary.main', 
              width: isMobile ? 28 : 36, 
              height: isMobile ? 28 : 36 
            }}>
              <SmartToy />
            </Avatar>
            <Box
              sx={{
                bgcolor: 'white',
                p: isMobile ? 1 : 2,
                borderRadius: 2,
                boxShadow: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
              role="status"
              aria-live="assertive"
            >
              <CircularProgress size={isMobile ? 14 : 16} />
              <Typography variant={isMobile ? "caption" : "body2"} color="text.secondary">
                Thinking...
              </Typography>
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
        
      </Box>
      
      {/* Scroll to Bottom FAB - Outside scrollable container */}
      <Zoom in={showScrollToBottom}>
        <Fab
          color="primary"
          size="small"
          onClick={handleScrollToBottom}
          aria-label={unreadCount > 0 ? `Scroll to bottom, ${unreadCount} unread messages` : 'Scroll to bottom'}
          sx={{
            position: 'absolute',
            bottom: isMobile ? 80 : 100,
            right: isMobile ? 16 : 32,
            zIndex: 1000,
          }}
        >
          <Badge badgeContent={unreadCount} color="error">
            <KeyboardArrowDown />
          </Badge>
        </Fab>
      </Zoom>

      <Divider />

      {/* Input Area */}
      <Box sx={{ p: isMobile ? 1 : 2 }}>
        {/* Attached Content Display */}
        {attachedContent.length > 0 && (
          <Box sx={{ mb: 0.5, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
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
        <Box sx={{ display: 'flex', gap: isMobile ? 0.5 : 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={isMobile ? 3 : 4}
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
          {isLoading && isStreamingRef.current ? (
            <IconButton
              color="error"
              onClick={handleStop}
              size={isMobile ? "small" : "medium"}
              aria-label="Stop response (Esc)"
              title="Stop response (Press Esc)"
              sx={{ 
                bgcolor: 'error.main',
                color: 'white',
                '&:hover': {
                  bgcolor: 'error.dark',
                },
              }}
            >
              <Stop />
            </IconButton>
          ) : (
            <IconButton
              color="primary"
              onClick={handleSend}
              disabled={isLoading || (!input.trim() && attachedContent.length === 0)}
              size={isMobile ? "small" : "medium"}
              aria-label="Send message"
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
          )}
        </Box>
      </Box>
    </Paper>
  )
}