'use client'

import { useState } from 'react';
import { Link2, Youtube, AlertCircle } from 'lucide-react';
import { videoApi, Video } from '@/lib/api';

interface UrlInputProps {
  onUrlSubmit: (video: Video) => void;
}

export default function UrlInput({ onUrlSubmit }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [sportType, setSportType] = useState('general');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isYouTubeUrl = (url: string) => {
    return url.includes('youtube.com') || url.includes('youtu.be');
  };

  const handleSubmit = async () => {
    if (!url) return;

    setLoading(true);
    setError('');

    try {
      const video = await videoApi.processFromUrl(url, title || 'Video from URL', sportType);
      onUrlSubmit(video);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process URL. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <div className="flex justify-center gap-4">
          <Youtube className="h-12 w-12 text-red-500" />
          <Link2 className="h-12 w-12 text-blue-500" />
        </div>
        <p className="text-gray-400">
          Enter a YouTube URL or any direct video link
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Video URL</label>
          <div className="relative">
            <input
              type="url"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setError('');
              }}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://youtube.com/watch?v=..."
            />
            <Link2 className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
          {url && isYouTubeUrl(url) && (
            <p className="text-sm text-green-400 mt-1">✓ YouTube URL detected</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Video Title (Optional)</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Will be auto-detected if not provided"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Sport Type</label>
          <select
            value={sportType}
            onChange={(e) => setSportType(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="general">General Sports</option>
            <option value="soccer">Soccer / Football</option>
            <option value="basketball">Basketball</option>
            <option value="football">American Football</option>
            <option value="baseball">Baseball</option>
            <option value="tennis">Tennis</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!url || loading}
        className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
          url && !loading
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-700 text-gray-400 cursor-not-allowed'
        }`}
      >
        {loading ? 'Processing...' : 'Process Video'}
      </button>

      <div className="text-center text-sm text-gray-500">
        <p>Supported: YouTube, Vimeo, and direct video URLs</p>
        <p className="mt-1">Max video duration: 30 minutes</p>
      </div>
    </div>
  );
}