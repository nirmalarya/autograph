import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import '../src/styles/globals.css';
import { ThemeProvider } from './components/ThemeProvider';
import PWAInstaller from './components/PWAInstaller';
import PushNotifications from './components/PushNotifications';
import OfflineStatusBanner from './components/OfflineStatusBanner';
import ErrorBoundary from './components/ErrorBoundary';
import PageTransition from './components/PageTransition';
import WelcomeTour from './components/WelcomeTour';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AutoGraph v3 - AI-Powered Diagramming Platform',
  description: 'Create professional diagrams with AI assistance. Architecture diagrams, flowcharts, ERDs, and more.',
  applicationName: 'AutoGraph v3',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'AutoGraph',
  },
  formatDetection: {
    telephone: false,
  },
  manifest: '/manifest.json',
  icons: {
    icon: '/icons/icon-192x192.png',
    apple: '/icons/icon-192x192.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#3b82f6',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#3b82f6" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
      </head>
      <body className={inter.className}>
        {/* Skip Navigation Link for Screen Readers and Keyboard Users */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md focus:shadow-lg"
        >
          Skip to main content
        </a>
        <ErrorBoundary>
          <ThemeProvider>
            <OfflineStatusBanner />
            <PWAInstaller />
            <PushNotifications />
            <WelcomeTour />
            <PageTransition>
              {children}
            </PageTransition>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
