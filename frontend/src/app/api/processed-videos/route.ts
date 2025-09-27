import { NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

export interface ProcessedVideo {
  hash: string
  title: string
  url: string
  folderPath: string
  highlightFiles: string[]
  reelFiles: string[]
  finalHighlight?: string
}

export async function GET() {
  try {
    const outputPath = process.env.NEXT_PUBLIC_OUTPUT_PATH || './output'

    // Check if output directory exists
    try {
      await fs.access(outputPath)
    } catch {
      return NextResponse.json({ videos: [] })
    }

    const folders = await fs.readdir(outputPath, { withFileTypes: true })
    const processedVideos: ProcessedVideo[] = []

    for (const folder of folders) {
      if (folder.isDirectory()) {
        const folderPath = path.join(outputPath, folder.name)
        const metadataPath = path.join(folderPath, 'metadata.json')

        try {
          // Check if metadata.json exists
          await fs.access(metadataPath)
          const metadataContent = await fs.readFile(metadataPath, 'utf-8')
          const metadata = JSON.parse(metadataContent)

          // Scan for video files in the folder
          const folderContents = await fs.readdir(folderPath)
          const highlightFiles = folderContents.filter(file =>
            file.startsWith('highlight_') && (file.endsWith('.mp4') || file.endsWith('.mov'))
          )
          const reelFiles = folderContents.filter(file =>
            file.startsWith('highlight_') && (file.endsWith('.mp4') || file.endsWith('.mov'))
          )
          const finalHighlight = folderContents.find(file =>
            file === 'final_highlight.mp4' || file === 'final_highlight.mov'
          )

          processedVideos.push({
            hash: folder.name,
            title: metadata.title || 'Unknown Title',
            url: metadata.url || '',
            folderPath: folderPath,
            highlightFiles,
            reelFiles,
            finalHighlight
          })
        } catch (error) {
          // Skip folders without valid metadata.json
          console.log(`Skipping folder ${folder.name}: no valid metadata.json`)
        }
      }
    }

    // Sort by folder name (hash) in descending order (newest first)
    processedVideos.sort((a, b) => b.hash.localeCompare(a.hash))

    return NextResponse.json({ videos: processedVideos })
  } catch (error) {
    console.error('Error reading processed videos:', error)
    return NextResponse.json(
      { error: 'Failed to read processed videos' },
      { status: 500 }
    )
  }
}