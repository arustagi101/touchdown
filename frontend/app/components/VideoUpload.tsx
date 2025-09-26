'use client'

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Film, AlertCircle } from 'lucide-react';
import { videoApi, Video } from '@/lib/api';

interface VideoUploadProps {
  onVideoUploaded: (video: Video) => void;
}

export default function VideoUpload({ onVideoUploaded }: VideoUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [sportType, setSportType] = useState('general');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setFile(file);
      setTitle(file.name.replace(/\.[^/.]+$/, ''));
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    },
    maxFiles: 1,
    maxSize: 500 * 1024 * 1024, // 500MB
    onDropRejected: (files) => {
      const rejection = files[0];
      if (rejection.file.size > 500 * 1024 * 1024) {
        setError('File size must be less than 500MB');
      } else {
        setError('Invalid file type. Please upload a video file.');
      }
    }
  });

  const handleUpload = async () => {
    if (!file || !title) return;

    setUploading(true);
    setError('');

    try {
      const video = await videoApi.uploadVideo(file, title, sportType);
      onVideoUploaded(video);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="space-y-4">
            <Film className="h-16 w-16 mx-auto text-blue-500" />
            <div>
              <p className="text-lg font-semibold">{file.name}</p>
              <p className="text-sm text-gray-400">{formatFileSize(file.size)}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setTitle('');
              }}
              className="text-sm text-red-400 hover:text-red-300"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className="h-16 w-16 mx-auto text-gray-500" />
            <div>
              <p className="text-lg font-semibold">
                {isDragActive ? 'Drop your video here' : 'Drag & drop your video'}
              </p>
              <p className="text-sm text-gray-400 mt-2">
                or click to browse (MP4, MOV, AVI, MKV, WebM - Max 500MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {file && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Video Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter video title"
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
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || !title || uploading}
        className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
          file && title && !uploading
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-700 text-gray-400 cursor-not-allowed'
        }`}
      >
        {uploading ? 'Uploading...' : 'Process Video'}
      </button>
    </div>
  );
}