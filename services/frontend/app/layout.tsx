import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import '../src/styles/globals.css';
import { ThemeProvider } from './components/ThemeProvider';
import PWAInstaller from './components/PWAInstaller';
import PushNotifications from './components/PushNotifications';

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
        <ThemeProvider>
          <PWAInstaller />
          <PushNotifications />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
