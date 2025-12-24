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

// Branding configuration - supports white-label branding via environment variables
const isCustomBranding = process.env.NEXT_PUBLIC_ENABLE_CUSTOM_BRANDING === 'true';
const logoUrl = isCustomBranding ? (process.env.NEXT_PUBLIC_CUSTOM_LOGO_URL || '/icons/icon-192x192.png') : '/icons/icon-192x192.png';
const primaryColor = isCustomBranding ? (process.env.NEXT_PUBLIC_PRIMARY_COLOR || '#3b82f6') : '#3b82f6';
const secondaryColor = isCustomBranding ? (process.env.NEXT_PUBLIC_SECONDARY_COLOR || '#2563eb') : '#2563eb';
const productName = isCustomBranding ? (process.env.NEXT_PUBLIC_PRODUCT_NAME || 'AutoGraph') : 'AutoGraph';
const companyName = isCustomBranding ? (process.env.NEXT_PUBLIC_COMPANY_NAME || 'AutoGraph') : 'AutoGraph';

export const metadata: Metadata = {
  title: `${productName} - AI-Powered Diagramming Platform`,
  description: `Create professional diagrams with AI assistance. Architecture diagrams, flowcharts, ERDs, and more. ${isCustomBranding ? `Powered by ${companyName}.` : ''}`,
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
  // Inject brand colors as CSS custom properties
  const brandStyles = isCustomBranding ? {
    '--brand-primary-color': primaryColor,
    '--brand-secondary-color': secondaryColor,
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
