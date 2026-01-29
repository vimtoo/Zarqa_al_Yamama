'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface ForecastResult {
    request_id: string;
    scenario: string;
    temporal_forecast: {
        metric: string;
        current_value: number;
        forecast_30d: number;
        confidence_30d: number;
    };
    context_sentiment: {
        sentiment_score: number;
        narrative_momentum: string;
        mentions_24h: number;
    };
    quantified_forecast: {
        final_forecast: number;
        final_confidence: number;
        adjustment_rationale: string;
    };
    executive_summary: string;
    strategic_recommendation: string;
    weak_signals: Array<{
        signal: string;
        source: string;
        impact: string;
    }>;
    agents_executed: string[];
    processing_time_ms: number;
    errors: string[];
    warnings: string[];
    report_path?: string;
    report_filename?: string;
    report_format?: string;
    report_pdf_filename?: string;
    scenario_is_market?: boolean;
    scenario_classification?: string;
    evidence_summary?: string;
    evidence_summary_ar?: string;
    evidence_confidence?: number;
    evidence_contradictions?: string[];
    evidence_contradictions_ar?: string[];
    evidence_unknowns?: string[];
    evidence_unknowns_ar?: string[];
}

export default function Home() {
    const [scenario, setScenario] = useState('Middle East Oil Price');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ForecastResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const runForecast = async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
            const response = await fetch(`${apiUrl}/api/v1/forecast`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ scenario }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const downloadReport = () => {
        if (!result?.report_filename) {
            return;
        }
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const url = `${apiUrl}/api/v1/reports/${encodeURIComponent(
            result.report_filename
        )}`;
        window.open(url, '_blank', 'noopener,noreferrer');
    };



    const openReportPage = () => {
        if (!result?.report_filename) {
            return;
        }
        const params = new URLSearchParams({
            file: result.report_filename,
        });

        window.open(`/our-foresight?${params.toString()}`, '_blank', 'noopener,noreferrer');
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
            {/* Header */}
            <header className="border-b border-purple-500/30 backdrop-blur-sm bg-black/20">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                            زرقاء اليمامة
                        </h1>
                        <p className="text-xs text-purple-300/70">Zarqa al Yamama • Foresight Intelligence</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/about">
                            <button className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/40 rounded-lg text-sm transition-all border border-purple-500/30">
                                About Us
                            </button>
                        </Link>
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                            <span className="text-sm text-green-400">System Online</span>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Input Section */}
                <section className="mb-8">
                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6">
                        <h2 className="text-lg font-semibold text-purple-300 mb-4">
                            🔮 Forecast Scenario
                        </h2>
                        <div className="flex gap-4">
                            <input
                                type="text"
                                value={scenario}
                                onChange={(e) => setScenario(e.target.value)}
                                placeholder="Enter a forecast scenario (e.g., Middle East Oil Price)"
                                className="flex-1 px-4 py-3 bg-black/30 border border-purple-500/30 rounded-xl 
                                         text-white placeholder-gray-500 focus:outline-none focus:border-purple-400
                                         focus:ring-2 focus:ring-purple-400/20 transition-all"
                            />
                            <button
                                onClick={runForecast}
                                disabled={loading || !scenario.trim()}
                                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl
                                         font-semibold hover:from-purple-500 hover:to-pink-500 
                                         disabled:opacity-50 disabled:cursor-not-allowed
                                         transition-all transform hover:scale-105 active:scale-95
                                         shadow-lg shadow-purple-500/25"
                            >
                                {loading ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Processing...
                                    </span>
                                ) : (
                                    '⚡ Run Forecast'
                                )}
                            </button>
                        </div>

                        {/* Quick Scenarios */}
                        <div className="mt-4 flex flex-wrap gap-2">
                            <span className="text-xs text-gray-500">Quick scenarios:</span>
                            {['Middle East Oil Price', 'Gold Price Forecast', 'US Dollar Index', 'Saudi Aramco Stock'].map((s) => (
                                <button
                                    key={s}
                                    onClick={() => setScenario(s)}
                                    className="px-3 py-1 text-xs bg-purple-500/20 hover:bg-purple-500/30 
                                             rounded-full border border-purple-500/30 transition-colors"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Error Display */}
                {error && (
                    <div className="mb-8 p-4 bg-red-500/20 border border-red-500/50 rounded-xl">
                        <p className="text-red-400">❌ Error: {error}</p>
                    </div>
                )}

                {/* Results Section */}
                {result && (
                    <section className="space-y-6 animate-fadeIn">
                        {/* Executive Summary */}
                        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6">
                            <h2 className="text-lg font-semibold text-purple-300 mb-3">📊 Executive Summary</h2>
                            <p className="text-gray-200 leading-relaxed">{result.executive_summary}</p>
                        </div>

                        {/* Evidence Summary */}
                        {(result.evidence_summary || result.evidence_summary_ar) && (
                            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6">
                                <h2 className="text-lg font-semibold text-purple-300 mb-3">🧭 Evidence Summary</h2>
                                {result.evidence_confidence !== undefined && (
                                    <p className="text-xs text-purple-300/80 mb-2">
                                        Confidence: {(result.evidence_confidence * 100).toFixed(0)}%
                                    </p>
                                )}
                                {result.evidence_summary && (
                                    <p className="text-gray-200 leading-relaxed mb-3">
                                        {result.evidence_summary}
                                    </p>
                                )}
                                {result.evidence_summary_ar && (
                                    <p className="text-gray-300 leading-relaxed text-right">
                                        {result.evidence_summary_ar}
                                    </p>
                                )}
                            </div>
                        )}

                        {((result.evidence_contradictions?.length || 0) > 0 ||
                            (result.evidence_contradictions_ar?.length || 0) > 0 ||
                            (result.evidence_unknowns?.length || 0) > 0 ||
                            (result.evidence_unknowns_ar?.length || 0) > 0) && (
                                <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6">
                                    <h2 className="text-lg font-semibold text-purple-300 mb-3">Contradictions/Unknowns</h2>

                                    {result.evidence_contradictions?.length ? (
                                        <div className="mb-4">
                                            <p className="text-sm text-purple-300/80 mb-2">Contradictions (EN)</p>
                                            <ul className="list-disc list-inside text-gray-200 space-y-1">
                                                {result.evidence_contradictions.map((item, index) => (
                                                    <li key={`contradiction-en-${index}`}>{item}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    ) : null}

                                    {result.evidence_contradictions_ar?.length ? (
                                        <div className="mb-4 text-right">
                                            <p className="text-sm text-purple-300/80 mb-2">التناقضات (AR)</p>
                                            <ul className="list-disc list-inside text-gray-300 space-y-1">
                                                {result.evidence_contradictions_ar.map((item, index) => (
                                                    <li key={`contradiction-ar-${index}`}>{item}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    ) : null}

                                    {result.evidence_unknowns?.length ? (
                                        <div className="mb-4">
                                            <p className="text-sm text-purple-300/80 mb-2">Unknowns (EN)</p>
                                            <ul className="list-disc list-inside text-gray-200 space-y-1">
                                                {result.evidence_unknowns.map((item, index) => (
                                                    <li key={`unknown-en-${index}`}>{item}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    ) : null}

                                    {result.evidence_unknowns_ar?.length ? (
                                        <div className="text-right">
                                            <p className="text-sm text-purple-300/80 mb-2">المجهوليات (AR)</p>
                                            <ul className="list-disc list-inside text-gray-300 space-y-1">
                                                {result.evidence_unknowns_ar.map((item, index) => (
                                                    <li key={`unknown-ar-${index}`}>{item}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    ) : null}
                                </div>
                            )}

                        {/* Key Metrics Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {result.scenario_is_market === true && (
                                <>
                                    {/* Current Value */}
                                    <div className="bg-white/5 backdrop-blur-md rounded-xl border border-purple-500/20 p-5">
                                        <p className="text-sm text-gray-400 mb-1">Current Value</p>
                                        <p className="text-3xl font-bold text-white">
                                            ${result.temporal_forecast?.current_value?.toFixed(2) || 'N/A'}
                                        </p>
                                        <p className="text-xs text-purple-400 mt-1">{result.temporal_forecast?.metric}</p>
                                    </div>

                                    {/* Forecast Value */}
                                    <div className="bg-white/5 backdrop-blur-md rounded-xl border border-purple-500/20 p-5">
                                        <p className="text-sm text-gray-400 mb-1">30-Day Forecast</p>
                                        <p className="text-3xl font-bold text-green-400">
                                            ${result.quantified_forecast?.final_forecast?.toFixed(2) || 'N/A'}
                                        </p>
                                        <p className="text-xs text-purple-400 mt-1">
                                            Confidence: {((result.quantified_forecast?.final_confidence || 0) * 100).toFixed(0)}%
                                        </p>
                                    </div>
                                </>
                            )}

                            {/* Sentiment */}
                            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-purple-500/20 p-5">
                                <p className="text-sm text-gray-400 mb-1">Market Sentiment</p>
                                <p className={`text-3xl font-bold ${(result.context_sentiment?.sentiment_score || 0) > 0 ? 'text-green-400' :
                                    (result.context_sentiment?.sentiment_score || 0) < 0 ? 'text-red-400' : 'text-yellow-400'
                                    }`}>
                                    {(result.context_sentiment?.sentiment_score || 0) > 0 ? '📈 Positive' :
                                        (result.context_sentiment?.sentiment_score || 0) < 0 ? '📉 Negative' : '➡️ Neutral'}
                                </p>
                                <p className="text-xs text-purple-400 mt-1">
                                    {result.context_sentiment?.mentions_24h?.toLocaleString() || 0} mentions (24h)
                                </p>
                            </div>
                        </div>

                        {/* Strategic Recommendation */}
                        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6">
                            <h2 className="text-lg font-semibold text-purple-300 mb-3">💡 Strategic Recommendation</h2>
                            <p className="text-gray-200 leading-relaxed">{result.strategic_recommendation}</p>
                        </div>

                        {/* Report Download */}
                        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6 flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-purple-300">📝 Report</h2>
                                <p className="text-xs text-gray-500 mt-1">
                                    {result.report_filename ? result.report_filename : 'No report available'}
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={openReportPage}
                                    disabled={!result.report_filename}
                                    className="px-4 py-2 bg-white/10 rounded-lg text-sm font-semibold
                                             disabled:opacity-50 disabled:cursor-not-allowed
                                             hover:bg-white/20 transition-colors"
                                >
                                    View Report
                                </button>
                                <button
                                    onClick={downloadReport}
                                    disabled={!result.report_filename}
                                    className="px-4 py-2 bg-purple-600/80 rounded-lg text-sm font-semibold
                                             disabled:opacity-50 disabled:cursor-not-allowed
                                             hover:bg-purple-500 transition-colors"
                                >
                                    Download TXT
                                </button>

                            </div>
                        </div>

                        {/* Weak Signals */}
                        {result.weak_signals && result.weak_signals.length > 0 && (
                            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-yellow-500/20 p-6">
                                <h2 className="text-lg font-semibold text-yellow-400 mb-3">⚠️ Weak Signals</h2>
                                <div className="space-y-3">
                                    {result.weak_signals.map((signal, index) => (
                                        <div key={index} className="flex items-start gap-3 p-3 bg-yellow-500/10 rounded-lg">
                                            <span className="text-yellow-400">•</span>
                                            <div>
                                                <p className="text-gray-200">{signal.signal}</p>
                                                <p className="text-xs text-gray-500 mt-1">
                                                    Source: {signal.source} | Impact: {signal.impact}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Processing Info */}
                        <div className="flex items-center justify-between text-sm text-gray-500 px-2">
                            <p>Agents: {result.agents_executed?.join(', ')}</p>
                            <p>Processing time: {result.processing_time_ms?.toFixed(0)}ms</p>
                        </div>
                    </section>
                )}

                {/* Empty State */}
                {!result && !loading && !error && (
                    <div className="text-center py-20">
                        <div className="text-6xl mb-4">🔮</div>
                        <h3 className="text-xl text-gray-400 mb-2">Ready for Foresight</h3>
                        <p className="text-gray-500">Enter a scenario above to generate an AI-powered forecast</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <footer className="border-t border-purple-500/20 mt-12">
                <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-500">
                    <p>Zarqa al Yamama • Multi-Agent Foresight Intelligence System</p>
                    <p className="text-xs mt-1">Created by Qusai Al-Duaij • Powered by LangGraph</p>
                </div>
            </footer>
        </main>
    );
}
