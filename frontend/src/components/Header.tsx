"use client"

import { useState } from "react"
import Link from "next/link"
import { ThemeToggle } from "./ThemeToggle"
import { Menu, X } from "lucide-react"
import { usePathname } from "next/navigation"
import cn from "classnames"

export function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const pathname = usePathname()

  return (
    <header className="bg-white dark:bg-secondary-900 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="text-2xl font-bold text-primary-600">
                MCP Client
              </Link>
            </div>
            <nav className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                href="/"
                className={cn(
                  "border-transparent text-secondary-500 dark:text-secondary-300 hover:border-primary-500 hover:text-secondary-700 dark:hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium",
                  pathname === "/" && "border-primary-500 text-secondary-700 dark:text-white"
                )}
              >
                Home
              </Link>
              <Link
                href="/features"
                className={cn(
                  "border-transparent text-secondary-500 dark:text-secondary-300 hover:border-primary-500 hover:text-secondary-700 dark:hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium",
                  pathname === "/features" && "border-primary-500 text-secondary-700 dark:text-white"
                )}
              >
                Features
              </Link>
            </nav>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <ThemeToggle />
            <div className="ml-4">
              <Link
                href="/app"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Get Started
              </Link>
            </div>
          </div>
          <div className="-mr-2 flex items-center sm:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-secondary-400 hover:text-secondary-500 hover:bg-secondary-100 dark:hover:bg-secondary-800 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            >
              <span className="sr-only">Open main menu</span>
              {isMenuOpen ? (
                <X className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu, show/hide based on menu state */}
      {isMenuOpen && (
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            <Link
              href="/"
              className="bg-secondary-50 dark:bg-secondary-800 border-primary-500 text-primary-700 dark:text-white block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </Link>
            <Link
              href="/features"
              className="border-transparent text-secondary-500 dark:text-secondary-300 hover:bg-secondary-50 dark:hover:bg-secondary-800 hover:border-primary-500 hover:text-secondary-700 dark:hover:text-white block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Features
            </Link>
          </div>
          <div className="pt-4 pb-3 border-t border-secondary-200 dark:border-secondary-700">
            <div className="flex items-center px-4">
              <div className="flex-shrink-0">
                <ThemeToggle />
              </div>
              <div className="ml-3">
                <Link
                  href="/app"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
