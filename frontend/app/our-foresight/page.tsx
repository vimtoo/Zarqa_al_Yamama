'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import { Suspense } from 'react';

function OurForesightContent() {
    const searchParams = useSearchParams();
    const file = searchParams.get('file');
    const pdf = searchParams.get('pdf');
    const [content, setContent] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const reportUrl = useMemo(() => {
        if (!file) {
            return null;
        }
        return `http://localhost:8000/api/v1/reports/${encodeURIComponent(file)}`;
    }, [file]);

    const pdfUrl = useMemo(() => {
        if (!pdf) {
            return null;
        }
        return `http://localhost:8000/api/v1/reports/${encodeURIComponent(pdf)}`;
    }, [pdf]);

    useEffect(() => {
        if (!reportUrl) {
            return;
        }
        setLoading(true);
        setError(null);
        fetch(reportUrl)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.text();
            })
            .then((text) => setContent(text))
            .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load report'))
            .finally(() => setLoading(false));
    }, [reportUrl]);

    const downloadTxt = () => {
        if (reportUrl) {
            window.open(reportUrl, '_blank', 'noopener,noreferrer');
        }
    };

    const downloadPdf = () => {
        if (pdfUrl) {
            window.open(pdfUrl, '_blank', 'noopener,noreferrer');
        }
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
            <header className="border-b border-purple-500/30 backdrop-blur-sm bg-black/20">
                <div className="max-w-5xl mx-auto px-6 py-4">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                        Our Foresight • رؤيتنا المستقبلية
                    </h1>
                    <p className="text-xs text-purple-300/70 mt-1">
                        View, review, and save your final report • عرض التقرير النهائي وحفظه
                    </p>
                </div>
            </header>

            <section className="max-w-5xl mx-auto px-6 py-8 space-y-6">
                <div className="flex flex-wrap items-center gap-3">
                    <button
                        onClick={downloadTxt}
                        disabled={!reportUrl}
                        className="px-4 py-2 bg-purple-600/80 rounded-lg text-sm font-semibold
                                 disabled:opacity-50 disabled:cursor-not-allowed
                                 hover:bg-purple-500 transition-colors"
                    >
                        Download TXT • تحميل TXT
                    </button>
                    <button
                        onClick={downloadPdf}
                        disabled={!pdfUrl}
                        className="px-4 py-2 bg-purple-700/80 rounded-lg text-sm font-semibold
                                 disabled:opacity-50 disabled:cursor-not-allowed
                                 hover:bg-purple-600 transition-colors"
                    >
                        Download PDF • تحميل PDF
                    </button>
                </div>

                {loading && (
                    <div className="p-4 bg-white/10 rounded-xl border border-purple-500/20">
                        Loading report…
                    </div>
                )}

                {error && (
                    <div className="p-4 bg-red-500/20 rounded-xl border border-red-500/40">
                        Error: {error}
                    </div>
                )}

                {!loading && !error && (
                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-purple-500/20 p-6">
                        <pre className="whitespace-pre-wrap text-sm text-gray-200 leading-relaxed">
                            {content || 'No report content available.'}
                        </pre>
                    </div>
                )}
            </section>
        </main>
    );
}

export default function OurForesightPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-slate-900 text-white p-10">Loading Foresight Engine...</div>}>
            <OurForesightContent />
        </Suspense>
    );
}
