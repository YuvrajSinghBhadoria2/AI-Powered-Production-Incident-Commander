'use client'

import { MessageSquare, CheckCircle, AlertCircle, Lightbulb, TrendingUp } from 'lucide-react'

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
        if (score >= 0.8) return 'text-green-400'
        if (score >= 0.6) return 'text-yellow-400'
        return 'text-orange-400'
    }

    const getConfidenceLabel = (score: number) => {
        if (score >= 0.8) return 'High Confidence'
        if (score >= 0.6) return 'Medium Confidence'
        return 'Low Confidence'
    }

    return (
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
                <MessageSquare className="w-5 h-5 text-purple-400" />
                <h2 className="text-xl font-semibold text-white">Root Cause Analysis</h2>
            </div>

            <div className="space-y-6">
                {/* Incident Summary */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-semibold text-blue-400 mb-1">Incident</h3>
                            <p className="text-white font-medium">{incident.title}</p>
                            <p className="text-sm text-gray-400 mt-1">Service: {incident.service}</p>
                        </div>
                    </div>
                </div>

                {/* Root Cause */}
                <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <Lightbulb className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold text-purple-400">Root Cause</h3>
                                <span className={`text-xs font-medium ${getConfidenceColor(rcaResult.confidence_score)}`}>
                                    {getConfidenceLabel(rcaResult.confidence_score)} ({Math.round(rcaResult.confidence_score * 100)}%)
                                </span>
                            </div>
                            <p className="text-white leading-relaxed">{rcaResult.root_cause}</p>
                            {rcaResult.hypothesis_validation && (
                                <div className="mt-3 pt-3 border-t border-purple-500/20">
                                    <p className="text-sm text-gray-400">
                                        <span className="font-medium text-purple-300">Validation: </span>
                                        {rcaResult.hypothesis_validation}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Mitigation Steps */}
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                            <h3 className="font-semibold text-green-400 mb-3">Mitigation Steps</h3>
                            <div className="space-y-2">
                                {rcaResult.mitigation_steps.map((step, index) => (
                                    <div key={index} className="flex items-start gap-3">
                                        <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <span className="text-xs font-bold text-green-400">{index + 1}</span>
                                        </div>
                                        <p className="text-white text-sm leading-relaxed">{step}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Similar Incidents */}
                {rcaResult.similar_incidents && rcaResult.similar_incidents.length > 0 && (
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                            <TrendingUp className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <h3 className="font-semibold text-orange-400 mb-3">Similar Past Incidents</h3>
                                <div className="space-y-2">
                                    {rcaResult.similar_incidents.map((incidentId, index) => (
                                        <div key={index} className="text-sm text-gray-300 bg-gray-900/50 rounded px-3 py-2">
                                            {incidentId}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
