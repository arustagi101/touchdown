'use client'

import { useState } from 'react';
import { Upload, Link2, Activity } from 'lucide-react';
import VideoUpload from './components/VideoUpload';
import UrlInput from './components/UrlInput';
import ProcessingStatus from './components/ProcessingStatus';
import HighlightEditor from './components/HighlightEditor';
import { Video } from '@/lib/api';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'url'>('upload');
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleVideoSubmit = (video: Video) => {
    setCurrentVideo(video);
    setIsProcessing(true);
  };

  const handleProcessingComplete = () => {
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <header className="border-b border-gray-700">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <Activity className="h-8 w-8 text-blue-500" />
            <h1 className="text-3xl font-bold">Touchdown</h1>
            <span className="text-gray-400 text-sm">AI-Powered Highlight Reel Generator</span>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {!currentVideo ? (
          <div className="max-w-2xl mx-auto">
            <div className="bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
              <div className="flex border-b border-gray-700">
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`flex-1 flex items-center justify-center gap-2 px-6 py-4 transition-colors ${
                    activeTab === 'upload'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-900 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  <Upload className="h-5 w-5" />
                  Upload Video
                </button>
                <button
                  onClick={() => setActiveTab('url')}
                  className={`flex-1 flex items-center justify-center gap-2 px-6 py-4 transition-colors ${
                    activeTab === 'url'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-900 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  <Link2 className="h-5 w-5" />
                  From URL
                </button>
              </div>

              <div className="p-8">
                {activeTab === 'upload' ? (
                  <VideoUpload onVideoUploaded={handleVideoSubmit} />
                ) : (
                  <UrlInput onUrlSubmit={handleVideoSubmit} />
                )}
              </div>
            </div>

            <div className="mt-8 text-center text-gray-400">
              <h2 className="text-lg font-semibold mb-4">How it works</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gray-800 rounded-lg p-6">
                  <div className="text-3xl mb-3">📹</div>
                  <h3 className="font-semibold mb-2">Upload Video</h3>
                  <p className="text-sm">Upload your sports footage or provide a YouTube URL</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-6">
                  <div className="text-3xl mb-3">🤖</div>
                  <h3 className="font-semibold mb-2">AI Analysis</h3>
                  <p className="text-sm">Our AI analyzes the video to identify key moments</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-6">
                  <div className="text-3xl mb-3">✨</div>
                  <h3 className="font-semibold mb-2">Get Highlights</h3>
                  <p className="text-sm">Download your personalized highlight reel</p>
                </div>
              </div>
            </div>
          </div>
        ) : isProcessing ? (
          <ProcessingStatus
            video={currentVideo}
            onComplete={handleProcessingComplete}
          />
        ) : (
          <HighlightEditor video={currentVideo} />
        )}
      </main>
    </div>
  );
}
