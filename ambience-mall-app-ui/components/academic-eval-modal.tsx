'use client'

import React from 'react'
import { X, Cpu, GitCompare, CheckCircle2, AlertCircle, Layers, ArrowRight, Zap, Award } from 'lucide-react'
import type { Route, RouteEvaluation } from '@/lib/api'

interface AcademicEvalModalProps {
  isOpen: boolean
  onClose: () => void
  route?: Route
}

export default function AcademicEvalModal({ isOpen, onClose, route }: AcademicEvalModalProps) {
  if (!isOpen) return null

  const evalData = route?.evaluation

  return (
    <div className="ai-modal-backdrop" onClick={onClose}>
      <div className="ai-modal-sheet academic-eval-sheet" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-modal-header">
          <div className="ai-modal-title">
            <div className="ai-icon-bubble" style={{ background: '#7c3aed' }}>
              <Cpu size={18} color="#ffffff" />
            </div>
            <div>
              <h3>Academic / Viva RL Evaluation</h3>
              <small>Reinforcement Learning Policy vs Dijkstra Ground Truth</small>
            </div>
          </div>
          <button className="ai-close-btn" onClick={onClose} aria-label="Close evaluation modal">
            <X size={20} />
          </button>
        </div>

        <div className="analytics-modal-body">
          {/* Model Specification Card */}
          <div className="analytics-section">
            <div className="analytics-section-header">
              <h4>Reinforcement Learning Architecture</h4>
              <span className="analytics-badge verified">Converged Q-Table</span>
            </div>
            <div className="eval-specs-grid">
              <div className="eval-spec-item">
                <small>Algorithm</small>
                <b>Tabular Q-Learning</b>
                <span>Bellman Equation convergence with reward shaping</span>
              </div>
              <div className="eval-spec-item">
                <small>State Space Formulation</small>
                <b>342,732 States</b>
                <span>338 nodes × 338 destinations × 3 navigation profiles</span>
              </div>
              <div className="eval-spec-item">
                <small>Action Space</small>
                <b>6 Actions</b>
                <span>NORTH, SOUTH, WEST, EAST, VERTICAL, CONNECTED</span>
              </div>
              <div className="eval-spec-item">
                <small>Q-Table Array Shape</small>
                <b>(342732, 6) float64</b>
                <span>2,056,392 learned values · 16.4 MB model</span>
              </div>
            </div>
          </div>

          {/* Active Navigation State & Q-Values */}
          {route ? (
            <div className="analytics-section">
              <div className="analytics-section-header">
                <h4>Active Navigation State Telemetry</h4>
                <span className="analytics-badge" style={{ background: '#ede9fe', color: '#6d28d9' }}>
                  {route.profile || 'Standard'} Mode
                </span>
              </div>

              <div className="active-state-banner">
                <div>
                  <small>Origin Node (s₀)</small>
                  <b>{route.start.name}</b>
                  <code>ID: {route.start.id} · Floor {route.start.floorId}</code>
                </div>
                <ArrowRight size={20} className="state-arrow" />
                <div>
                  <small>Destination Goal (s*)</small>
                  <b>{route.destination.name}</b>
                  <code>ID: {route.destination.id} · Floor {route.destination.floorId}</code>
                </div>
              </div>

              {/* Start State Q-Values Breakdown */}
              {evalData?.rl.qValuesAtStart && Object.keys(evalData.rl.qValuesAtStart).length > 0 && (
                <div className="q-values-block">
                  <div className="q-values-title">
                    <span>Q(s₀, a) Learned Policy Values at Start Node:</span>
                    <small>Highest value selected by policy</small>
                  </div>
                  <div className="q-values-bars">
                    {Object.entries(evalData.rl.qValuesAtStart).map(([action, qVal]) => {
                      const numVal = Number(qVal)
                      const isMax = numVal === Math.max(...Object.values(evalData.rl.qValuesAtStart).map(Number))
                      return (
                        <div key={action} className={`q-bar-row ${isMax ? 'q-max-action' : ''}`}>
                          <span className="q-action-name">
                            {action}
                            {isMax && <span className="q-max-badge">Selected (π*)</span>}
                          </span>
                          <div className="q-bar-track">
                            <div
                              className="q-bar-fill"
                              style={{
                                width: `${Math.min(100, Math.max(10, ((numVal + 50) / 150) * 100))}%`,
                                background: isMax ? '#10b981' : '#64748b'
                              }}
                            />
                          </div>
                          <span className="q-val-number">{numVal.toFixed(2)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Head-to-Head Comparison Scorecard */}
              {evalData && (
                <div className="analytics-section" style={{ marginTop: '16px' }}>
                  <div className="analytics-section-header">
                    <h4>RL Policy vs Dijkstra Baseline Comparison</h4>
                    <span className="analytics-badge" style={{ background: '#f0fdf4', color: '#166534' }}>
                      Academic Ground Truth
                    </span>
                  </div>

                  <table className="eval-comparison-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Reinforcement Learning (Q-Table)</th>
                        <th>Dijkstra Shortest Path (Baseline)</th>
                        <th>Evaluation</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><b>Destination Reached</b></td>
                        <td>
                          {evalData.rl.success ? (
                            <span className="status-pill success"><CheckCircle2 size={13} /> Reached</span>
                          ) : (
                            <span className="status-pill warn"><AlertCircle size={13} /> Fallback</span>
                          )}
                        </td>
                        <td>
                          {evalData.baseline.success ? (
                            <span className="status-pill success"><CheckCircle2 size={13} /> Reached</span>
                          ) : (
                            <span className="status-pill warn"><AlertCircle size={13} /> Unreachable</span>
                          )}
                        </td>
                        <td>{evalData.rl.success ? 'Validated in real graph' : 'Controlled baseline active'}</td>
                      </tr>
                      <tr>
                        <td><b>Trajectory Steps</b></td>
                        <td><b>{evalData.rl.steps} steps</b></td>
                        <td><b>{evalData.baseline.steps} steps</b></td>
                        <td>
                          {evalData.rl.steps === evalData.baseline.steps ? (
                            <span className="diff-pill optimal">Identical (Optimal)</span>
                          ) : evalData.rl.steps < evalData.baseline.steps ? (
                            <span className="diff-pill better">RL shorter by {evalData.baseline.steps - evalData.rl.steps} steps</span>
                          ) : (
                            <span className="diff-pill neutral">+{evalData.rl.steps - evalData.baseline.steps} steps</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td><b>Relative Path Cost</b></td>
                        <td><b>{evalData.rl.pathCost.toFixed(1)}</b></td>
                        <td><b>{evalData.baseline.pathCost.toFixed(1)}</b></td>
                        <td>
                          {evalData.rl.pathCost <= evalData.baseline.pathCost ? (
                            <span className="diff-pill optimal">Optimal cost</span>
                          ) : (
                            <span className="diff-pill neutral">+{(evalData.rl.pathCost - evalData.baseline.pathCost).toFixed(1)} cost</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td><b>Computation Time</b></td>
                        <td>{evalData.rl.timeMs} ms</td>
                        <td>{evalData.baseline.timeMs} ms</td>
                        <td>Sub-millisecond policy rollout</td>
                      </tr>
                      <tr>
                        <td><b>Floor Transitions</b></td>
                        <td>{evalData.rl.floorChanges}</td>
                        <td>{evalData.baseline.floorChanges}</td>
                        <td>
                          {evalData.rl.connectors.length > 0 ? evalData.rl.connectors.join(', ') : 'Direct same floor'}
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  {/* Viva Summary Note */}
                  <div className="eval-summary-card">
                    <Award size={18} color="#7c3aed" />
                    <div>
                      <b>Academic Viva Summary:</b>
                      <p>
                        {route.comparisonSummary || (evalData.identicalPath
                          ? 'The learned RL policy converged to the mathematically proven shortest path produced by Dijkstra across topological corridor vertices.'
                          : `The RL policy produced ${evalData.rl.steps} steps (cost ${evalData.rl.pathCost.toFixed(1)}) vs Dijkstra baseline ${evalData.baseline.steps} steps (cost ${evalData.baseline.pathCost.toFixed(1)}).`)}
                      </p>
                      {route.isFallback && (
                        <p style={{ marginTop: '6px', color: '#b45309', fontSize: '11px', fontWeight: 600 }}>
                          ⚠️ Fallback Notice: {evalData.rl.validationReason || 'RL route failed safety validation; verified Dijkstra baseline path active.'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-copy">
              <p className="muted">Select any destination and start a route to inspect live RL policy actions.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
