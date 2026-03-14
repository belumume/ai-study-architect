import { useState } from 'react'
import { ContentSelector } from '@/components/content'
import { ChatInterface } from '@/components/chat'

export function StudyPage() {
  const [selectedContent, setSelectedContent] = useState<
    { id: string; title: string }[]
  >([])

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Left side - Content Selection */}
      <div className="hidden w-[350px] flex-shrink-0 flex-col overflow-hidden rounded-xl border border-border bg-surface p-4 lg:flex">
        <h2 className="font-display text-sm font-bold uppercase tracking-wider">
          Study Materials
        </h2>
        <p className="mb-3 mt-1 font-body text-xs text-text-muted">
          Add content to enhance your chat, or start chatting directly
        </p>
        <div className="min-h-0 flex-1 overflow-auto">
          <ContentSelector
            onSelectionChange={setSelectedContent}
            selectedContent={selectedContent}
          />
        </div>
      </div>

      {/* Right side - Chat Interface (Primary) */}
      <div className="min-h-0 flex-1">
        <ChatInterface selectedContent={selectedContent} />
      </div>
    </div>
  )
}
