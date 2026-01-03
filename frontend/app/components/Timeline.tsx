'use client'

import { motion } from 'framer-motion'
import { Clock, AlertTriangle, CheckCircle2 } from 'lucide-react'

interface TimelineEvent {
    timestamp: string
    event: string
    impact: string
}

interface TimelineProps {
    timeline: TimelineEvent[]
}

export default function Timeline({ timeline }: TimelineProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card rounded-[2rem] p-8 border-white/5 relative overflow-hidden"
        >
            <div className="absolute top-0 right-0 p-8 opacity-5">
                <Clock className="w-32 h-32 text-blue-400" />
            </div>

            <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                    <Clock className="w-5 h-5 text-blue-400" />
                </div>
                Incident Timeline
            </h2>

            <div className="relative ml-4">
                {/* Vertical Line */}
                <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-transparent opacity-30" />

                <div className="space-y-10">
                    {timeline.length > 0 ? (
                        timeline.map((item, idx) => (
                            <motion.div
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                key={idx}
                                className="relative pl-10"
                            >
                                {/* Node */}
                                <div className={`absolute left-[-5px] top-1.5 w-3 h-3 rounded-full border-2 border-background z-10 ${idx === 0 ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'bg-purple-500'
                                    }`} />

                                <div className="space-y-2">
                                    <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest bg-white/5 px-2 py-0.5 rounded">
                                            {new Date(item.timestamp).toLocaleTimeString()}
                                        </span>
                                        <h3 className="text-lg font-bold text-white leading-tight">
                                            {item.event}
                                        </h3>
                                    </div>
                                    <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex items-start gap-3 group hover:bg-white/[0.04] transition-colors">
                                        <AlertTriangle className="w-4 h-4 text-amber-500/50 mt-0.5 shrink-0" />
                                        <p className="text-sm text-slate-400 leading-relaxed group-hover:text-slate-300">
                                            <span className="text-slate-500 font-bold uppercase text-[10px] inline-block mr-2">Impact:</span>
                                            {item.impact}
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        ))
                    ) : (
                        <div className="py-20 text-center opacity-50">
                            <Clock className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                            <p className="text-slate-500 font-medium">No timeline events detected yet.</p>
                        </div>
                    )}

                    {timeline.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: timeline.length * 0.1 }}
                            className="relative pl-10"
                        >
                            <div className="absolute left-[-5px] top-1.5 w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                            <div className="flex items-center gap-3">
                                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                <span className="text-sm font-bold text-emerald-400/80 uppercase tracking-widest">Analysis Converged</span>
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
