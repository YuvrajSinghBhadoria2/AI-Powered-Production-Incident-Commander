'use client'

import { useState, useEffect } from 'react'
import { AlertCircle, Activity, Clock, TrendingUp } from 'lucide-react'
import Timeline from './components/Timeline'
import RCAChat from './components/RCAChat'

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

export default function Home() {
    const [incidents, setIncidents] = useState<Incident[]>([])
    const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
    const [rcaResult, setRcaResult] = useState<RCAResult | null>(null)
    const [analyzing, setAnalyzing] = useState(false)
    const [timeWindow, setTimeWindow] = useState('last_30_min')
    const [loading, setLoading] = useState(false)

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
            setRcaResult(null)

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
                    if (data.rca_results) {
                        setRcaResult(data.rca_results)
                    }
                }
            }
        } catch (error) {
            console.error('Analysis failed:', error)
        } finally {
            setAnalyzing(false)
        }
    }

    useEffect(() => {
        fetchIncidents()
    }, [])

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/50'
            case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/50'
            case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
            default: return 'bg-blue-500/20 text-blue-400 border-blue-500/50'
        }
    }

    return (
        <main className="min-h-screen p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <Activity className="w-8 h-8 text-blue-400" />
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                            AI Incident Commander
                        </h1>
                    </div>
                    <p className="text-gray-400">Production-grade incident detection and root cause analysis</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Total Incidents</p>
                                <p className="text-3xl font-bold text-white mt-1">{incidents.length}</p>
                            </div>
                            <AlertCircle className="w-10 h-10 text-blue-400 opacity-50" />
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-red-900/20 to-gray-900/50 backdrop-blur-sm border border-red-500/30 rounded-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Critical</p>
                                <p className="text-3xl font-bold text-red-400 mt-1">
                                    {incidents.filter(i => i.severity === 'critical').length}
                                </p>
                            </div>
                            <TrendingUp className="w-10 h-10 text-red-400 opacity-50" />
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-orange-900/20 to-gray-900/50 backdrop-blur-sm border border-orange-500/30 rounded-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">High Priority</p>
                                <p className="text-3xl font-bold text-orange-400 mt-1">
                                    {incidents.filter(i => i.severity === 'high').length}
                                </p>
                            </div>
                            <Clock className="w-10 h-10 text-orange-400 opacity-50" />
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-green-900/20 to-gray-900/50 backdrop-blur-sm border border-green-500/30 rounded-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Resolved</p>
                                <p className="text-3xl font-bold text-green-400 mt-1">
                                    {incidents.filter(i => i.status === 'resolved').length}
                                </p>
                            </div>
                            <Activity className="w-10 h-10 text-green-400 opacity-50" />
                        </div>
                    </div>
                </div>

                {/* Analysis Controls */}
                <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold mb-4 text-white">Analyze Incidents</h2>
                    <div className="flex gap-4 items-end">
                        <div className="flex-1">
                            <label className="block text-sm text-gray-400 mb-2">Time Window</label>
                            <select
                                value={timeWindow}
                                onChange={(e) => setTimeWindow(e.target.value)}
                                className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="last_15_min">Last 15 minutes</option>
                                <option value="last_30_min">Last 30 minutes</option>
                                <option value="last_1_hour">Last 1 hour</option>
                                <option value="last_6_hours">Last 6 hours</option>
                                <option value="last_24_hours">Last 24 hours</option>
                            </select>
                        </div>
                        <button
                            onClick={analyzeIncident}
                            disabled={analyzing}
                            className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-gray-600 disabled:to-gray-700 text-white px-8 py-2 rounded-lg font-medium transition-all duration-200 disabled:cursor-not-allowed"
                        >
                            {analyzing ? (
                                <span className="flex items-center gap-2">
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Analyzing...
                                </span>
                            ) : (
                                'Run Analysis'
                            )}
                        </button>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Incidents List */}
                    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
                        <h2 className="text-xl font-semibold mb-4 text-white">Recent Incidents</h2>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                            {loading ? (
                                <div className="text-center py-8 text-gray-400">Loading incidents...</div>
                            ) : incidents.length === 0 ? (
                                <div className="text-center py-8 text-gray-400">
                                    No incidents detected. Run analysis to detect incidents.
                                </div>
                            ) : (
                                incidents.map((incident) => (
                                    <div
                                        key={incident.id}
                                        onClick={() => setSelectedIncident(incident)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 hover:scale-[1.02] ${selectedIncident?.id === incident.id
                                                ? 'bg-blue-500/20 border-blue-500/50'
                                                : 'bg-gray-900/50 border-gray-700/50 hover:border-gray-600'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="font-semibold text-white">{incident.title}</h3>
                                            <span className={`text-xs px-2 py-1 rounded border ${getSeverityColor(incident.severity)}`}>
                                                {incident.severity}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400 mb-2">{incident.description}</p>
                                        <div className="flex items-center gap-4 text-xs text-gray-500">
                                            <span>{incident.service}</span>
                                            <span>•</span>
                                            <span>{new Date(incident.timestamp).toLocaleString()}</span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* RCA Results */}
                    <div className="space-y-6">
                        {rcaResult && selectedIncident && (
                            <>
                                <Timeline timeline={rcaResult.timeline} />
                                <RCAChat rcaResult={rcaResult} incident={selectedIncident} />
                            </>
                        )}
                        {!rcaResult && !analyzing && (
                            <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-12 text-center">
                                <Activity className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                                <p className="text-gray-400">Run analysis to see root cause analysis and timeline</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    )
}
