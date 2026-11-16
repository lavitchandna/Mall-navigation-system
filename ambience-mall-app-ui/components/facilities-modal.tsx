'use client'

import React, { useState } from 'react'
import { X, Navigation, Info, ShieldAlert, Car, ArrowUpCircle, Layers, HelpCircle } from 'lucide-react'
import { type Store } from '@/lib/api'

interface FacilitiesModalProps {
  isOpen: boolean
  onClose: () => void
  onNavigateToFacility: (facilityNode: Store) => void
}

interface FacilityItem {
  id: string
  name: string
  floor: string
  floorId: number
  type: string
  iconName: string
  description: string
  category: string
}

const REAL_FACILITIES: FacilityItem[] = [
  // Restrooms
  { id: 'G_CORR_N06', name: 'Restrooms (North Promenade)', floor: 'Ground Floor', floorId: 0, type: 'restroom', iconName: 'restroom', description: 'Next to North Atrium & Lifts', category: 'Restrooms' },
  { id: 'G_CORR_ATRIUM', name: 'Restrooms (Central Atrium)', floor: 'Ground Floor', floorId: 0, type: 'restroom', iconName: 'restroom', description: 'Beside Central Grand Atrium fountain', category: 'Restrooms' },
  { id: 'G_CORR_SOUTH_ATRIUM', name: 'Restrooms (South Wing)', floor: 'Ground Floor', floorId: 0, type: 'restroom', iconName: 'restroom', description: 'Near South Plaza & Exit', category: 'Restrooms' },
  { id: 'F1_CORR_N_ATRIUM', name: 'Restrooms (First Floor North)', floor: 'First Floor', floorId: 1, type: 'restroom', iconName: 'restroom', description: 'Near Home Centre & Titan', category: 'Restrooms' },
  { id: 'F1_CORR_ATRIUM', name: 'Restrooms (First Floor Central)', floor: 'First Floor', floorId: 1, type: 'restroom', iconName: 'restroom', description: 'Beside Central Grand Atrium void', category: 'Restrooms' },
  { id: 'F2_CORR_NORTH_ATRIUM', name: 'Restrooms (Second Floor North)', floor: 'Second Floor', floorId: 2, type: 'restroom', iconName: 'restroom', description: 'Beside Geetanjali Salon & Looks', category: 'Restrooms' },

  // Elevators
  { id: 'LIFT_NORTH_G', name: 'North Glass Elevator', floor: 'Ground Floor', floorId: 0, type: 'lift', iconName: 'lift', description: 'Connects GF, 1F, 2F near North Atrium', category: 'Elevators' },
  { id: 'LIFT_CENTRAL_G', name: 'Central Grand Atrium Elevator', floor: 'Ground Floor', floorId: 0, type: 'lift', iconName: 'lift', description: 'Main scenic elevator beside central fountain', category: 'Elevators' },
  { id: 'LIFT_SOUTH_G', name: 'South Boulevard Elevator', floor: 'Ground Floor', floorId: 0, type: 'lift', iconName: 'lift', description: 'Connects GF, 1F, 2F near Uniqlo & Trends', category: 'Elevators' },

  // Escalators
  { id: 'ESC_NORTH_G', name: 'North Escalator Bank', floor: 'Ground Floor', floorId: 0, type: 'escalator', iconName: 'escalator', description: 'Rapid transit between Ground & First Floor', category: 'Escalators' },
  { id: 'ESC_CENTRAL_G', name: 'Central Atrium Escalator Bank', floor: 'Ground Floor', floorId: 0, type: 'escalator', iconName: 'escalator', description: 'Direct escalator to 1F Grand Atrium', category: 'Escalators' },
  { id: 'ESC_SOUTH_G', name: 'South Promenade Escalator Bank', floor: 'Ground Floor', floorId: 0, type: 'escalator', iconName: 'escalator', description: 'Rapid transit near South Wing', category: 'Escalators' },

  // Information & Services
  { id: 'G_GATE_1', name: 'Concierge & Information Desk', floor: 'Ground Floor', floorId: 0, type: 'service', iconName: 'info', description: 'Customer help, wheelchair assistance & directory', category: 'Services' },
  { id: 'G_GATE_1', name: 'First Aid & Medical Emergency Station', floor: 'Ground Floor', floorId: 0, type: 'emergency', iconName: 'medical', description: 'Equipped medical station near Main Reception', category: 'Emergency' },
  { id: 'G_GATE_PARKING', name: 'Parking Lobby & Valet Reception', floor: 'Ground Floor', floorId: 0, type: 'parking', iconName: 'parking', description: 'Access to Basement 1 & 2 vehicle parking', category: 'Parking' },

  // Emergency Exits & Gates
  { id: 'G_GATE_1', name: 'Emergency Exit: Gate 1 (North Entry)', floor: 'Ground Floor', floorId: 0, type: 'emergency', iconName: 'exit', description: 'Main North emergency muster point to NH-8', category: 'Emergency' },
  { id: 'G_GATE_3', name: 'Emergency Exit: Gate 3 (South Entry)', floor: 'Ground Floor', floorId: 0, type: 'emergency', iconName: 'exit', description: 'South emergency exit to Ambience Island', category: 'Emergency' },
  { id: 'G_GATE_2', name: 'Emergency Exit: Gate 2 (East Promenade)', floor: 'Ground Floor', floorId: 0, type: 'emergency', iconName: 'exit', description: 'East outdoor driveway exit', category: 'Emergency' },
  { id: 'G_GATE_4', name: 'Emergency Exit: Gate 4 (West Plaza)', floor: 'Ground Floor', floorId: 0, type: 'emergency', iconName: 'exit', description: 'West wing plaza outdoor evacuation point', category: 'Emergency' }
]

export default function FacilitiesModal({
  isOpen,
  onClose,
  onNavigateToFacility,
}: FacilitiesModalProps) {
  const [activeCat, setActiveCat] = useState<string>('All')

  if (!isOpen) return null

  const categories = ['All', 'Restrooms', 'Elevators', 'Escalators', 'Services', 'Parking', 'Emergency']

  const filtered = activeCat === 'All'
    ? REAL_FACILITIES
    : REAL_FACILITIES.filter(f => f.category === activeCat)

  const handleNavigate = (f: FacilityItem) => {
    onNavigateToFacility({
      id: f.id,
      name: f.name,
      floor: f.floor,
      floorId: f.floorId,
      category: f.category,
      description: f.description
    })
    onClose()
  }

  return (
    <div className="ai-modal-backdrop" onClick={onClose}>
      <div className="ai-modal-sheet" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-modal-header">
          <div className="ai-modal-title">
            <div className="ai-icon-bubble" style={{ background: '#2563eb' }}>
              <Info size={18} color="#ffffff" />
            </div>
            <div>
              <h3>Mall Facilities & Services</h3>
              <small>Restrooms, Elevators, First Aid & Parking</small>
            </div>
          </div>
          <button className="ai-close-btn" onClick={onClose} aria-label="Close facilities">
            <X size={20} />
          </button>
        </div>

        {/* Categories Bar */}
        <div className="ai-quick-prompts">
          {categories.map(c => (
            <button
              key={c}
              type="button"
              className={`ai-quick-chip ${activeCat === c ? 'active' : ''}`}
              onClick={() => setActiveCat(c)}
            >
              {c}
            </button>
          ))}
        </div>

        {/* Facilities List */}
        <div className="facilities-scroll-list">
          {filtered.map(f => (
            <div key={f.id + f.name} className="facility-card">
              <div className="facility-card-icon">
                {f.category === 'Restrooms' && '🚻'}
                {f.category === 'Elevators' && '🛗'}
                {f.category === 'Escalators' && '🪜'}
                {f.category === 'Services' && 'ℹ️'}
                {f.category === 'Parking' && '🚗'}
                {f.category === 'Emergency' && '🚨'}
              </div>
              <div className="facility-card-info">
                <b>{f.name}</b>
                <p>{f.description}</p>
                <div className="facility-card-meta">
                  <span className="facility-floor-pill">{f.floor}</span>
                  <span className="facility-cat-pill">{f.category}</span>
                </div>
              </div>
              <button
                type="button"
                className="facility-nav-btn"
                onClick={() => handleNavigate(f)}
                title="Navigate to facility"
              >
                <Navigation size={14} />
                <span>Navigate</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
