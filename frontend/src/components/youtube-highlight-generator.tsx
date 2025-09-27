"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Play, Sparkles, Video, Scissors, Folder, FolderOpen, RefreshCw, ExternalLink } from 'lucide-react'
import { getOutputPath } from '@/lib/config'
import { VideoDetailView } from './video-detail-view'

interface ProcessedVideo {
  hash: string
  title: string
  url: string
  folderPath: string
  highlightFiles: string[]
  reelFiles: string[]
  finalHighlight?: string
}

function extractVideoId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)/
  ]

  for (const pattern of patterns) {
    const match = url.match(pattern)
    if (match) return match[1]
  }
  return null
}

export function YoutubeHighlightGenerator() {
  const [url, setUrl] = useState('')
  const [videoId, setVideoId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [outputPath, setOutputPath] = useState<string>('')
  const [processedVideos, setProcessedVideos] = useState<ProcessedVideo[]>([])
  const [isLoadingVideos, setIsLoadingVideos] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState<ProcessedVideo | null>(null)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)

    // Only run after hydration
    const loadConfig = () => {
      try {
        const path = getOutputPath()
        setOutputPath(path)
        fetchProcessedVideos()
      } catch (err) {
        setError('Configuration error: NEXT_PUBLIC_OUTPUT_PATH not set')
      }
    }

    // Small delay to ensure hydration is complete
    const timer = setTimeout(loadConfig, 100)
    return () => clearTimeout(timer)
  }, [])

  const fetchProcessedVideos = async () => {
    setIsLoadingVideos(true)
    try {
      const response = await fetch('/api/processed-videos')
      const data = await response.json()
      if (response.ok) {
        setProcessedVideos(data.videos)
      }
    } catch (err) {
      console.error('Failed to fetch processed videos:', err)
    } finally {
      setIsLoadingVideos(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const extractedVideoId = extractVideoId(url)
    if (!extractedVideoId) {
      setError('Please enter a valid YouTube URL')
      setIsLoading(false)
      return
    }

    // Fire and forget API call to localhost:8000
    try {
      fetch(`http://localhost:8000/?url=${encodeURIComponent(url)}`, {
        method: 'GET',
        mode: 'no-cors'
      }).catch(() => {
        // Ignore errors for fire and forget
      })
    } catch {
      // Ignore errors for fire and forget
    }

    setVideoId(extractedVideoId)
    setIsLoading(false)

    // Refresh processed videos list when a new video is added
    setTimeout(() => {
      fetchProcessedVideos()
    }, 1000)
  }

  const isValidUrl = url && extractVideoId(url)

  // Prevent hydration issues by only rendering after mount
  if (!isMounted) {
    return (
      <div className="max-w-7xl mx-auto p-6 space-y-8">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2 text-3xl font-bold">
            <Sparkles className="w-8 h-8 text-yellow-500" />
            Touchdown Highlight Generator
          </div>
          <p className="text-muted-foreground text-lg">
            Loading...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-2 text-3xl font-bold">
          <Sparkles className="w-8 h-8 text-yellow-500" />
          Touchdown Highlight Generator
        </div>
        <p className="text-muted-foreground text-lg">
          Transform your YouTube videos into engaging highlights and reels
        </p>
      </div>

      {/* Configuration Info */}
      {/* {outputPath && (
        <div className="bg-muted/50 border rounded-lg p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Output directory:</span>
            <code className="bg-muted px-2 py-1 rounded text-xs font-mono">
              {outputPath}
            </code>
          </div>
        </div>
      )} */}

      {/* URL Input Form */}
      <div className="bg-card border rounded-lg p-6 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="youtube-url" className="text-sm font-medium">
              Add New YouTube Video
            </label>
            <div className="flex gap-3">
              <Input
                id="youtube-url"
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1"
                aria-invalid={!!error}
              />
              <Button
                type="submit"
                disabled={!isValidUrl || isLoading || !outputPath}
                className="px-6"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                    Processing
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Highlights
                  </>
                )}
              </Button>
            </div>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        </form>
      </div>

      {/* Current Video Preview */}
      {/* {videoId && (
        <div className="bg-card border rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Play className="w-5 h-5 text-primary" />
            <h2 className="text-xl font-semibold">Current Video Processing</h2>
          </div>
          <div className="relative aspect-video rounded-lg overflow-hidden bg-black max-w-2xl">
            <iframe
              src={`https://www.youtube.com/embed/${videoId}`}
              title="YouTube video player"
              className="absolute inset-0 w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      )} */}

      {/* Processed Videos List */}
      <div className="bg-card border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-semibold">Processed Videos</h2>
            <span className="bg-muted text-muted-foreground text-sm px-2 py-1 rounded-full">
              {processedVideos.length} videos
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProcessedVideos}
            disabled={isLoadingVideos}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingVideos ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {isLoadingVideos && (
          <div className="text-center py-8">
            <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading processed videos...</p>
          </div>
        )}

        {!isLoadingVideos && processedVideos.length === 0 && (
          <div className="text-center py-8">
            <Video className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
            <h3 className="font-medium mb-2">No processed videos found</h3>
            <p className="text-muted-foreground">
              Add a YouTube URL above to start generating highlights.
            </p>
          </div>
        )}

        {!isLoadingVideos && processedVideos.length > 0 && (
          <div className="space-y-4">
            {processedVideos.map((video) => (
              <div
                key={video.hash}
                className="border rounded-lg p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => setSelectedVideo(video)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Video className="w-5 h-5 text-primary flex-shrink-0" />
                      <h3 className="font-medium truncate" title={video.title}>
                        {video.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Scissors className="w-4 h-4" />
                        <span>{video.finalHighlight ? 'Final highlight ready' : 'Processing...'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Video className="w-4 h-4" />
                        <span>{video.highlightFiles.length} reels</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {video.url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          window.open(video.url, '_blank')
                        }}
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedVideo(video)
                      }}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Video Detail View - Below Table */}
      {selectedVideo && (
        <VideoDetailView
          video={selectedVideo}
          isOpen={!!selectedVideo}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </div>
  )
}