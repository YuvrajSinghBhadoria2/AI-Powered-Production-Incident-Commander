'use client'

import { useState, useEffect } from 'react'
import { AlertCircle, Activity, Clock, TrendingUp, Cpu, Server, Shield, Zap, RefreshCw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import Timeline from '@/app/components/Timeline'
import RCAChat from '@/app/components/RCAChat'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Incident {
    id: string
    timestamp: string
    service: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    title: string
    description: string
    status: string
}

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
}

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
}

const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
        y: 0,
        opacity: 1,
        transition: {
            stiffness: 100
        }
    }
}

export default function Home() {
    const [incidents, setIncidents] = useState<Incident[]>([])
    const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
    const [rcaResultsMap, setRcaResultsMap] = useState<Record<string, RCAResult>>({})
    const [analyzing, setAnalyzing] = useState(false)
    const [timeWindow, setTimeWindow] = useState('last_30_min')
    const [loading, setLoading] = useState(false)

    const rcaResult = selectedIncident ? rcaResultsMap[selectedIncident.id] : null

    const handleIncidentSelect = async (incident: Incident) => {
        // Check if RCA results already exist for this incident
        if (!rcaResultsMap[incident.id]) {
            // If not, run analysis specifically for this incident
            try {
                const response = await fetch(`${API_BASE_URL}/analyze/incident`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        incident_id: incident.id,
                        time_window: 'last_1_hour',
                        services: [incident.service],
                        severity_threshold: 'medium'
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    if (data.rca_results && Array.isArray(data.rca_results)) {
                        const newMap: Record<string, RCAResult> = { ...rcaResultsMap };
                        data.rca_results.forEach((r: any) => {
                            if (r.incident_id) {
                                newMap[r.incident_id] = r;
                            }
                        });
                        setRcaResultsMap(newMap);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch RCA for incident:', error);
            }
        }
        
        // Set the selected incident
        setSelectedIncident(incident);
    };

    const fetchIncidents = async () => {
        try {
            setLoading(true)
            const response = await fetch(`${API_BASE_URL}/analyze/incidents`)
            if (response.ok) {
                const data = await response.json()
                setIncidents(data.incidents || [])
            }
        } catch (error) {
            console.error('Failed to fetch incidents:', error)
        } finally {
            setLoading(false)
        }
    }

    const analyzeIncident = async () => {
        try {
            setAnalyzing(true)
            setRcaResultsMap({})

            const response = await fetch(`${API_BASE_URL}/analyze/incident`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    time_window: timeWindow,
                    services: null,
                    severity_threshold: 'medium'
                })
            })

            if (response.ok) {
                const data = await response.json()
                if (data.incidents_detected && data.incidents_detected.length > 0) {
                    setIncidents(data.incidents_detected)
                    setSelectedIncident(data.incidents_detected[0])

                    if (data.rca_results && Array.isArray(data.rca_results)) {
                        const newMap: Record<string, RCAResult> = {}
                        data.rca_results.forEach((r: any) => {
                            if (r.incident_id) {
                                newMap[r.incident_id] = r
                            }
                        })
                        setRcaResultsMap(newMap)
                    }
                }
            }
        } catch (error) {
            console.error('Analysis failed:', error)
        } finally {
            setAnalyzing(false)
        }
    }

    const flushData = async () => {
        if (!confirm('Are you sure you want to clear all logs, metrics, and incidents?')) return

        try {
            setLoading(true)
            const response = await fetch(`${API_BASE_URL}/ingest/flush`, { method: 'POST' })
            if (response.ok) {
                setIncidents([])
                setSelectedIncident(null)
                setRcaResultsMap({})
            }
        } catch (error) {
            console.error('Failed to flush data:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchIncidents()
    }, [])

    const getSeverityStyles = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-rose-500/20 text-rose-400 border-rose-500/50 shadow-[0_0_10px_rgba(244,63,94,0.2)]'
            case 'high': return 'bg-amber-500/20 text-amber-400 border-amber-500/50'
            case 'medium': return 'bg-sky-500/20 text-sky-400 border-sky-500/50'
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/50'
        }
    }

    return (
        <main className="min-h-screen p-4 md:p-8 selection:bg-purple-500/30">
            <div className="max-w-[1600px] mx-auto">
                {/* Header Section */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12"
                >
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-500/10 rounded-xl border border-purple-500/20 neon-glow-purple">
                                <Zap className="w-8 h-8 text-purple-400" />
                            </div>
                            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-purple-200 to-purple-400 bg-clip-text text-transparent">
                                Incident Commander
                            </h1>
                        </div>
                        <p className="text-slate-400 font-medium ml-1">Automated Root Cause Analysis & Prediction</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={flushData}
                            disabled={loading || analyzing}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 hover:border-rose-500/20 transition-all duration-300 disabled:opacity-50"
                            title="Clear all data"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            <span className="text-sm font-bold uppercase tracking-wider">Flush System</span>
                        </button>

                        <div className="flex items-center gap-3 bg-white/5 p-1.5 rounded-2xl border border-white/10 backdrop-blur-md">
                            <select
                                value={timeWindow}
                                onChange={(e) => setTimeWindow(e.target.value)}
                                className="bg-transparent border-none text-slate-300 text-sm focus:ring-0 cursor-pointer px-4 py-2 pr-10"
                            >
                                <option value="last_15_min">Last 15m</option>
                                <option value="last_30_min">Last 30m</option>
                                <option value="last_1_hour">Last 1h</option>
                                <option value="last_6_hours">Last 6h</option>
                            </select>
                            <button
                                onClick={analyzeIncident}
                                disabled={analyzing}
                                className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2 shadow-lg shadow-purple-500/20 active:scale-95"
                            >
                                {analyzing ? (
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Activity className="w-4 h-4" />
                                )}
                                {analyzing ? 'Processing...' : 'Run Engine'}
                            </button>
                        </div>
                    </div>
                </motion.div>

                {/* Stats Grid */}
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
                >
                    {[
                        { label: 'Total Alerts', value: incidents.length, icon: Server, color: 'text-indigo-400', bg: 'indigo' },
                        { label: 'Critical Errors', value: incidents.filter(i => i.severity === 'critical').length, icon: Shield, color: 'text-rose-400', bg: 'rose' },
                        { label: 'Active Incidents', value: incidents.filter(i => i.status !== 'resolved').length, icon: AlertCircle, color: 'text-amber-400', bg: 'amber' },
                        { label: 'System Health', value: '98.2%', icon: Cpu, color: 'text-emerald-400', bg: 'emerald' },
                    ].map((stat, idx) => (
                        <motion.div
                            key={idx}
                            variants={itemVariants}
                            className="glass-card p-6 rounded-3xl relative overflow-hidden group"
                        >
                            <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform`}>
                                <stat.icon className={`w-20 h-20 ${stat.color}`} />
                            </div>
                            <div className="relative z-10">
                                <p className="text-slate-400 text-sm font-semibold mb-1 uppercase tracking-wider">{stat.label}</p>
                                <p className={`text-4xl font-black text-white`}>{stat.value}</p>
                            </div>
                        </motion.div>
                    ))}
                </motion.div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
                    {/* Incidents Feed */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 }}
                        className="xl:col-span-5 hidden lg:block"
                    >
                        <div className="glass-card rounded-[2rem] overflow-hidden border-white/5">
                            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-purple-400" />
                                    Active Feed
                                </h2>
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-widest bg-white/5 px-3 py-1 rounded-full">
                                    Live Updates
                                </span>
                            </div>
                            <div className="p-4 space-y-4 max-h-[700px] overflow-y-auto scrollbar-hide">
                                <AnimatePresence mode='popLayout'>
                                    {loading ? (
                                        <div className="flex flex-col items-center justify-center py-20 gap-4">
                                            <div className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
                                            <p className="text-slate-400 font-medium">Fetching telemetry...</p>
                                        </div>
                                    ) : incidents.length === 0 ? (
                                        <div className="text-center py-20">
                                            <Server className="w-16 h-16 text-slate-700 mx-auto mb-4 opacity-50" />
                                            <p className="text-slate-500 font-medium">System nominal. No incidents detected.</p>
                                        </div>
                                    ) : (
                                        incidents.map((incident) => (
                                            <motion.div
                                                layout
                                                initial={{ opacity: 0, scale: 0.95 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.95 }}
                                                key={incident.id}
                                                onClick={() => handleIncidentSelect(incident)}
                                                className={`p-5 rounded-2xl border transition-all duration-300 cursor-pointer relative group ${selectedIncident?.id === incident.id
                                                    ? 'bg-purple-500/10 border-purple-500/50 ring-1 ring-purple-500/20'
                                                    : 'bg-white/[0.03] border-white/5 hover:border-white/20'
                                                    }`}
                                            >
                                                <div className="flex items-start justify-between mb-3">
                                                    <div>
                                                        <h3 className="font-bold text-white group-hover:text-purple-300 transition-colors uppercase tracking-tight text-sm">
                                                            {incident.title}
                                                        </h3>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-slate-600 animate-pulse" />
                                                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{incident.service}</span>
                                                        </div>
                                                    </div>
                                                    <span className={`text-[10px] font-black px-2.5 py-1 rounded-lg border uppercase tracking-tighter ${getSeverityStyles(incident.severity)}`}>
                                                        {incident.severity}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{incident.description}</p>
                                            </motion.div>
                                        ))
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>

                    {/* RCA Viewport */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 }}
                        className="xl:col-span-7 space-y-8"
                    >
                        <AnimatePresence mode='wait'>
                            {rcaResult && selectedIncident ? (
                                <motion.div
                                    key={selectedIncident.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    className="space-y-8"
                                >
                                    <Timeline timeline={rcaResult.timeline} />
                                    <RCAChat rcaResult={rcaResult} incident={selectedIncident} />
                                </motion.div>
                            ) : (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="glass-card rounded-[2rem] p-20 text-center flex flex-col items-center justify-center border-dashed border-2 border-white/10"
                                >
                                    <div className="w-24 h-24 bg-purple-500/10 rounded-full flex items-center justify-center mb-6 animate-pulse-slow">
                                        <TrendingUp className="w-10 h-10 text-purple-400 opacity-50" />
                                    </div>
                                    <h3 className="text-2xl font-bold text-white mb-2">Analysis Engine Ready</h3>
                                    <p className="text-slate-400 max-w-sm">Select an incident from the feed or run a new system-wide analysis to generate a root cause timeline.</p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </div>
            </div>
        </main>
    )
}
