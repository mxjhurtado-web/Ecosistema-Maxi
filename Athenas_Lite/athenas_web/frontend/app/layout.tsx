"use client";

import Link from "next/link";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const handleLogout = () => {
    // Clear cookies
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost";
    document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost";
    document.cookie = "user_info=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost";
    // Redirect to login
    window.location.href = "/";
  };

  return (
    <html lang="es">
      <head>
        <title>ATHENAS Lite - Quality Analysis Platform</title>
        <meta name="description" content="AI-powered audio quality analysis for call centers" />
      </head>
      <body className={inter.className}>
        <nav className="bg-gray-900 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              {/* Logo */}
              <div className="flex items-center gap-4">
                <img
                  src="/Athenas2.png"
                  alt="ATHENAS"
                  className="h-8"
                />
                <span className="text-xl font-bold">ATHENAS Lite</span>
              </div>

              {/* Navigation Links */}
              <div className="hidden md:flex items-center gap-6">
                <Link
                  href="/dashboard"
                  className="hover:text-brand transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/results"
                  className="hover:text-brand transition-colors"
                >
                  Resultados
                </Link>
                <Link
                  href="/admin"
                  className="hover:text-brand transition-colors"
                >
                  Admin
                </Link>
                <Link
                  href="/settings"
                  className="hover:text-brand transition-colors flex items-center gap-2"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  Configuración
                </Link>
              </div>

              {/* User Menu & Logout */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <img
                    src="/Maxilogo.png"
                    alt="Maxi"
                    className="h-6"
                  />
                </div>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 bg-brand hover:bg-brand-dark rounded-lg transition-colors flex items-center gap-2"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  Cerrar Sesión
                </button>
              </div>
            </div>
          </div>
        </nav>
        <main className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
          {children}
        </main>
      </body>
    </html>
  );
}
