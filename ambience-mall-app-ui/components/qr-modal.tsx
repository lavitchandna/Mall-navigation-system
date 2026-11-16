'use client'

import React, { useState } from 'react'
import { X, QrCode, Navigation, CheckCircle, Sparkles } from 'lucide-react'

interface QRModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectStartLocation: (startNodeId: string, startName: string) => void
}

const QR_PILLARS = [
  {
    id: 'G_GATE_1',
    code: 'AMB-GF-PIL-01',
    name: 'Gate 1 (North Main Entry)',
    floor: 'Ground Floor',
    zone: 'North Promenade',
    color: '#ed1b2f'
  },
  {
    id: 'G_CORR_ATRIUM',
    code: 'AMB-GF-PIL-14',
    name: 'Central Grand Atrium Fountain',
    floor: 'Ground Floor',
    zone: 'Central Atrium',
    color: '#2563eb'
  },
  {
    id: 'LIFT_NORTH_F1',
    code: 'AMB-1F-PIL-08',
    name: 'First Floor North Glass Elevator',
    floor: 'First Floor',
    zone: 'First Floor North',
    color: '#8b5cf6'
  },
  {
    id: 'F2_CORR_CENTRAL_ATRIUM',
    code: 'AMB-2F-PIL-05',
    name: 'Second Floor Central Promenade',
    floor: 'Second Floor',
    zone: 'Second Floor Central',
    color: '#059669'
  }
]

export default function QRModal({
  isOpen,
  onClose,
  onSelectStartLocation,
}: QRModalProps) {
  const [selectedQR, setSelectedQR] = useState(QR_PILLARS[0])
  const [scanned, setScanned] = useState(false)

  if (!isOpen) return null

  const handleSimulateScan = (pillar: typeof QR_PILLARS[0]) => {
    setSelectedQR(pillar)
    setScanned(true)
    setTimeout(() => {
      onSelectStartLocation(pillar.id, pillar.name)
      onClose()
      setScanned(false)
    }, 600)
  }

  return (
    <div className="ai-modal-backdrop" onClick={onClose}>
      <div className="ai-modal-sheet" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-modal-header">
          <div className="ai-modal-title">
            <div className="ai-icon-bubble" style={{ background: '#4f46e5' }}>
              <QrCode size={18} color="#ffffff" />
            </div>
            <div>
              <h3>Pillar QR Code Navigator</h3>
              <small>Scan a physical mall pillar tag to set your start point</small>
            </div>
          </div>
          <button className="ai-close-btn" onClick={onClose} aria-label="Close QR scanner">
            <X size={20} />
          </button>
        </div>

        <div className="qr-modal-body">
          {/* Simulated Scanner Viewfinder */}
          <div className="qr-viewfinder">
            <div className="qr-laser-line" />
            <div className="qr-code-mockup">
              <QrCode size={96} color="#1e293b" />
            </div>
            <span className="qr-scan-label">
              {scanned ? '✓ Scanned Successfully!' : 'Point camera at any mall directory QR pillar'}
            </span>
            <small className="qr-demo-tag">Development Simulator</small>
          </div>

          {/* Quick Pillar Preset Selection */}
          <div className="qr-presets-section">
            <h4>Select a Pillar to Simulate Scan:</h4>
            <div className="qr-pillars-list">
              {QR_PILLARS.map(p => (
                <div
                  key={p.id}
                  className="qr-pillar-item"
                  onClick={() => handleSimulateScan(p)}
                >
                  <div className="qr-pillar-left">
                    <span className="qr-pillar-code">{p.code}</span>
                    <b>{p.name}</b>
                    <small>{p.floor} · {p.zone}</small>
                  </div>
                  <button type="button" className="qr-scan-btn">
                    Scan Here
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
