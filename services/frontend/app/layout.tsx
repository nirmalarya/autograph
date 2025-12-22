import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../src/styles/globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AutoGraph v3 - AI-Powered Diagramming Platform',
  description: 'Create professional diagrams with AI assistance. Architecture diagrams, flowcharts, ERDs, and more.',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
