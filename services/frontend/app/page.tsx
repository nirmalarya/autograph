export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-8 sm:px-8 sm:py-12 md:px-16 md:py-16 lg:p-24 bg-white dark:bg-gray-900">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        {/* Responsive heading - smaller on mobile */}
        <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-center mb-4 sm:mb-6 md:mb-8 text-gray-900 dark:text-gray-100">
          AutoGraph v3
        </h1>
        <p className="text-base sm:text-lg md:text-xl text-center mb-4 text-gray-700 dark:text-gray-300">
          AI-Powered Diagramming Platform
        </p>
        
        {/* Responsive grid: 1 column on mobile, 2 on tablet, 3 on desktop */}
        <div className="mt-6 sm:mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          <div className="p-4 sm:p-5 md:p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h2 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">Canvas Drawing</h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Professional canvas with TLDraw integration
            </p>
          </div>
          <div className="p-4 sm:p-5 md:p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h2 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">Diagram-as-Code</h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Mermaid.js support for all diagram types
            </p>
          </div>
          <div className="p-4 sm:p-5 md:p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h2 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">AI Generation</h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Generate diagrams from natural language
            </p>
          </div>
        </div>
        
        <div className="mt-6 sm:mt-8 text-center">
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mb-4 sm:mb-6">
            Status: Infrastructure Ready ✅
          </p>
          {/* Responsive buttons: stack on mobile, side-by-side on larger screens */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <a
              href="/register"
              className="px-6 py-3 sm:px-8 sm:py-4 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition text-center text-sm sm:text-base touch-manipulation"
            >
              Get Started
            </a>
            <a
              href="/login"
              className="px-6 py-3 sm:px-8 sm:py-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition text-center text-sm sm:text-base touch-manipulation"
            >
              Sign In
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
