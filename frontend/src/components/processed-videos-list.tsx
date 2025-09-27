"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Video, ExternalLink, Calendar, Hash, RefreshCw, FolderOpen } from 'lucide-react'

interface ProcessedVideo {
  hash: string
  title: string
  url: string
  folderPath: string
}

interface ProcessedVideosListProps {
  isOpen: boolean
  onClose: () => void
}

export function ProcessedVideosList({ isOpen, onClose }: ProcessedVideosListProps) {
  const [videos, setVideos] = useState<ProcessedVideo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchProcessedVideos = async () => {
    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/processed-videos')
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch processed videos')
      }

      setVideos(data.videos)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchProcessedVideos()
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background border rounded-lg shadow-lg w-full max-w-4xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="border-b p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-semibold">Processed Videos</h2>
              <span className="bg-muted text-muted-foreground text-sm px-2 py-1 rounded-full">
                {videos.length} videos
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchProcessedVideos}
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {isLoading && (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading processed videos...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-8">
              <p className="text-destructive mb-4">{error}</p>
              <Button variant="outline" onClick={fetchProcessedVideos}>
                Try Again
              </Button>
            </div>
          )}

          {!isLoading && !error && videos.length === 0 && (
            <div className="text-center py-8">
              <Video className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="font-medium mb-2">No processed videos found</h3>
              <p className="text-muted-foreground">
                Process some YouTube videos to see them here.
              </p>
            </div>
          )}

          {!isLoading && !error && videos.length > 0 && (
            <div className="space-y-4">
              {videos.map((video) => (
                <div
                  key={video.hash}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Video className="w-5 h-5 text-primary flex-shrink-0" />
                        <h3 className="font-medium truncate" title={video.title}>
                          {video.title}
                        </h3>
                      </div>

                      <div className="space-y-1 text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Hash className="w-4 h-4" />
                          <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">
                            {video.hash}
                          </code>
                        </div>

                        <div className="flex items-center gap-2">
                          <FolderOpen className="w-4 h-4" />
                          <span className="truncate" title={video.folderPath}>
                            {video.folderPath}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 flex-shrink-0">
                      {video.url && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(video.url, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Original
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          // Open folder in file explorer (this is a placeholder)
                          navigator.clipboard.writeText(video.folderPath)
                        }}
                        title="Copy folder path to clipboard"
                      >
                        <FolderOpen className="w-4 h-4 mr-2" />
                        Folder
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}