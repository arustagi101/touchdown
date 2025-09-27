import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ hash: string; filename: string }> }
) {
  try {
    const { hash, filename } = await params
    const outputPath = process.env.NEXT_PUBLIC_OUTPUT_PATH || './output'
    const videoPath = path.join(outputPath, hash, filename)

    // Security check: ensure the file is within the output directory
    const resolvedVideoPath = path.resolve(videoPath)
    const resolvedOutputPath = path.resolve(outputPath)
    if (!resolvedVideoPath.startsWith(resolvedOutputPath)) {
      return NextResponse.json({ error: 'Access denied' }, { status: 403 })
    }

    // Check if file exists
    try {
      await fs.access(videoPath)
    } catch {
      return NextResponse.json({ error: 'Video not found' }, { status: 404 })
    }

    // Read the video file
    const videoBuffer = await fs.readFile(videoPath)
    const stat = await fs.stat(videoPath)

    // Determine content type
    const ext = path.extname(filename).toLowerCase()
    let contentType = 'video/mp4'
    if (ext === '.mov') contentType = 'video/quicktime'
    if (ext === '.avi') contentType = 'video/x-msvideo'
    if (ext === '.webm') contentType = 'video/webm'

    // Handle range requests for video streaming
    const range = request.headers.get('range')
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-')
      const start = parseInt(parts[0], 10)
      const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1
      const chunksize = (end - start) + 1

      const chunk = videoBuffer.slice(start, end + 1)

      return new NextResponse(chunk, {
        status: 206,
        headers: {
          'Content-Range': `bytes ${start}-${end}/${stat.size}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': chunksize.toString(),
          'Content-Type': contentType,
        },
      })
    }

    // Return full video if no range requested
    return new NextResponse(videoBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Length': stat.size.toString(),
        'Accept-Ranges': 'bytes',
      },
    })
  } catch (error) {
    console.error('Error serving video:', error)
    return NextResponse.json(
      { error: 'Failed to serve video' },
      { status: 500 }
    )
  }
}