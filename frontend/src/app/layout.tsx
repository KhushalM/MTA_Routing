import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../styles/globals.css'
import { Header } from '@/components/Header'
import { Footer } from '@/components/Footer'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'X-Query | Real-time Twitter Analysis',
  description: 'MCP-Powered Agentic RAG for Twitter Analysis and Insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex-col">
          {/* Make the header fixed at the top, always visible */}
          <div className="fixed top-0 left-0 w-full z-30 shadow bg-background">
            <Header />
          </div>
          {/* Add padding top to main to prevent content being hidden under header */}
          <main className="flex-grow mx-auto pt-20">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
