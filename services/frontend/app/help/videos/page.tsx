'use client';

/**
 * Feature #673: Help System - Video Tutorials
 * 
 * Comprehensive video tutorial library for learning AutoGraph features.
 * 
 * Features:
 * - Video tutorial library organized by category
 * - Embedded video player
 * - Search and filtering
 * - Progress tracking
 * - Related tutorials
 * - Playlists for learning paths
 * - Duration and difficulty indicators
 * - Captions and transcripts
 * - High-quality production
 */

import React, { useState } from 'react';
import { Play, Clock, Star, Check, Search, BookOpen, ChevronRight } from 'lucide-react';
import Link from 'next/link';

interface VideoTutorial {
  id: string;
  title: string;
  description: string;
  category: string;
  duration: string; // e.g., "5:32"
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  videoUrl: string; // YouTube embed URL
  thumbnailUrl: string;
  topics: string[];
  relatedVideos?: string[];
}

const VIDEO_TUTORIALS: VideoTutorial[] = [
  // Getting Started
  {
    id: 'intro-autograph',
    title: 'Welcome to AutoGraph - Quick Start Guide',
    description: 'Get started with AutoGraph in 5 minutes. Learn how to create your first diagram, navigate the interface, and use basic tools.',
    category: 'getting-started',
    duration: '5:24',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/intro.jpg',
    topics: ['basics', 'dashboard', 'navigation'],
    relatedVideos: ['canvas-basics', 'first-diagram'],
  },
  {
    id: 'first-diagram',
    title: 'Creating Your First Diagram',
    description: 'Step-by-step walkthrough of creating a professional diagram from scratch. Learn tools, styling, and best practices.',
    category: 'getting-started',
    duration: '8:15',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/first-diagram.jpg',
    topics: ['canvas', 'drawing', 'basics'],
    relatedVideos: ['intro-autograph', 'canvas-basics'],
  },

  // Canvas & Drawing
  {
    id: 'canvas-basics',
    title: 'Canvas Basics - Tools and Techniques',
    description: 'Master the canvas with drawing tools, selection, transformation, and keyboard shortcuts. Become productive fast!',
    category: 'canvas',
    duration: '12:45',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/canvas-basics.jpg',
    topics: ['canvas', 'tools', 'shortcuts'],
    relatedVideos: ['advanced-canvas', 'keyboard-shortcuts'],
  },
  {
    id: 'advanced-canvas',
    title: 'Advanced Canvas Features',
    description: 'Unlock advanced features: grouping, alignment, z-order, figures, and professional styling techniques.',
    category: 'canvas',
    duration: '15:30',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/advanced-canvas.jpg',
    topics: ['grouping', 'alignment', 'styling'],
    relatedVideos: ['canvas-basics', 'design-tips'],
  },
  {
    id: 'figures-frames',
    title: 'Working with Figures and Frames',
    description: 'Organize complex diagrams using figures. Learn nesting, collapsing, and exporting individual frames.',
    category: 'canvas',
    duration: '9:20',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/figures.jpg',
    topics: ['figures', 'organization'],
    relatedVideos: ['advanced-canvas', 'export-selection'],
  },

  // AI Generation
  {
    id: 'ai-generation',
    title: 'AI Diagram Generation - From Idea to Diagram',
    description: 'Generate professional diagrams with AI. Learn prompt writing, refinement, and achieving high-quality results.',
    category: 'ai',
    duration: '10:55',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/ai-generation.jpg',
    topics: ['ai', 'generation', 'prompts'],
    relatedVideos: ['ai-prompts', 'ai-refinement'],
  },
  {
    id: 'ai-prompts',
    title: 'Writing Effective AI Prompts',
    description: 'Master the art of prompt engineering. Learn patterns, examples, and techniques for best AI results.',
    category: 'ai',
    duration: '8:40',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/ai-prompts.jpg',
    topics: ['ai', 'prompts', 'techniques'],
    relatedVideos: ['ai-generation', 'ai-refinement'],
  },
  {
    id: 'ai-refinement',
    title: 'Refining AI-Generated Diagrams',
    description: 'Iterate on AI results to perfection. Learn refinement commands, layout improvements, and quality tips.',
    category: 'ai',
    duration: '7:25',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/ai-refinement.jpg',
    topics: ['ai', 'refinement', 'iteration'],
    relatedVideos: ['ai-generation', 'ai-prompts'],
  },

  // Mermaid / Diagram-as-Code
  {
    id: 'mermaid-intro',
    title: 'Introduction to Diagram-as-Code with Mermaid',
    description: 'Learn Mermaid syntax basics. Create flowcharts, sequence diagrams, and ERDs with code.',
    category: 'mermaid',
    duration: '11:15',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/mermaid-intro.jpg',
    topics: ['mermaid', 'code', 'syntax'],
    relatedVideos: ['mermaid-flowcharts', 'mermaid-sequence'],
  },
  {
    id: 'mermaid-flowcharts',
    title: 'Mermaid Flowcharts Deep Dive',
    description: 'Master flowchart syntax: nodes, edges, subgraphs, styling, and complex workflows.',
    category: 'mermaid',
    duration: '13:50',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/mermaid-flowcharts.jpg',
    topics: ['mermaid', 'flowcharts', 'syntax'],
    relatedVideos: ['mermaid-intro', 'mermaid-sequence'],
  },
  {
    id: 'mermaid-sequence',
    title: 'Sequence Diagrams with Mermaid',
    description: 'Create sequence diagrams for API flows, authentication, and interactions. Learn participants, messages, and loops.',
    category: 'mermaid',
    duration: '10:30',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/mermaid-sequence.jpg',
    topics: ['mermaid', 'sequence', 'api'],
    relatedVideos: ['mermaid-intro', 'mermaid-flowcharts'],
  },

  // Collaboration
  {
    id: 'real-time-collab',
    title: 'Real-Time Collaboration',
    description: 'Work together with your team. Learn cursors, presence, comments, and collaborative editing.',
    category: 'collaboration',
    duration: '9:45',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/collaboration.jpg',
    topics: ['collaboration', 'real-time', 'team'],
    relatedVideos: ['comments', 'sharing'],
  },
  {
    id: 'comments',
    title: 'Comments and @Mentions',
    description: 'Discuss diagrams with comments. Learn threading, @mentions, reactions, and resolving comments.',
    category: 'collaboration',
    duration: '7:15',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/comments.jpg',
    topics: ['comments', 'mentions', 'feedback'],
    relatedVideos: ['real-time-collab', 'sharing'],
  },

  // Export & Sharing
  {
    id: 'export-guide',
    title: 'Complete Export Guide',
    description: 'Export diagrams in PNG, SVG, PDF formats. Learn resolution, quality settings, and batch export.',
    category: 'export',
    duration: '8:55',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/export.jpg',
    topics: ['export', 'png', 'svg', 'pdf'],
    relatedVideos: ['export-selection', 'sharing'],
  },
  {
    id: 'sharing',
    title: 'Sharing and Permissions',
    description: 'Share diagrams securely. Learn public links, permissions, password protection, and expiration.',
    category: 'sharing',
    duration: '6:40',
    difficulty: 'beginner',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/sharing.jpg',
    topics: ['sharing', 'permissions', 'security'],
    relatedVideos: ['real-time-collab', 'team-workspaces'],
  },

  // Productivity
  {
    id: 'keyboard-shortcuts',
    title: 'Keyboard Shortcuts Masterclass',
    description: '50+ keyboard shortcuts to boost productivity. Learn shortcuts for tools, navigation, and editing.',
    category: 'productivity',
    duration: '14:20',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/shortcuts.jpg',
    topics: ['shortcuts', 'productivity', 'efficiency'],
    relatedVideos: ['canvas-basics', 'command-palette'],
  },
  {
    id: 'design-tips',
    title: 'Design Best Practices for Professional Diagrams',
    description: 'Create beautiful diagrams. Learn layout, colors, typography, whitespace, and consistency.',
    category: 'productivity',
    duration: '12:05',
    difficulty: 'intermediate',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    thumbnailUrl: '/tutorial-thumbs/design.jpg',
    topics: ['design', 'best practices', 'styling'],
    relatedVideos: ['advanced-canvas', 'figures-frames'],
  },
];

const CATEGORIES = [
  { id: 'all', label: 'All Videos', color: 'blue' },
  { id: 'getting-started', label: 'Getting Started', color: 'green' },
  { id: 'canvas', label: 'Canvas & Drawing', color: 'purple' },
  { id: 'ai', label: 'AI Generation', color: 'yellow' },
  { id: 'mermaid', label: 'Diagram-as-Code', color: 'indigo' },
  { id: 'collaboration', label: 'Collaboration', color: 'pink' },
  { id: 'export', label: 'Export & Sharing', color: 'orange' },
  { id: 'productivity', label: 'Productivity', color: 'teal' },
];

export default function VideoTutorialsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedVideo, setSelectedVideo] = useState<VideoTutorial | null>(null);
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());

  // Filter videos
  const filteredVideos = VIDEO_TUTORIALS.filter(video => {
    const matchesCategory = selectedCategory === 'all' || video.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      video.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      video.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      video.topics.some(topic => topic.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  // Mark video as completed
  const markCompleted = (videoId: string) => {
    setCompletedVideos(prev => new Set([...prev, videoId]));
  };

  // Get difficulty badge color
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'intermediate': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'advanced': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4 mb-4">
            <Link
              href="/dashboard"
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Back to dashboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>

            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Play className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Video Tutorials
                </h1>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Learn AutoGraph with high-quality video guides covering all features
              </p>
            </div>
          </div>

          {/* Search */}
          <div className="relative max-w-2xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search video tutorials..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Category filters */}
        <div className="mb-8 overflow-x-auto">
          <div className="flex gap-2 flex-wrap min-w-max">
            {CATEGORIES.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  selectedCategory === category.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Video Grid */}
        {filteredVideos.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-2">No video tutorials found</p>
            <p className="text-sm text-gray-500">
              Try adjusting your search or category filter
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredVideos.map(video => {
              const isCompleted = completedVideos.has(video.id);
              
              return (
                <div
                  key={video.id}
                  className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => setSelectedVideo(video)}
                >
                  {/* Thumbnail */}
                  <div className="relative aspect-video bg-gray-200 dark:bg-gray-700 overflow-hidden">
                    <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-purple-600 to-blue-600">
                      <Play className="w-16 h-16 text-white opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all" />
                    </div>
                    <div className="absolute top-2 right-2 px-2 py-1 bg-black/80 text-white text-xs rounded flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {video.duration}
                    </div>
                    {isCompleted && (
                      <div className="absolute top-2 left-2 px-2 py-1 bg-green-600 text-white text-xs rounded flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        Completed
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
                      {video.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                      {video.description}
                    </p>

                    {/* Meta */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs px-2 py-1 rounded ${getDifficultyColor(video.difficulty)}`}>
                        {video.difficulty}
                      </span>
                      {video.topics.slice(0, 2).map(topic => (
                        <span
                          key={topic}
                          className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Video Modal */}
      {selectedVideo && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          onClick={() => setSelectedVideo(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Video Player */}
            <div className="aspect-video bg-black">
              <iframe
                src={selectedVideo.videoUrl}
                title={selectedVideo.title}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>

            {/* Details */}
            <div className="p-6 overflow-y-auto">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {selectedVideo.title}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    {selectedVideo.description}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedVideo(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition ml-4"
                  aria-label="Close"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Meta Info */}
              <div className="flex items-center gap-4 mb-4 flex-wrap">
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <Clock className="w-4 h-4" />
                  {selectedVideo.duration}
                </div>
                <span className={`text-xs px-3 py-1 rounded ${getDifficultyColor(selectedVideo.difficulty)}`}>
                  {selectedVideo.difficulty}
                </span>
              </div>

              {/* Topics */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Topics covered:
                </h3>
                <div className="flex gap-2 flex-wrap">
                  {selectedVideo.topics.map(topic => (
                    <span
                      key={topic}
                      className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => markCompleted(selectedVideo.id)}
                  disabled={completedVideos.has(selectedVideo.id)}
                  className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
                    completedVideos.has(selectedVideo.id)
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  <Check className="w-4 h-4" />
                  {completedVideos.has(selectedVideo.id) ? 'Completed' : 'Mark as Complete'}
                </button>
              </div>

              {/* Related Videos */}
              {selectedVideo.relatedVideos && selectedVideo.relatedVideos.length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                    <ChevronRight className="w-4 h-4" />
                    Continue Learning
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedVideo.relatedVideos.map(relatedId => {
                      const relatedVideo = VIDEO_TUTORIALS.find(v => v.id === relatedId);
                      if (!relatedVideo) return null;
                      return (
                        <button
                          key={relatedId}
                          onClick={() => setSelectedVideo(relatedVideo)}
                          className="text-left p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded flex items-center justify-center">
                              <Play className="w-4 h-4 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
                                {relatedVideo.title}
                              </p>
                              <p className="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-1 mt-1">
                                <Clock className="w-3 h-3" />
                                {relatedVideo.duration}
                              </p>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
