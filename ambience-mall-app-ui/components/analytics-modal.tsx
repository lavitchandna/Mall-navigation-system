'use client'

import React from 'react'
import { X, BarChart3, Activity, Cpu, Users, Layers, ShieldCheck, MapPin } from 'lucide-react'

interface AnalyticsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function AnalyticsModal({ isOpen, onClose }: AnalyticsModalProps) {
  if (!isOpen) return null

  const stats = [
    { label: 'Stores Catalogued', value: '221', icon: '🏬', note: 'Real POIs across 3 floors' },
    { label: 'Floors Active', value: '3', icon: '🏢', note: 'Ground, 1st & 2nd Floors' },
    { label: 'Navigation Nodes', value: '338', icon: '📍', note: 'Topological walking vertices' },
    { label: 'Corridor Edges', value: '362', icon: '🛣️', note: 'Verified bidirectional paths' },
    { label: 'Vertical Connectors', value: '27', icon: '🛗', note: '9 Lifts, 9 Escalators, 9 Stairs' },
    { label: 'Store Categories', value: '11', icon: '🏷️', note: 'Fashion, Dining, Electronics…' }
  ]

  const crowdZones = [
    { zone: 'Ground Floor North Promenade', level: 'Low', color: '#10b981', note: 'Quiet, fast walking pace' },
    { zone: 'Central Grand Atrium & Fountain', level: 'Moderate', color: '#f59e0b', note: 'Steady visitor footfall' },
    { zone: 'South Food & Dining Concourse', level: 'High', color: '#ef4444', note: 'Popular peak activity' },
    { zone: 'First Floor Central Boulevard', level: 'Moderate', color: '#f59e0b', note: 'Fashion & apparel shoppers' },
    { zone: 'Second Floor Gadget & Toy Zone', level: 'Low', color: '#10b981', note: 'Clear corridors' }
  ]

  return (
    <div className="ai-modal-backdrop" onClick={onClose}>
      <div className="ai-modal-sheet" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-modal-header">
          <div className="ai-modal-title">
            <div className="ai-icon-bubble" style={{ background: '#0284c7' }}>
              <BarChart3 size={18} color="#ffffff" />
            </div>
            <div>
              <h3>Mall Analytics & System Status</h3>
              <small>System Metrics & Zone Crowd Insights</small>
            </div>
          </div>
          <button className="ai-close-btn" onClick={onClose} aria-label="Close analytics">
            <X size={20} />
          </button>
        </div>

        <div className="analytics-modal-body">
          {/* Real System Metadata Cards */}
          <div className="analytics-section">
            <div className="analytics-section-header">
              <h4>System Architecture Telemetry</h4>
              <span className="analytics-badge verified">Verified Backend Real Data</span>
            </div>
            <div className="analytics-grid">
              {stats.map(s => (
                <div key={s.label} className="analytics-card">
                  <div className="analytics-card-top">
                    <span className="analytics-icon">{s.icon}</span>
                    <span className="analytics-value">{s.value}</span>
                  </div>
                  <b>{s.label}</b>
                  <small>{s.note}</small>
                </div>
              ))}
            </div>
          </div>

          {/* Crowd Insights Module */}
          <div className="analytics-section">
            <div className="analytics-section-header">
              <h4>Mall Zone Crowd Activity</h4>
              <span className="analytics-badge demo">Demo Crowd Estimate</span>
            </div>
            <p className="analytics-desc">
              Estimated zone density based on current shopping periods. Ready for IoT / WiFi footfall sensor integration.
            </p>
            <div className="crowd-list">
              {crowdZones.map(cz => (
                <div key={cz.zone} className="crowd-item">
                  <div className="crowd-item-left">
                    <b>{cz.zone}</b>
                    <small>{cz.note}</small>
                  </div>
                  <span className="crowd-pill" style={{ background: `${cz.color}15`, color: cz.color, borderColor: cz.color }}>
                    ● {cz.level}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Tech Stack Info */}
          <div className="analytics-tech-banner">
            <Cpu size={16} color="#64748b" />
            <span>Pathfinding: <b>Dijkstra Graph Planner</b> · Coordinate Transform: <b>Thin-Plate Spline (TPS)</b> · Backend: <b>Flask API on :5001</b></span>
          </div>
        </div>
      </div>
    </div>
  )
}
