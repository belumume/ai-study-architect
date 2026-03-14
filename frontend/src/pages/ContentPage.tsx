import { useState } from 'react'
import { ContentUpload, ContentList } from '@/components/content'
import { Button } from '@/components/ui/button'

export function ContentPage() {
  const [activeTab, setActiveTab] = useState<'list' | 'upload'>('list')
  const [refreshList, setRefreshList] = useState(0)

  const handleUploadComplete = () => {
    setActiveTab('list')
    setRefreshList((prev) => prev + 1)
  }

  return (
    <div>
      <div className="mb-4 flex gap-2">
        <Button
          variant={activeTab === 'list' ? 'default' : 'outline'}
          onClick={() => setActiveTab('list')}
          className={
            activeTab === 'list'
              ? 'bg-primary text-void'
              : 'border-border text-text-primary hover:bg-raised'
          }
        >
          My Content
        </Button>
        <Button
          variant={activeTab === 'upload' ? 'default' : 'outline'}
          onClick={() => setActiveTab('upload')}
          className={
            activeTab === 'upload'
              ? 'bg-primary text-void'
              : 'border-border text-text-primary hover:bg-raised'
          }
        >
          Upload New
        </Button>
      </div>

      {activeTab === 'upload' ? (
        <ContentUpload onUploadComplete={handleUploadComplete} />
      ) : (
        <ContentList key={refreshList} />
      )}
    </div>
  )
}
