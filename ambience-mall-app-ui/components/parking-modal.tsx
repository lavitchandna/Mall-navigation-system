'use client'

import React, { useState } from 'react'
import { X, Car, Navigation, Search, CheckCircle2 } from 'lucide-react'
import { type Store } from '@/lib/api'
import StoreLogo from '@/components/store-logo'

interface ParkingModalProps {
  isOpen: boolean
  onClose: () => void
  stores: Store[]
  onStartParkingNavigation: (parkingNodeId: string, store: Store) => void
}

const PARKING_ENTRANCES = [
  {
    id: 'G_GATE_PARKING',
    name: 'Parking Lobby (Basement 1 & 2)',
    description: 'Central elevator access straight to Ground Floor Grand Atrium',
    floor: 'Ground Floor',
    tag: 'Recommended'
  },
  {
    id: 'G_GATE_4',
    name: 'West Plaza Parking Entry',
    description: 'Direct entry near West Wing, ZARA and Fashion stores',
    floor: 'Ground Floor',
    tag: 'West Side'
  },
  {
    id: 'G_GATE_3',
    name: 'South Boulevard Parking Entry',
    description: 'Direct entry near South Wing, Uniqlo, Trends & Dining',
    floor: 'Ground Floor',
    tag: 'South Side'
  }
]

export default function ParkingModal({
  isOpen,
  onClose,
  stores,
  onStartParkingNavigation,
}: ParkingModalProps) {
  const [selectedParkingId, setSelectedParkingId] = useState<string>('G_GATE_PARKING')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedStore, setSelectedStore] = useState<Store | null>(null)

  if (!isOpen) return null

  const filteredStores = searchQuery.trim()
    ? stores.filter(s => s.name.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 6)
    : stores.slice(0, 6)

  const handleLaunch = () => {
    if (!selectedStore) return
    onStartParkingNavigation(selectedParkingId, selectedStore)
    onClose()
  }

  return (
    <div className="ai-modal-backdrop" onClick={onClose}>
      <div className="ai-modal-sheet" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-modal-header">
          <div className="ai-modal-title">
            <div className="ai-icon-bubble" style={{ background: '#059669' }}>
              <Car size={18} color="#ffffff" />
            </div>
            <div>
              <h3>Parking Assistant</h3>
              <small>Navigate from your parked vehicle to any store</small>
            </div>
          </div>
          <button className="ai-close-btn" onClick={onClose} aria-label="Close parking assistant">
            <X size={20} />
          </button>
        </div>

        <div className="parking-modal-body">
          {/* Step 1: Select Parking Entrance */}
          <div className="parking-step-section">
            <h4>1. Where did you park?</h4>
            <div className="parking-options-grid">
              {PARKING_ENTRANCES.map(p => (
                <div
                  key={p.id}
                  className={`parking-opt-card ${selectedParkingId === p.id ? 'active' : ''}`}
                  onClick={() => setSelectedParkingId(p.id)}
                >
                  <div className="parking-opt-header">
                    <b>{p.name}</b>
                    <span className="parking-tag">{p.tag}</span>
                  </div>
                  <p>{p.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Step 2: Choose Destination Store */}
          <div className="parking-step-section">
            <h4>2. Where do you want to go?</h4>
            <div className="parking-search-box">
              <Search size={16} color="#64748b" />
              <input
                type="text"
                placeholder="Search store name (e.g. Asics, ZARA, Food)..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="parking-store-chips">
              {filteredStores.map(s => (
                <button
                  key={s.id}
                  type="button"
                  className={`parking-store-chip ${selectedStore?.id === s.id ? 'selected' : ''}`}
                  onClick={() => setSelectedStore(s)}
                >
                  <StoreLogo store={s} size="xs" />
                  <span>{s.name}</span>
                  <small>({s.floor})</small>
                </button>
              ))}
            </div>
          </div>

          {/* Action Button */}
          <div className="parking-action-bar">
            <button
              type="button"
              className="parking-submit-btn"
              disabled={!selectedStore}
              onClick={handleLaunch}
            >
              <Navigation size={16} />
              <span>
                {selectedStore ? `Navigate to ${selectedStore.name} from Parking` : 'Select a store to navigate'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
