export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          AutoGraph v3
        </h1>
        <p className="text-xl text-center mb-4">
          AI-Powered Diagramming Platform
        </p>
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">Canvas Drawing</h2>
            <p className="text-gray-600">
              Professional canvas with TLDraw integration
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">Diagram-as-Code</h2>
            <p className="text-gray-600">
              Mermaid.js support for all diagram types
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">AI Generation</h2>
            <p className="text-gray-600">
              Generate diagrams from natural language
            </p>
          </div>
        </div>
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 mb-6">
            Status: Infrastructure Ready ✅
          </p>
          <div className="flex gap-4 justify-center">
            <a
              href="/register"
              className="px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
            >
              Get Started
            </a>
            <a
              href="/login"
              className="px-6 py-3 bg-gray-200 text-gray-800 rounded-md font-medium hover:bg-gray-300 transition"
            >
              Sign In
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
