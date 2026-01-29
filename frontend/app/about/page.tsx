'use client';

import React from 'react';
import Link from 'next/link';

export default function AboutPage() {
    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
            {/* Header */}
            <header className="border-b border-purple-500/30 backdrop-blur-sm bg-black/20 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/">
                        <div className="cursor-pointer hover:opacity-80 transition-opacity">
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                                زرقاء اليمامة
                            </h1>
                            <p className="text-xs text-purple-300/70">Zarqa al Yamama • Foresight Intelligence</p>
                        </div>
                    </Link>
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <button className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/40 rounded-lg text-sm transition-all border border-purple-500/30">
                                ← Back to Dashboard
                            </button>
                        </Link>
                    </div>
                </div>
            </header>

            <div className="max-w-4xl mx-auto px-6 py-12">
                <div className="mb-12 text-center">
                    <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                        System Architecture & Methodology
                    </h2>
                    <p className="text-gray-400 text-lg">
                        A detailed technical walkthrough of how Zarqa al Yamama generates foresight.
                    </p>
                </div>

                {/* System Overview */}
                <section className="mb-12 space-y-6">
                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-8">
                        <h3 className="text-2xl font-bold text-purple-300 mb-4">🔮 System Overview</h3>
                        <p className="text-gray-300 leading-relaxed mb-4">
                            Zarqa al Yamama is a multi-agent foresight system that synthesizes real-time data from financial markets,
                            geopolitical news, think tanks, and trusted walled-garden sources. It uses a graph-based workflow (LangGraph)
                            to coordinate specialized AI agents that run in parallel and then converge to build a single shared forecast state.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                            <div className="bg-black/20 p-4 rounded-xl border border-purple-500/20">
                                <h4 className="font-semibold text-purple-400 mb-2">Backend</h4>
                                <p className="text-sm text-gray-400">FastAPI + LangGraph (Python). Manages the workflow orchestration, agent execution, and data aggregation.</p>
                            </div>
                            <div className="bg-black/20 p-4 rounded-xl border border-purple-500/20">
                                <h4 className="font-semibold text-pink-400 mb-2">Frontend</h4>
                                <p className="text-sm text-gray-400">Next.js + Tailwind CSS. Provides a reactive dashboard for scenario input and real-time report visualization.</p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Agent Workflow */}
                <section className="mb-12">
                    <h3 className="text-2xl font-bold text-white mb-6 pl-2 border-l-4 border-purple-500">
                        🤖 Multi-Agent Workflow
                    </h3>

                    <div className="space-y-6">
                        {/* Phase 1: Ingestion */}
                        <div className="bg-white/5 rounded-xl border border-white/10 p-6 transition-all hover:border-purple-500/40">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold">1</span>
                                <h4 className="text-xl font-semibold text-blue-300">Data Ingestion & Analysis</h4>
                            </div>
                            <p className="text-gray-300 mb-4">Several agents run in parallel to gather diverse intelligence:</p>
                            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-400">
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span><strong>Market Classifier:</strong> Determines if the scenario is financial or geopolitical.</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span><strong>Context Interpreter:</strong> Analyzes sentiments and narratives from global news (NewsAPI, GNews, GDELT).</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span><strong>Think Tank Analyst:</strong> Scrapes insights from Brookings, RAND, Carnegie, and major policy institutes.</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-400">•</span>
                                    <span><strong>Walled Garden Analyst:</strong> Performs restricted searches on a "safe list" of trusted domains.</span>
                                </li>
                            </ul>
                        </div>

                        {/* Phase 2: Synthesis */}
                        <div className="bg-white/5 rounded-xl border border-white/10 p-6 transition-all hover:border-purple-500/40">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold">2</span>
                                <h4 className="text-xl font-semibold text-purple-300">Synthesis & Forecasting</h4>
                            </div>
                            <p className="text-gray-300 mb-4">
                                The <strong>Quantifier</strong> and <strong>Scenario Modeler</strong> agents fuse qualitative and quantitative data.
                            </p>
                            <div className="bg-black/20 p-4 rounded-lg text-sm text-gray-300 font-mono border-l-2 border-purple-500">
                                Final_Forecast = Base_Trend × (1 + Sentiment_Score × Risk_Weight × Volatility_Factor)
                            </div>
                        </div>

                        {/* Phase 3: Validation */}
                        <div className="bg-white/5 rounded-xl border border-white/10 p-6 transition-all hover:border-purple-500/40">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 font-bold">3</span>
                                <h4 className="text-xl font-semibold text-green-300">Governance & Reporting</h4>
                            </div>
                            <p className="text-gray-300 mb-4">Before outputting results, the system applies rigorous checks:</p>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span>
                                    <strong>Critic Agent:</strong> Validates sources, flags biases, and ensures evidence quality.
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span>
                                    <strong>Governor Agent:</strong> Applies ethical guardrails and generates an audit log.
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="text-green-400">✓</span>
                                    <strong>Report Writer:</strong> Generates bilingual (English/Arabic) reports in TXT and PDF formats.
                                </li>
                            </ul>
                        </div>
                    </div>
                </section>

                {/* Tech Stack */}
                <section className="mb-12">
                    <h3 className="text-2xl font-bold text-white mb-6">🛠️ Technology Stack</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-white/5 p-4 rounded-xl text-center border border-white/5 hover:bg-white/10 transition-colors">
                            <div className="text-2xl mb-2">🐍</div>
                            <div className="font-bold text-white">Python</div>
                            <div className="text-xs text-gray-500">Backend Core</div>
                        </div>
                        <div className="bg-white/5 p-4 rounded-xl text-center border border-white/5 hover:bg-white/10 transition-colors">
                            <div className="text-2xl mb-2">⚛️</div>
                            <div className="font-bold text-white">React/Next.js</div>
                            <div className="text-xs text-gray-500">Frontend UI</div>
                        </div>
                        <div className="bg-white/5 p-4 rounded-xl text-center border border-white/5 hover:bg-white/10 transition-colors">
                            <div className="text-2xl mb-2">🕸️</div>
                            <div className="font-bold text-white">LangGraph</div>
                            <div className="text-xs text-gray-500">Agent Orchestration</div>
                        </div>
                        <div className="bg-white/5 p-4 rounded-xl text-center border border-white/5 hover:bg-white/10 transition-colors">
                            <div className="text-2xl mb-2">⚡</div>
                            <div className="font-bold text-white">FastAPI</div>
                            <div className="text-xs text-gray-500">API Layer</div>
                        </div>
                    </div>
                </section>

                <div className="text-center mt-12 pt-8 border-t border-purple-500/20">
                    <p className="text-gray-500 text-sm">
                        Designed for advanced foresight capabilities using hybrid LLM-quantitative analysis.
                    </p>
                </div>
            </div>
        </main>
    );
}
