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
import InteractiveTutorial from './components/InteractiveTutorial';
import GlobalHelpCenter from './components/GlobalHelpCenter';
import { ContextualTooltipsProvider, ContextualTooltipsSettings, ContextualTooltipsToggle } from './components/ContextualTooltips';
import { NotificationProvider, NotificationCenter } from './components/NotificationSystem';

const inter = Inter({ subsets: ['latin'] });

// Branding configuration - supports Bayer branding via environment variables
const isBayerBranding = process.env.NEXT_PUBLIC_ENABLE_BAYER_BRANDING === 'true';
const logoUrl = isBayerBranding ? (process.env.NEXT_PUBLIC_BAYER_LOGO_URL || '/bayer-logo.svg') : '/icons/icon-192x192.png';
const primaryColor = isBayerBranding ? (process.env.NEXT_PUBLIC_BAYER_PRIMARY_COLOR || '#00A0E3') : '#3b82f6';
const secondaryColor = isBayerBranding ? (process.env.NEXT_PUBLIC_BAYER_SECONDARY_COLOR || '#0066B2') : '#2563eb';
const productName = isBayerBranding ? 'AutoGraph v3 for Bayer' : 'AutoGraph v3';
const companyName = isBayerBranding ? 'Bayer' : 'AutoGraph';

export const metadata: Metadata = {
  title: `${productName} - AI-Powered Diagramming Platform`,
  description: `Create professional diagrams with AI assistance. Architecture diagrams, flowcharts, ERDs, and more. ${isBayerBranding ? `Powered by ${companyName}.` : ''}`,
  applicationName: productName,
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: companyName,
  },
  formatDetection: {
    telephone: false,
  },
  manifest: '/manifest.json',
  icons: {
    icon: logoUrl,
    apple: logoUrl,
  },
};

export const viewport: Viewport = {
  themeColor: primaryColor,
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
  // Inject Bayer brand colors as CSS custom properties
  const brandStyles = isBayerBranding ? {
    '--bayer-primary-color': primaryColor,
    '--bayer-secondary-color': secondaryColor,
  } as React.CSSProperties : {};

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content={primaryColor} />
        <link rel="apple-touch-icon" href={logoUrl} />
      </head>
      <body className={inter.className} style={brandStyles}>
        {/* Skip Navigation Link for Screen Readers and Keyboard Users */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md focus:shadow-lg"
        >
          Skip to main content
        </a>
        <ErrorBoundary>
          <ThemeProvider>
            <NotificationProvider>
              <ContextualTooltipsProvider defaultEnabled={true}>
                <OfflineStatusBanner />
                <PWAInstaller />
                <PushNotifications />
                <WelcomeTour />
                <InteractiveTutorial />
                <GlobalHelpCenter />
                <ContextualTooltipsToggle />
                <ContextualTooltipsSettings />
                <NotificationCenter />
                <PageTransition>
                  {children}
                </PageTransition>
              </ContextualTooltipsProvider>
            </NotificationProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
