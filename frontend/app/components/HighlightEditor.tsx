'use client'

import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Play, Download, Clock, Star, GripVertical, Eye, EyeOff } from 'lucide-react';
import { Video, Highlight, videoApi } from '@/lib/api';

interface HighlightEditorProps {
  video: Video;
}

export default function HighlightEditor({ video }: HighlightEditorProps) {
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [selectedDuration, setSelectedDuration] = useState(120);
  const [generating, setGenerating] = useState(false);
  const [totalDuration, setTotalDuration] = useState(0);

  useEffect(() => {
    loadHighlights();
  }, [video.id]);

  const loadHighlights = async () => {
    try {
      const data = await videoApi.getHighlights(video.id);
      setHighlights(data);
      updateTotalDuration(data);
    } catch (err) {
      console.error('Failed to load highlights:', err);
    }
  };

  const updateTotalDuration = (highlights: Highlight[]) => {
    const duration = highlights
      .filter(h => h.is_included)
      .reduce((sum, h) => sum + h.duration, 0);
    setTotalDuration(duration);
  };

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(highlights);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setHighlights(items);

    try {
      await videoApi.reorderHighlights(video.id, items.map(h => h.id));
    } catch (err) {
      console.error('Failed to reorder highlights:', err);
    }
  };

  const toggleHighlight = async (highlight: Highlight) => {
    const updated = highlights.map(h =>
      h.id === highlight.id ? { ...h, is_included: !h.is_included } : h
    );
    setHighlights(updated);
    updateTotalDuration(updated);

    try {
      await videoApi.updateHighlight(highlight.id, { is_included: !highlight.is_included });
    } catch (err) {
      console.error('Failed to update highlight:', err);
    }
  };

  const autoSelect = async () => {
    try {
      const result = await videoApi.autoSelectHighlights(video.id, selectedDuration);
      await loadHighlights();
    } catch (err) {
      console.error('Failed to auto-select:', err);
    }
  };

  const generateReel = async () => {
    setGenerating(true);
    try {
      const includedIds = highlights.filter(h => h.is_included).map(h => h.id);
      await videoApi.generateReel(video.id, includedIds, selectedDuration);
    } catch (err) {
      console.error('Failed to generate reel:', err);
    } finally {
      setGenerating(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-xl shadow-2xl p-6">
            <h2 className="text-xl font-bold mb-4">Detected Highlights</h2>

            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-400">
                  {highlights.filter(h => h.is_included).length} selected
                </span>
                <span className="text-sm text-gray-400">
                  Total: {formatTime(totalDuration)}
                </span>
              </div>
              <button
                onClick={autoSelect}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"
              >
                Auto-select
              </button>
            </div>

            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="highlights">
                {(provided) => (
                  <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-3">
                    {highlights.map((highlight, index) => (
                      <Draggable key={highlight.id} draggableId={highlight.id} index={index}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className={`bg-gray-700 rounded-lg p-4 transition-all ${
                              snapshot.isDragging ? 'shadow-xl' : ''
                            } ${!highlight.is_included ? 'opacity-50' : ''}`}
                          >
                            <div className="flex items-start gap-4">
                              <div
                                {...provided.dragHandleProps}
                                className="mt-1 cursor-move"
                              >
                                <GripVertical className="h-5 w-5 text-gray-500" />
                              </div>

                              <div className="flex-1">
                                <div className="flex items-start justify-between mb-2">
                                  <div>
                                    <span className="font-semibold">
                                      {highlight.category || 'Highlight'}
                                    </span>
                                    <div className="flex items-center gap-3 mt-1">
                                      <span className="text-sm text-gray-400">
                                        {formatTime(highlight.start_time)} - {formatTime(highlight.end_time)}
                                      </span>
                                      <span className="text-sm text-gray-400">
                                        {formatTime(highlight.duration)}
                                      </span>
                                      <div className="flex items-center gap-1">
                                        <Star className="h-4 w-4 text-yellow-500" />
                                        <span className="text-sm">{highlight.score.toFixed(0)}</span>
                                      </div>
                                    </div>
                                  </div>
                                  <button
                                    onClick={() => toggleHighlight(highlight)}
                                    className="p-2 hover:bg-gray-600 rounded-lg transition-colors"
                                  >
                                    {highlight.is_included ? (
                                      <Eye className="h-5 w-5 text-blue-500" />
                                    ) : (
                                      <EyeOff className="h-5 w-5 text-gray-500" />
                                    )}
                                  </button>
                                </div>
                                {highlight.description && (
                                  <p className="text-sm text-gray-300">{highlight.description}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="bg-gray-800 rounded-xl shadow-2xl p-6 sticky top-8">
            <h3 className="text-xl font-bold mb-4">Generate Highlight Reel</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Target Duration</label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="30"
                    max="300"
                    step="30"
                    value={selectedDuration}
                    onChange={(e) => setSelectedDuration(Number(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium w-12">{formatTime(selectedDuration)}</span>
                </div>
              </div>

              <div className="bg-gray-700 rounded-lg p-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Selected Highlights</span>
                    <span>{highlights.filter(h => h.is_included).length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Total Duration</span>
                    <span className={totalDuration > selectedDuration ? 'text-yellow-400' : ''}>
                      {formatTime(totalDuration)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Target Duration</span>
                    <span>{formatTime(selectedDuration)}</span>
                  </div>
                </div>
              </div>

              {totalDuration > selectedDuration && (
                <div className="bg-yellow-500/10 border border-yellow-500/50 rounded-lg p-3">
                  <p className="text-sm text-yellow-400">
                    Selected highlights exceed target duration. Some clips may be trimmed.
                  </p>
                </div>
              )}

              <button
                onClick={generateReel}
                disabled={generating || highlights.filter(h => h.is_included).length === 0}
                className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2 ${
                  generating || highlights.filter(h => h.is_included).length === 0
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {generating ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-5 w-5" />
                    Generate Reel
                  </>
                )}
              </button>

              <div className="text-center text-sm text-gray-500">
                <p>Your highlight reel will be ready for download once generated</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}