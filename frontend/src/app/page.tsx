"use client"

import * as React from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import Image from "next/image"
import { Check, Circle, X } from "lucide-react"

// Hero Section Component
const Hero = ({
  title,
  description,
  image,
  ctaText,
  ctaLink,
  secondaryCtaText,
  secondaryCtaLink,
}) => {
  return (
    <div className="relative overflow-hidden bg-white dark:bg-secondary-900">
      <div className="mx-auto max-w-7xl">
        <div className="relative z-10 bg-white dark:bg-secondary-900 pb-8 sm:pb-16 md:pb-20 lg:w-full lg:max-w-2xl lg:pb-28 xl:pb-32">
          <svg
            className="absolute inset-y-0 right-0 hidden h-full w-48 translate-x-1/2 transform text-white dark:text-secondary-900 lg:block"
            fill="currentColor"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <polygon points="50,0 100,0 50,100 0,100" />
          </svg>

          <main className="mx-auto mt-10 max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
            <div className="sm:text-center lg:text-left">
              <h1 className="text-4xl font-extrabold tracking-tight text-secondary-900 dark:text-white sm:text-5xl md:text-6xl">
                <span className="block xl:inline">{title.split(' ').slice(0, 3).join(' ')}</span>{' '}
                <span className="block text-primary-600 xl:inline">
                  {title.split(' ').slice(3).join(' ')}
                </span>
              </h1>
              <p className="mt-3 text-base text-secondary-500 dark:text-secondary-300 sm:mx-auto sm:mt-5 sm:max-w-xl sm:text-lg md:mt-5 md:text-xl lg:mx-0">
                {description}
              </p>
              <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                <div className="rounded-md shadow">
                  <Link
                    href={ctaLink}
                    className="flex w-full items-center justify-center rounded-md border border-transparent bg-primary-600 px-8 py-3 text-base font-medium text-white hover:bg-primary-700 md:py-4 md:px-10 md:text-lg"
                  >
                    {ctaText}
                  </Link>
                </div>
                <div className="mt-3 sm:mt-0 sm:ml-3">
                  <Link
                    href={secondaryCtaLink}
                    className="flex w-full items-center justify-center rounded-md border border-transparent bg-secondary-100 dark:bg-secondary-800 px-8 py-3 text-base font-medium text-secondary-700 dark:text-secondary-200 hover:bg-secondary-200 dark:hover:bg-secondary-700 md:py-4 md:px-10 md:text-lg"
                  >
                    {secondaryCtaText}
                  </Link>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
      <div className="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
        <Image
          className="h-56 w-full object-cover sm:h-72 md:h-96 lg:h-full lg:w-full"
          src={image}
          alt="X-Query Dashboard"
          width={1920}
          height={1080}
        />
      </div>
    </div>
  )
}

// Features Section Component
const Features = ({ features }) => {
  return (
    <div className="py-12 bg-white dark:bg-secondary-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase">Features</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-secondary-900 dark:text-white sm:text-4xl">
            A better way to analyze Twitter
          </p>
          <p className="mt-4 max-w-2xl text-xl text-secondary-500 dark:text-secondary-300 lg:mx-auto">
            Get real-time insights from Twitter with our intelligent agent powered by RAG and MCP.
          </p>
        </div>

        <div className="mt-10">
          <dl className="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
            {features.map((feature) => (
              <div key={feature.name} className="relative">
                <dt>
                  <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-primary-500 text-white">
                    <feature.icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <p className="ml-16 text-lg leading-6 font-medium text-secondary-900 dark:text-white">{feature.name}</p>
                </dt>
                <dd className="mt-2 ml-16 text-base text-secondary-500 dark:text-secondary-300">{feature.description}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  )
}

// How It Works Section
const HowItWorks = ({ steps }) => {
  return (
    <div className="bg-secondary-50 dark:bg-secondary-800 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase">How It Works</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-secondary-900 dark:text-white sm:text-4xl">
            Simple yet powerful
          </p>
          <p className="mt-4 max-w-2xl text-xl text-secondary-500 dark:text-secondary-300 lg:mx-auto">
            Our intelligent agent does the heavy lifting so you don't have to.
          </p>
        </div>

        <div className="mt-10">
          <div className="relative">
            {steps.map((step, index) => (
              <div key={step.name} className="relative pb-12">
                {index !== steps.length - 1 ? (
                  <div className="absolute top-4 left-4 -ml-px mt-0.5 h-full w-0.5 bg-primary-600" aria-hidden="true" />
                ) : null}
                <div className="relative flex items-start group">
                  <span className="h-9 flex items-center">
                    <span className="relative z-10 w-8 h-8 flex items-center justify-center bg-primary-600 rounded-full group-hover:bg-primary-800">
                      <span className="text-white font-medium">{index + 1}</span>
                    </span>
                  </span>
                  <div className="ml-4 min-w-0 flex-1">
                    <h3 className="text-lg font-medium text-secondary-900 dark:text-white">{step.name}</h3>
                    <p className="text-base text-secondary-500 dark:text-secondary-300">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Demo Section
const Demo = () => {
  return (
    <div className="bg-white dark:bg-secondary-900 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase">Demo</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-secondary-900 dark:text-white sm:text-4xl">
            See X-Query in action
          </p>
          <p className="mt-4 max-w-2xl text-xl text-secondary-500 dark:text-secondary-300 lg:mx-auto">
            Watch how X-Query analyzes Twitter trends and provides insightful summaries.
          </p>
        </div>

        <div className="mt-10 bg-secondary-100 dark:bg-secondary-800 rounded-xl overflow-hidden shadow-lg">
          <div className="aspect-w-16 aspect-h-9 w-full">
            <div className="w-full h-full flex items-center justify-center">
              <div className="p-8 text-center">
                <p className="text-secondary-700 dark:text-secondary-300">Demo video coming soon!</p>
                <div className="mt-4 flex justify-center">
                  <Link
                    href="/demo"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700"
                  >
                    Try the demo
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// CTA Section
const CTA = () => {
  return (
    <div className="bg-primary-700">
      <div className="max-w-2xl mx-auto text-center py-16 px-4 sm:py-20 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
          <span className="block">Ready to dive in?</span>
          <span className="block">Start using X-Query today.</span>
        </h2>
        <p className="mt-4 text-lg leading-6 text-primary-200">
          Get real-time insights from Twitter with our intelligent agent.
        </p>
        <div className="mt-8 flex justify-center">
          <div className="inline-flex rounded-md shadow">
            <Link
              href="/app"
              className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
            >
              Get started
            </Link>
          </div>
          <div className="ml-3 inline-flex">
            <Link
              href="/docs"
              className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-800 hover:bg-primary-900"
            >
              Learn more
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

// Main Landing Page Component
const LandingPage = () => {
  // Mock data for features
  const features = [
    {
      name: 'Real-time Trend Analysis',
      description: 'Get instant insights into what\'s trending on Twitter right now.',
      icon: (props) => (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
        </svg>
      ),
    },
    {
      name: 'Intelligent Tweet Search',
      description: 'Search for tweets on any topic and get relevant results with our AI-powered search.',
      icon: (props) => (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
      ),
    },
    {
      name: 'Summarization',
      description: 'Get concise summaries of complex Twitter discussions and threads.',
      icon: (props) => (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
        </svg>
      ),
    },
    {
      name: 'MCP-Powered Agent',
      description: 'Our intelligent agent uses Model Context Protocol to reason over Twitter data and provide insights.',
      icon: (props) => (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
        </svg>
      ),
    },
  ];

  // Mock data for how it works steps
  const steps = [
    {
      name: 'Enter your query',
      description: 'Ask a question about Twitter trends or search for specific topics.',
    },
    {
      name: 'Agent retrieves data',
      description: 'Our intelligent agent uses tools to fetch relevant tweets and trending topics.',
    },
    {
      name: 'Analysis and reasoning',
      description: 'The agent analyzes the data, identifies patterns, and generates insights.',
    },
    {
      name: 'Get your insights',
      description: 'Receive a comprehensive summary with the most relevant information.',
    },
  ];

  return (
    <div>
      <Hero
        title="Real-time Twitter Analysis with AI"
        description="X-Query is an intelligent agent that uses Retrieval-Augmented Generation (RAG) and Model Context Protocol (MCP) to analyze, summarize, and provide insights on Twitter trends and tweets."
        image="/dashboard.png"
        ctaText="Get Started"
        ctaLink="/app"
        secondaryCtaText="Learn More"
        secondaryCtaLink="#features"
      />
      <Features features={features} />
      <HowItWorks steps={steps} />
      <Demo />
      <CTA />
    </div>
  )
}

export default LandingPage
