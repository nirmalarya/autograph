import Logo from './components/Logo';

export default function HomePage() {
  return (
    <main id="main-content" role="main" aria-label="Home page" className="flex min-h-screen flex-col items-center justify-center px-4 py-8 sm:px-8 sm:py-12 md:px-16 md:py-16 lg:p-24 bg-white dark:bg-gray-900">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        {/* Responsive Logo and Heading */}
        <div className="flex justify-center mb-4 sm:mb-6 md:mb-8">
          <Logo size="xl" showText={true} className="scale-125 sm:scale-150" />
        </div>
        <p className="text-base sm:text-lg md:text-xl text-center mb-4 text-gray-700 dark:text-gray-300">
          AI-Powered Diagramming Platform
        </p>
        
        {/* Responsive grid: 1 column on mobile, 2 on tablet, 3 on desktop */}
        <section aria-label="Features" className="mt-6 sm:mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          <article className="p-4 sm:p-5 md:p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h2 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">Canvas Drawing</h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Professional canvas with TLDraw integration
            </p>
          </article>
          <article className="p-4 sm:p-5 md:p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h2 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">Diagram-as-Code</h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Mermaid.js support for all diagram types
            </p>
          </article>
          <article className="p-4 sm:p-5 md:p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h2 className="text-lg sm:text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">AI Generation</h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Generate diagrams from natural language
            </p>
          </article>
        </section>
        
        <nav aria-label="Main navigation" className="mt-6 sm:mt-8 text-center">
          {/* Responsive buttons: stack on mobile, side-by-side on larger screens */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <a
              href="/register"
              aria-label="Get started by creating a new account"
              className="px-6 py-3 sm:px-8 sm:py-4 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition text-center text-sm sm:text-base touch-manipulation"
            >
              Get Started
            </a>
            <a
              href="/login"
              aria-label="Sign in to your existing account"
              className="px-6 py-3 sm:px-8 sm:py-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition text-center text-sm sm:text-base touch-manipulation"
            >
              Sign In
            </a>
          </div>
        </nav>
      </div>
    </main>
  );
}
