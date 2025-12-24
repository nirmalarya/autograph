'use client';

/**
 * Feature #668: Onboarding - Welcome Tour
 * 
 * A comprehensive guided tour for new users that highlights key features
 * and helps them get started with AutoGraph.
 * 
 * Features:
 * - Multi-step interactive tour
 * - Spotlight highlighting of UI elements
 * - Skip/dismiss functionality
 * - Progress indicator
 * - Keyboard navigation (arrow keys, Esc)
 * - Persistent state (localStorage)
 * - Responsive design
 * - Accessibility (ARIA labels, focus management)
 * - Dark mode support
 */

import { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react';

interface TourStep {
  id: string;
  title: string;
  description: string;
  targetSelector?: string; // CSS selector for element to highlight
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: {
    label: string;
    href?: string;
  };
}

const TOUR_STEPS: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to AutoGraph! 🎉',
    description: 'Let\'s take a quick tour to help you get started with our AI-powered diagramming platform. This will only take a minute.',
    position: 'center',
  },
  {
    id: 'dashboard',
    title: 'Your Dashboard',
    description: 'This is your central hub where you can see all your diagrams, recent files, starred items, and shared documents.',
    targetSelector: 'main',
    position: 'center',
  },
  {
    id: 'create',
    title: 'Create Diagrams',
    description: 'Click "Get Started" or "New Diagram" to create your first diagram. You can choose between canvas drawing, Mermaid code, or AI generation.',
    targetSelector: 'a[href="/register"], a[href="/dashboard"]',
    position: 'bottom',
    action: {
      label: 'Create Your First Diagram',
      href: '/dashboard',
    },
  },
  {
    id: 'ai-generation',
    title: 'AI-Powered Generation',
    description: 'Describe your diagram in natural language and our AI will generate it for you. Supports architecture diagrams, flowcharts, ERDs, and more.',
    position: 'center',
  },
  {
    id: 'canvas',
    title: 'Professional Canvas',
    description: 'Use our powerful canvas editor with drawing tools, shapes, icons, and real-time collaboration features.',
    position: 'center',
  },
  {
    id: 'mermaid',
    title: 'Diagram-as-Code',
    description: 'Write diagrams using Mermaid syntax with live preview, syntax highlighting, and auto-completion.',
    position: 'center',
  },
  {
    id: 'collaboration',
    title: 'Real-Time Collaboration',
    description: 'Work together with your team in real-time. See cursors, selections, and changes as they happen.',
    position: 'center',
  },
  {
    id: 'export',
    title: 'Export & Share',
    description: 'Export your diagrams as PNG, SVG, or PDF. Share with team members or create public links.',
    position: 'center',
  },
  {
    id: 'complete',
    title: 'You\'re All Set! ✨',
    description: 'You\'re ready to start creating amazing diagrams. Need help? Check out our documentation or use the keyboard shortcut ⌘K to access the command palette.',
    position: 'center',
    action: {
      label: 'Start Creating',
      href: '/dashboard',
    },
  },
];

const STORAGE_KEY = 'autograph-welcome-tour-completed';

export default function WelcomeTour() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  // Check if tour has been completed
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const tourCompleted = localStorage.getItem(STORAGE_KEY);
      if (!tourCompleted) {
        // Small delay to let the page load
        setTimeout(() => setIsOpen(true), 1000);
      }
    }
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleSkip();
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        handlePrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStep]);

  // Focus management
  useEffect(() => {
    if (isOpen) {
      // Focus the tour dialog
      const dialog = document.querySelector('[role="dialog"]') as HTMLElement;
      dialog?.focus();
    }
  }, [isOpen, currentStep]);

  const handleNext = useCallback(() => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentStep(prev => prev + 1);
        setIsAnimating(false);
      }, 200);
    } else {
      handleComplete();
    }
  }, [currentStep]);

  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentStep(prev => prev - 1);
        setIsAnimating(false);
      }, 200);
    }
  }, [currentStep]);

  const handleSkip = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, 'skipped');
    }
    setIsOpen(false);
  }, []);

  const handleComplete = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, 'completed');
    }
    setIsOpen(false);
  }, []);

  const handleRestart = useCallback(() => {
    setCurrentStep(0);
    setIsOpen(true);
  }, []);

  if (!isOpen) return null;

  const step = TOUR_STEPS[currentStep];
  const progress = ((currentStep + 1) / TOUR_STEPS.length) * 100;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === TOUR_STEPS.length - 1;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-[9998] transition-opacity duration-300"
        onClick={handleSkip}
        aria-hidden="true"
      />

      {/* Spotlight highlight for targeted elements */}
      {step.targetSelector && (
        <div
          className="fixed z-[9999] pointer-events-none"
          style={{
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.5)',
            borderRadius: '8px',
            transition: 'all 300ms ease-in-out',
          }}
          aria-hidden="true"
        />
      )}

      {/* Tour Dialog */}
      <div
        role="dialog"
        aria-labelledby="tour-title"
        aria-describedby="tour-description"
        aria-modal="true"
        tabIndex={-1}
        className={`
          fixed z-[10000] bg-white dark:bg-gray-800 rounded-lg shadow-2xl
          max-w-md w-full mx-4 p-6
          transition-all duration-300 ease-in-out
          ${isAnimating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}
          ${step.position === 'center' ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2' : ''}
          ${step.position === 'top' ? 'top-20 left-1/2 -translate-x-1/2' : ''}
          ${step.position === 'bottom' ? 'bottom-20 left-1/2 -translate-x-1/2' : ''}
          ${step.position === 'left' ? 'left-8 top-1/2 -translate-y-1/2' : ''}
          ${step.position === 'right' ? 'right-8 top-1/2 -translate-y-1/2' : ''}
        `}
      >
        {/* Close Button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors touch-target-small"
          aria-label="Skip tour"
          title="Skip tour (Esc)"
        >
          <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
        </button>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-valuenow={currentStep + 1}
              aria-valuemin={1}
              aria-valuemax={TOUR_STEPS.length}
              aria-label={`Step ${currentStep + 1} of ${TOUR_STEPS.length}`}
            />
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
            Step {currentStep + 1} of {TOUR_STEPS.length}
          </div>
        </div>

        {/* Content */}
        <div className="mb-6">
          <h2
            id="tour-title"
            className="text-2xl font-bold mb-3 text-gray-900 dark:text-gray-100"
          >
            {step.title}
          </h2>
          <p
            id="tour-description"
            className="text-base text-gray-600 dark:text-gray-300 leading-relaxed"
          >
            {step.description}
          </p>
        </div>

        {/* Action Button (if provided) */}
        {step.action && (
          <div className="mb-4">
            <a
              href={step.action.href}
              onClick={handleComplete}
              className="block w-full px-4 py-3 bg-blue-600 dark:bg-blue-700 text-white rounded-md font-medium hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors text-center touch-target-medium"
            >
              {step.action.label}
            </a>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between gap-3">
          <button
            onClick={handlePrevious}
            disabled={isFirstStep}
            className="flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors touch-target-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
            aria-label="Previous step"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>

          <button
            onClick={handleSkip}
            className="px-4 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors touch-target-medium"
            aria-label="Skip tour"
          >
            Skip Tour
          </button>

          <button
            onClick={handleNext}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-md font-medium hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors touch-target-medium"
            aria-label={isLastStep ? 'Complete tour' : 'Next step'}
          >
            {isLastStep ? (
              <>
                Complete
                <Check className="w-4 h-4" />
              </>
            ) : (
              <>
                Next
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Keyboard Hints */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Use arrow keys to navigate • Press Esc to skip
          </p>
        </div>
      </div>
    </>
  );
}

/**
 * Hook to manually trigger the welcome tour
 * Useful for "Show Tour Again" buttons in settings
 */
export function useWelcomeTour() {
  const restartTour = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
      window.location.reload();
    }
  }, []);

  const hasCompletedTour = useCallback(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(STORAGE_KEY) !== null;
    }
    return false;
  }, []);

  return {
    restartTour,
    hasCompletedTour,
  };
}
