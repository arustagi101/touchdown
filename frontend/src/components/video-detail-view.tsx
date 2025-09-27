"use client"

import React from 'react'
import { Button } from '@/components/ui/button'
import { Video, Scissors, ExternalLink, ArrowLeft, Download } from 'lucide-react'

interface ProcessedVideo {
  hash: string
  title: string
  url: string
  folderPath: string
  highlightFiles: string[]
  reelFiles: string[]
  finalHighlight?: string
}

interface VideoDetailViewProps {
  video: ProcessedVideo | null
  isOpen: boolean
  onClose: () => void
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

export function VideoDetailView({ video, isOpen, onClose }: VideoDetailViewProps) {
  if (!isOpen || !video) return null

  return (
    <div className="bg-card border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="border-b pb-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={onClose}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div>
              <h2 className="text-2xl font-semibold">{video.title}</h2>
              <p className="text-sm text-muted-foreground">Hash: {video.hash}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {video.url && (
              <Button
                variant="outline"
                onClick={() => window.open(video.url, '_blank')}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Original Video
              </Button>
            )}
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-8">
        {/* Final Highlight - Centered and Large */}
        <div className="flex flex-col items-center space-y-4">
          <div className="flex items-center gap-2">
            <Scissors className="w-6 h-6 text-green-500" />
            <h3 className="text-2xl font-semibold">Final Highlight</h3>
          </div>
          {video.finalHighlight ? (
            <div className="w-full max-w-4xl space-y-4">
              <div className="relative aspect-video rounded-lg overflow-hidden bg-black">
                <video
                  key={`${video.hash}-${video.finalHighlight}`}
                  controls
                  className="w-full h-full"
                  preload="metadata"
                >
                  <source src={`/api/video/${video.hash}/${video.finalHighlight}`} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              </div>
              <div className="flex justify-center">
                <Button variant="outline" size="lg">
                  <Download className="w-4 h-4 mr-2" />
                  Download Final Highlight
                </Button>
              </div>
            </div>
          ) : (
            <div className="w-full max-w-4xl aspect-video rounded-lg border border-dashed border-muted-foreground/30 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Scissors className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No final highlight available</h3>
                <p className="text-sm">The final highlight is still being processed</p>
              </div>
            </div>
          )}
        </div>

        {/* Highlight Reels - Horizontal Scroll */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Video className="w-6 h-6 text-blue-500" />
            <h3 className="text-2xl font-semibold">Highlight Reels</h3>
            <span className="bg-blue-100 text-blue-700 text-sm px-3 py-1 rounded-full">
              {video.highlightFiles.length} clips
            </span>
          </div>
          {video.highlightFiles.length > 0 ? (
            <div className="overflow-x-auto pb-4">
              <div className="flex gap-4 min-w-max">
                {video.highlightFiles.map((file, index) => (
                  <div key={file} className="flex-shrink-0 w-80 space-y-3">
                    <div className="relative aspect-video rounded-lg overflow-hidden bg-black">
                      <video
                        key={`${video.hash}-${file}`}
                        controls
                        className="w-full h-full"
                        preload="metadata"
                      >
                        <source src={`/api/video/${video.hash}/${file}`} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="font-medium truncate" title={file}>
                        Reel {index + 1}
                      </p>
                      <Button variant="ghost" size="sm">
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="border border-dashed border-muted-foreground/30 rounded-lg p-12 text-center text-muted-foreground">
              <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No highlight reels generated yet</h3>
              <p>Individual highlight clips will appear here once processing is complete</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}