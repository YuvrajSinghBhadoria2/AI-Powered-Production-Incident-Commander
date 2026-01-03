'use client'

import { motion } from 'framer-motion'
import { ShieldCheck, Target, ListChecks, MessageSquare, AlertCircle, Lightbulb, Zap, ArrowRight, BrainCircuit, TrendingUp } from 'lucide-react'

interface RCAResult {
    root_cause: string
    confidence_score: number
    timeline: Array<{
        timestamp: string
        event: string
        impact: string
    }>
    mitigation_steps: string[]
    similar_incidents: string[]
    hypothesis_validation?: string
}

interface Incident {
    id: string
    title: string
    service: string
    severity: string
}

interface RCAChatProps {
    rcaResult: RCAResult
    incident: Incident
}

export default function RCAChat({ rcaResult, incident }: RCAChatProps) {
    const getConfidenceColor = (score: number) => {
        if (score >= 0.8) return 'text-emerald-400'
        if (score >= 0.6) return 'text-amber-400'
        return 'text-rose-400'
    }

    const getConfidenceLabel = (score: number) => {
        if (score >= 0.8) return 'Verified Root Cause'
        if (score >= 0.6) return 'Probable Hypothesis'
        return 'Experimental Analysis'
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            {/* Header / Summary Card */}
            <div className="glass-card rounded-[2rem] p-8 border-purple-500/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                    <BrainCircuit className="w-32 h-32 text-purple-400" />
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-purple-500/20 rounded-xl border border-purple-500/20">
                            <Target className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-white tracking-tight uppercase">Root Cause Analysis</h2>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-0.5">Automated Diagnostic Protocol</p>
                        </div>
                    </div>

                    <div className="flex flex-col items-end">
                        <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-4 py-1.5 rounded-full backdrop-blur-sm">
                            <Zap className={`w-4 h-4 ${getConfidenceColor(rcaResult.confidence_score)}`} />
                            <span className={`text-xs font-black uppercase tracking-widest ${getConfidenceColor(rcaResult.confidence_score)}`}>
                                {Math.round(rcaResult.confidence_score * 100)}% Confidence
                            </span>
                        </div>
                        <span className="text-[10px] font-bold text-slate-600 uppercase mt-1.5 tracking-tighter">
                            {getConfidenceLabel(rcaResult.confidence_score)}
                        </span>
                    </div>
                </div>

                <div className="space-y-6">
                    {/* Primary Root Cause */}
                    <div className="bg-purple-600/10 border border-purple-500/30 rounded-3xl p-8 relative group hover:bg-purple-600/[0.15] transition-all duration-500">
                        <div className="absolute left-0 top-10 bottom-10 w-1.5 bg-gradient-to-b from-purple-400 to-purple-600 rounded-r-full shadow-[0_0_15px_rgba(168,85,247,0.4)]" />
                        <div className="flex items-center gap-2 mb-3 text-purple-400/80 uppercase text-[10px] font-black tracking-[0.2em]">
                            <Lightbulb className="w-3 h-3" />
                            Core Diagnosis
                        </div>
                        <p className="text-xl md:text-2xl text-white leading-tight font-bold tracking-tight">
                            {rcaResult.root_cause}
                        </p>
                    </div>

                    {/* Hypothesis Validation */}
                    {rcaResult.hypothesis_validation && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="flex items-start gap-4 p-5 rounded-2xl bg-white/[0.02] border border-white/5"
                        >
                            <ShieldCheck className="w-5 h-5 text-emerald-500/50 mt-1" />
                            <div className="space-y-1">
                                <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest">Evidence Validation</h4>
                                <p className="text-sm text-slate-300 leading-relaxed italic">"{rcaResult.hypothesis_validation}"</p>
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>

            {/* Action Items and History */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="glass-card rounded-[2rem] p-8 border-white/5">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <div className="p-2 bg-amber-500/20 rounded-lg">
                            <ListChecks className="w-5 h-5 text-amber-400" />
                        </div>
                        Remediation Path
                    </h3>
                    <div className="space-y-4">
                        {rcaResult.mitigation_steps.map((step, idx) => (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.4 + (idx * 0.1) }}
                                key={idx}
                                className="flex items-start gap-4 group"
                            >
                                <div className="mt-1.5 w-5 h-5 rounded-full bg-white/5 border border-white/10 flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:bg-amber-500/20 group-hover:border-amber-500/30 transition-all duration-300">
                                    <span className="text-[10px] font-black text-slate-500 group-hover:text-amber-400 transition-colors">{idx + 1}</span>
                                </div>
                                <p className="text-sm text-slate-400 leading-relaxed group-hover:text-slate-200 transition-colors pt-0.5">
                                    {step}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>

                <div className="glass-card rounded-[2rem] p-8 border-white/5">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                            <TrendingUp className="w-5 h-5 text-blue-400" />
                        </div>
                        Case Correlation
                    </h3>
                    <div className="space-y-4">
                        {rcaResult.similar_incidents && rcaResult.similar_incidents.length > 0 ? (
                            rcaResult.similar_incidents.map((incident_id, idx) => (
                                <motion.div
                                    whileHover={{ x: 5 }}
                                    key={idx}
                                    className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center justify-between group cursor-pointer hover:bg-white/[0.04] transition-all"
                                >
                                    <div className="flex items-center gap-3">
                                        <MessageSquare className="w-4 h-4 text-blue-400/50" />
                                        <div className="flex flex-col">
                                            <span className="text-xs font-bold text-slate-300 group-hover:text-blue-400">Past Occurrence Detected</span>
                                            <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest leading-none mt-1">Ref ID: {incident_id}</span>
                                        </div>
                                    </div>
                                    <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                                </motion.div>
                            ))
                        ) : (
                            <div className="py-12 text-center bg-white/[0.01] border border-dashed border-white/5 rounded-[2rem] flex flex-col items-center justify-center">
                                <ShieldCheck className="w-10 h-10 text-slate-800 mb-3 opacity-20" />
                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em]">Novel Signature Found</p>
                                <p className="text-[9px] text-slate-700 mt-2 max-w-[150px] leading-tight">No historical matches found in the knowledge base.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    )
}
