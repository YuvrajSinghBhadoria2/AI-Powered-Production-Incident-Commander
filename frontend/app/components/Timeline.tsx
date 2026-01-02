'use client'

import { Clock, AlertTriangle } from 'lucide-react'

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
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700/50 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-6">
                <Clock className="w-5 h-5 text-blue-400" />
                <h2 className="text-xl font-semibold text-white">Incident Timeline</h2>
            </div>

            <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-transparent" />

                {/* Timeline events */}
                <div className="space-y-6">
                    {timeline.map((event, index) => (
                        <div key={index} className="relative pl-12">
                            {/* Timeline dot */}
                            <div className="absolute left-0 top-1 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/50">
                                <div className="w-3 h-3 rounded-full bg-white" />
                            </div>

                            {/* Event card */}
                            <div className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-4 hover:border-blue-500/50 transition-all duration-200">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-semibold text-white">{event.event}</h3>
                                            <span className="text-xs text-gray-400">
                                                {new Date(event.timestamp).toLocaleTimeString()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400">{event.impact}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {timeline.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                    No timeline events available
                </div>
            )}
        </div>
    )
}
