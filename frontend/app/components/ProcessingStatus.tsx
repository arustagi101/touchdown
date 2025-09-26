'use client'

import { useEffect, useState } from 'react';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Video, WebSocketClient, videoApi } from '@/lib/api';

interface ProcessingStatusProps {
  video: Video;
  onComplete: () => void;
}

export default function ProcessingStatus({ video, onComplete }: ProcessingStatusProps) {
  const [status, setStatus] = useState(video.status);
  const [progress, setProgress] = useState(video.processing_progress);
  const [message, setMessage] = useState('Initializing...');
  const [error, setError] = useState('');

  useEffect(() => {
    const ws = new WebSocketClient();
    ws.connect(video.id);

    ws.onMessage((data) => {
      if (data.type === 'progress') {
        setStatus(data.status);
        setProgress(data.progress);
        setMessage(data.message || getStatusMessage(data.status));
      } else if (data.type === 'completed') {
        setStatus('completed');
        setProgress(100);
        setMessage('Processing complete!');
        setTimeout(onComplete, 2000);
      } else if (data.type === 'error') {
        setStatus('failed');
        setError(data.error);
      }
    });

    const pollStatus = setInterval(async () => {
      try {
        const statusData = await videoApi.getVideoStatus(video.id);
        setStatus(statusData.status);
        setProgress(statusData.progress);

        if (statusData.status === 'completed') {
          clearInterval(pollStatus);
          setTimeout(onComplete, 2000);
        } else if (statusData.status === 'failed') {
          clearInterval(pollStatus);
          setError(statusData.error_message || 'Processing failed');
        }
      } catch (err) {
        console.error('Failed to poll status:', err);
      }
    }, 5000);

    return () => {
      ws.disconnect();
      clearInterval(pollStatus);
    };
  }, [video.id, onComplete]);

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'Downloading video...';
      case 'transcribing':
        return 'Extracting audio and transcribing...';
      case 'analyzing':
        return 'AI analyzing for highlights...';
      case 'generating':
        return 'Generating highlight reel...';
      case 'completed':
        return 'Processing complete!';
      default:
        return 'Processing...';
    }
  };

  const getStepStatus = (step: string) => {
    const steps = ['downloading', 'transcribing', 'analyzing', 'generating'];
    const currentIndex = steps.indexOf(status);
    const stepIndex = steps.indexOf(step);

    if (status === 'failed') return 'failed';
    if (status === 'completed' || stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  const StepIcon = ({ step }: { step: string }) => {
    const stepStatus = getStepStatus(step);

    if (stepStatus === 'completed') {
      return <CheckCircle className="h-6 w-6 text-green-500" />;
    } else if (stepStatus === 'active') {
      return <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />;
    } else if (stepStatus === 'failed') {
      return <XCircle className="h-6 w-6 text-red-500" />;
    } else {
      return <div className="h-6 w-6 rounded-full bg-gray-600" />;
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gray-800 rounded-xl shadow-2xl p-8">
        <h2 className="text-2xl font-bold mb-8 text-center">Processing Video</h2>

        <div className="space-y-8">
          <div className="bg-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-lg font-semibold">{video.title}</span>
              <span className="text-sm text-gray-400">{progress}%</span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-3">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-400 mt-3">{message}</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <StepIcon step="downloading" />
              <div className="flex-1">
                <p className="font-semibold">Download Video</p>
                <p className="text-sm text-gray-400">Retrieving video content</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <StepIcon step="transcribing" />
              <div className="flex-1">
                <p className="font-semibold">Transcribe Audio</p>
                <p className="text-sm text-gray-400">Converting speech to text</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <StepIcon step="analyzing" />
              <div className="flex-1">
                <p className="font-semibold">AI Analysis</p>
                <p className="text-sm text-gray-400">Identifying key moments</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <StepIcon step="generating" />
              <div className="flex-1">
                <p className="font-semibold">Generate Highlights</p>
                <p className="text-sm text-gray-400">Creating your highlight reel</p>
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
              <p className="text-red-400 font-semibold mb-2">Processing Failed</p>
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {status === 'completed' && (
            <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
              <p className="text-green-400 font-semibold">✓ Processing Complete!</p>
              <p className="text-sm text-green-300 mt-1">Redirecting to highlight editor...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}