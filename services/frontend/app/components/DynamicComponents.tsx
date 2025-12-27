'use client';

import dynamic from 'next/dynamic';

// Lazy load heavy components that aren't needed for initial page render
export const PWAInstaller = dynamic(() => import('./PWAInstaller'), { ssr: false });
export const PushNotifications = dynamic(() => import('./PushNotifications'), { ssr: false });
export const OfflineStatusBanner = dynamic(() => import('./OfflineStatusBanner'), { ssr: false });
export const WelcomeTour = dynamic(() => import('./WelcomeTour'), { ssr: false });
export const InteractiveTutorial = dynamic(() => import('./InteractiveTutorial'), { ssr: false });
export const GlobalHelpCenter = dynamic(() => import('./GlobalHelpCenter'), { ssr: false });
export const ContextualTooltipsSettings = dynamic(() => import('./ContextualTooltips').then(mod => mod.ContextualTooltipsSettings), { ssr: false });
export const ContextualTooltipsToggle = dynamic(() => import('./ContextualTooltips').then(mod => mod.ContextualTooltipsToggle), { ssr: false });
export const NotificationCenter = dynamic(() => import('./NotificationSystem').then(mod => mod.NotificationCenter), { ssr: false });
