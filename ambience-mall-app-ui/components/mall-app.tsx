'use client'

import React, { useMemo, useState, useEffect } from 'react'
import useSWR, { type SWRConfiguration } from 'swr'
import {
  ArrowLeft,
  ChevronRight,
  Heart,
  LocateFixed,
  MapPin,
  Navigation,
  Phone,
  Plus,
  Search,
  SlidersHorizontal,
  Minus,
  Sparkles,
  ChevronLeft,
  Cpu,
  Zap,
  Users,
  Compass,
  Home as HomeIcon,
  ArrowRight,
  Send,
  Clock,
  Car,
  Utensils,
  ShoppingBag,
  ChevronUp,
  ChevronDown,
  Layers,
  Flame,
  Award,
  Film,
  Coffee,
  Check,
  Shirt,
  Gem,
  Laptop,
  Armchair,
  UtensilsCrossed
} from 'lucide-react'
import {
  connectorLabel,
  floorLabel,
  getFloorGeometry,
  getFloors,
  getLocations,
  getNearby,
  getRoute,
  type Floor,
  type Store,
  type Route,
  type RouteMode,
  type RouteAlgorithm
} from '@/lib/api'
import RouteMap from '@/components/route-map'
import FacilitiesModal from '@/components/facilities-modal'
import ParkingModal from '@/components/parking-modal'
import AcademicEvalModal from '@/components/academic-eval-modal'
import VoiceSearchButton from '@/components/voice-search'
import StoreLogo from '@/components/store-logo'

export type TabScreen = 'home' | 'explore' | 'navigate' | 'ai'
export type Screen = TabScreen | 'detail'
export type Go = (screen: Screen, store?: Store, query?: string) => void

const swrOptions: SWRConfiguration = {
  revalidateOnFocus: false,
  errorRetryInterval: 4000,
  errorRetryCount: 4,
}

const offlineFloors: Floor[] = [
  { id: 0, name: 'Ground Floor' },
  { id: 1, name: 'First Floor' },
  { id: 2, name: 'Second Floor' },
]

// =============================================================================
// LUXURY APP HEADER (FOR DETAIL & EXPLORE SCREENS)
// =============================================================================

function SubHeader({
  title,
  subtitle,
  onBack,
  onOpenEval,
}: {
  title: string
  subtitle?: string
  onBack?: () => void
  onOpenEval?: () => void
}) {
  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        background: 'rgba(250, 248, 245, 0.96)',
        backdropFilter: 'blur(14px)',
        borderBottom: '1px solid var(--border-light)',
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            aria-label="Go back"
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: '#ffffff',
              border: '1px solid var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--text-primary)',
            }}
          >
            <ArrowLeft size={16} />
          </button>
        )}
        <div>
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            {title}
          </h2>
          {subtitle && (
            <span style={{ fontSize: '10.5px', color: 'var(--gold-accent)', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              {subtitle}
            </span>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {onOpenEval && (
          <button
            type="button"
            onClick={onOpenEval}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '5px 9px',
              borderRadius: 'var(--radius-full)',
              background: '#fbf7ff',
              border: '1px solid #e9d5ff',
              color: '#6b21a8',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <Cpu size={12} />
            <span>RL Viva</span>
          </button>
        )}
      </div>
    </header>
  )
}

// =============================================================================
// BOTTOM NAVIGATION BAR (Strictly 4 Tabs: HOME, EXPLORE, NAVIGATE, AI)
// =============================================================================

function BottomNavigation({ screen, go }: { screen: Screen; go: Go }) {
  const tabs: Array<{ id: TabScreen; label: string; icon: React.ReactNode }> = [
    { id: 'home', label: 'Home', icon: <HomeIcon size={19} /> },
    { id: 'explore', label: 'Explore', icon: <Compass size={19} /> },
    { id: 'navigate', label: 'Navigate', icon: <Navigation size={19} /> },
    { id: 'ai', label: 'Concierge', icon: <Sparkles size={19} /> },
  ]

  const activeTabId = screen === 'detail' ? 'explore' : screen

  return (
    <nav className="luxury-bottom-nav" aria-label="Main Navigation">
      {tabs.map(tab => {
        const isActive = activeTabId === tab.id
        return (
          <button
            key={tab.id}
            className={`nav-tab-btn ${isActive ? 'active' : ''}`}
            onClick={() => go(tab.id)}
            aria-current={isActive ? 'page' : undefined}
          >
            {isActive && <div className="nav-tab-indicator" />}
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

// =============================================================================
// 1. HOME SCREEN (CINEMATIC HERO + ASYMMETRIC ACTIONS + EDITORIAL DISCOVERY)
// =============================================================================

function Home({
  go,
  onOpenFacilities,
  onOpenEval,
  onOpenPlanner,
}: {
  go: Go
  onOpenFacilities: () => void
  onOpenEval: () => void
  onOpenPlanner: () => void
}) {
  const [query, setQuery] = useState('')
  const { data: directoryData } = useSWR('locations', getLocations, swrOptions)
  const stores = directoryData?.stores ?? []

  // Autocomplete search filtering
  const searchResults = useMemo(() => {
    if (!query.trim()) return []
    const q = query.trim().toLowerCase()
    return stores
      .filter(s => s.name.toLowerCase().includes(q) || (s.category && s.category.toLowerCase().includes(q)))
      .slice(0, 5)
  }, [stores, query])

  // Featured flagship store for large editorial card (e.g. ZARA)
  const featuredStore = useMemo(() => {
    return stores.find(s => s.name.toLowerCase() === 'zara') || stores[0]
  }, [stores])

  // Curated flagship brands for horizontal rail
  const flagshipBrands = useMemo(() => {
    const targetNames = ["Paul's Bakery", 'Nike', 'Diesel', 'Lacoste', 'Onitsuka Tiger', 'Asics', 'Barista', "Levi's", 'Aldo']
    const matched = targetNames.map(name => stores.find(s => s.name.toLowerCase() === name.toLowerCase())).filter(Boolean) as Store[]
    return matched.length > 0 ? matched : stores.slice(1, 9)
  }, [stores])

  const editorialCategories: Array<{
    title: string
    sub: string
    icon: React.ReactNode
    filterCat?: string
  }> = [
    { title: 'Fashion', sub: 'Runway & Luxury', icon: <Shirt size={17} strokeWidth={1.6} /> },
    { title: 'Dining', sub: 'Cafes & Bistro', icon: <UtensilsCrossed size={17} strokeWidth={1.6} />, filterCat: 'Food & Dining' },
    { title: 'Beauty', sub: 'Skincare & Care', icon: <Sparkles size={17} strokeWidth={1.6} />, filterCat: 'Beauty & Wellness' },
    { title: 'Jewellery', sub: 'Gold & Diamond', icon: <Gem size={17} strokeWidth={1.6} />, filterCat: 'Jewellery & Luxury' },
    { title: 'Electronics', sub: 'Audio & Gadgets', icon: <Laptop size={17} strokeWidth={1.6} />, filterCat: 'Electronics' },
    { title: 'Lifestyle', sub: 'Home & Decor', icon: <Armchair size={17} strokeWidth={1.6} />, filterCat: 'Home & Lifestyle' },
  ]

  const handleSelectStore = (store: Store) => {
    setQuery('')
    go('navigate', store)
  }

  return (
    <>
      <main className="page home-page">
        {/* GRAND EDITORIAL HERO SECTION */}
        <div className="home-hero-container">
          <div className="home-hero-backdrop" />
          <div className="home-hero-glow" />

          {/* Top Branding & Status Row */}
          <div className="hero-top-row">
            <div className="hero-brand-block">
              <h1>Ambience</h1>
              <span>Gurugram</span>
            </div>
            <a
              href="tel:+918860800800"
              className="hero-status-pill"
              title="Call Ambience Concierge (+91 88608 00800)"
            >
              <Phone size={10} color="#a6824e" />
              <span>Concierge</span>
            </a>
          </div>

          {/* Hero Headlines */}
          <div className="hero-headline-block">
            <span className="hero-kicker">Digital Concierge</span>
            <h2 className="hero-display-quote">
              Your mall.<br />Your way.
            </h2>
            <p className="hero-subquote">
              Indoor navigation &amp; 221 verified luxury brands across 3 floors.
            </p>
          </div>

          {/* Hero Embedded Search Bar */}
          <div className="hero-search-wrapper">
            <form
              className="hero-search-field"
              role="search"
              onSubmit={e => {
                e.preventDefault()
                if (query.trim()) go('explore', undefined, query.trim())
              }}
            >
              <Search size={18} color="#635f58" />
              <input
                type="search"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search stores, food &amp; experiences…"
                aria-label="Search stores, food, facilities"
              />
              <VoiceSearchButton onResult={text => go('explore', undefined, text)} />
            </form>

            {/* Autocomplete Dropdown */}
            {searchResults.length > 0 && (
              <div className="search-autocomplete-card">
                {searchResults.map(s => (
                  <div key={s.id} className="search-item-row" onClick={() => handleSelectStore(s)}>
                    <div className="search-item-info">
                      <StoreLogo store={s} size="sm" />
                      <div className="search-item-text">
                        <div className="search-item-name">{s.name}</div>
                        <div className="search-item-sub">{s.floor || 'Ground Floor'} · {s.category}</div>
                      </div>
                    </div>
                    <button type="button" className="search-item-action">
                      <Navigation size={11} />
                      <span>Route</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Hero Footer Bar */}
          <div className="hero-footer-bar">
            <button type="button" className="hero-footer-link" onClick={() => go('explore')}>
              <span>Explore all directory</span>
              <ArrowRight size={13} />
            </button>
            <span className="hero-floors-meta">GF · 1F · 2F · RL Online</span>
          </div>
        </div>

        {/* ASYMMETRIC SMART ACTIONS */}
        <div className="smart-actions-asymmetric">
          {/* Large Hero Primary Card: NAVIGATE */}
          <div className="smart-action-hero" onClick={() => go('navigate')}>
            <Navigation size={72} className="action-hero-bg-icon" />
            <div className="action-hero-top">
              <span className="action-hero-tag">
                <span className="status-dot-pulse" style={{ background: '#a6824e', boxShadow: '0 0 6px #a6824e' }} />
                <span>Q-Learning Route</span>
              </span>
              <span className="action-hero-btn">
                <span>Start</span>
                <ArrowRight size={11} />
              </span>
            </div>
            <h3 className="action-hero-title">Indoor Navigation</h3>
            <p className="action-hero-sub">
              Instant obstacle-free path across Ground, 1st &amp; 2nd floor corridors.
            </p>
          </div>
        </div>

        {/* Secondary Actions (3-Columns) */}
        <div className="smart-actions-secondary-row">
          <div className="smart-action-secondary" onClick={() => go('explore')}>
            <div className="smart-action-icon-wrap">
              <ShoppingBag size={17} />
            </div>
            <span className="smart-action-label">Find Store</span>
            <span className="smart-action-sublabel">221 Brands</span>
          </div>

          <div className="smart-action-secondary" onClick={() => go('explore', undefined, 'Food & Dining')}>
            <div className="smart-action-icon-wrap">
              <Utensils size={17} />
            </div>
            <span className="smart-action-label">Dining</span>
            <span className="smart-action-sublabel">Cafes &amp; Court</span>
          </div>

          <div className="smart-action-secondary gold-tile" onClick={onOpenFacilities}>
            <div className="smart-action-icon-wrap">
              <MapPin size={17} />
            </div>
            <span className="smart-action-label">Nearby</span>
            <span className="smart-action-sublabel">Lifts &amp; Lobbies</span>
          </div>
        </div>

        {/* EDITORIAL "PLAN YOUR VISIT" CARD */}
        <div className="editorial-planner-card">
          <div className="editorial-planner-accent" />
          <div className="editorial-planner-header">
            <span className="editorial-planner-tag">Curated Itinerary</span>
            <span className="editorial-duration-badge">2 Hours</span>
          </div>
          <h3 className="editorial-planner-title">Make the most of your time.</h3>
          <p className="editorial-planner-sub">
            Personalized visit itinerary linking fashion, artisan coffee and dining with optimal walking sequence.
          </p>
          <div className="editorial-curated-chips">
            <span className="curated-chip-item">Shopping</span>
            <span className="curated-chip-item">Coffee</span>
            <span className="curated-chip-item">Dining</span>
          </div>
          <button type="button" className="editorial-planner-cta" onClick={onOpenPlanner}>
            <span>Build my itinerary</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* DISCOVERY SECTION (LARGE FEATURED STORE + HORIZONTAL RAIL) */}
        <div className="discovery-section-wrap">
          <div className="discovery-section-header">
            <h3 className="discovery-title">Discover Ambience</h3>
            <button type="button" className="discovery-link-btn" onClick={() => go('explore')}>
              View 221 stores →
            </button>
          </div>

          {/* Large Featured Store Card */}
          {featuredStore && (
            <div className="featured-store-hero-card" onClick={() => go('detail', featuredStore)}>
              <div className="featured-store-left">
                <StoreLogo store={featuredStore} size="md" />
                <div className="featured-store-info">
                  <span className="featured-store-badge">Featured Flagship</span>
                  <h4 className="featured-store-title">{featuredStore.name}</h4>
                  <span className="featured-store-meta">{featuredStore.category} · {featuredStore.floor || 'Ground Floor'}</span>
                </div>
              </div>
              <button
                type="button"
                className="featured-store-cta"
                onClick={e => {
                  e.stopPropagation()
                  go('navigate', featuredStore)
                }}
              >
                <span>Navigate</span>
                <ChevronRight size={13} />
              </button>
            </div>
          )}

          {/* Horizontal Flagship Brand Rail */}
          <div className="flagship-brand-rail">
            {flagshipBrands.map(s => (
              <div key={s.id} className="flagship-brand-chip" onClick={() => go('detail', s)}>
                <StoreLogo store={s} size="md" />
                <span className="flagship-brand-name">{s.name}</span>
                <span className="flagship-brand-floor">{s.floor || 'Ground Floor'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* EDITORIAL CATEGORY TILES */}
        <div style={{ marginBottom: '24px' }}>
          <div className="discovery-section-header">
            <h3 className="discovery-title">Browse by Category</h3>
          </div>
          <div className="category-editorial-grid">
            {editorialCategories.map(cat => (
              <div
                key={cat.title}
                className="category-editorial-tile"
                onClick={() => go('explore', undefined, cat.filterCat || cat.title)}
              >
                <span className="category-editorial-icon">{cat.icon}</span>
                <span className="category-editorial-title">{cat.title}</span>
                <span className="category-editorial-sub">{cat.sub}</span>
              </div>
            ))}
          </div>
        </div>

        {/* SUBTLE RL TECHNICAL TELEMETRY CALLOUT */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-subtle)',
            marginBottom: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: '#fbf7ff',
                color: '#6b21a8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Cpu size={16} />
            </div>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Q-Learning Navigation Policy
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                Trained on 342,732 states with Dijkstra baseline validation
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onOpenEval}
            style={{
              background: '#fbf7ff',
              border: '1px solid #e9d5ff',
              color: '#6b21a8',
              padding: '5px 9px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Viva Scorecard
          </button>
        </div>
      </main>
      <BottomNavigation screen="home" go={go} />
    </>
  )
}

// =============================================================================
// 2. EXPLORE SCREEN (RETAIL DISCOVERY & VARIANT EDITORIAL CARDS)
// =============================================================================

function Explore({
  go,
  favorites,
  toggleFavorite,
  initialQuery = '',
  onOpenEval,
}: {
  go: Go
  favorites: string[]
  toggleFavorite: (id: string) => void
  initialQuery?: string
  onOpenEval: () => void
}) {
  const [query, setQuery] = useState(initialQuery)
  const [selectedFloor, setSelectedFloor] = useState<number | 'all'>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const { data: directoryData } = useSWR('locations', getLocations, swrOptions)
  const stores = directoryData?.stores ?? []
  const categories = directoryData?.categories ?? []

  useEffect(() => {
    if (initialQuery) {
      if (categories.includes(initialQuery)) {
        setSelectedCategory(initialQuery)
        setQuery('')
      } else {
        setQuery(initialQuery)
      }
    }
  }, [initialQuery, categories])

  const filteredStores = useMemo(() => {
    return stores.filter(s => {
      if (selectedFloor !== 'all' && s.floorId !== selectedFloor) return false
      if (selectedCategory !== 'all' && s.category !== selectedCategory) return false
      if (query.trim()) {
        const q = query.toLowerCase()
        const matchName = s.name.toLowerCase().includes(q)
        const matchCat = s.category && s.category.toLowerCase().includes(q)
        if (!matchName && !matchCat) return false
      }
      return true
    })
  }, [stores, selectedFloor, selectedCategory, query])

  return (
    <>
      <SubHeader title="Explore Ambience" subtitle="Store Directory" onBack={() => go('home')} onOpenEval={onOpenEval} />
      <main className="page stores-page">
        {/* Editorial Top Headline */}
        <div className="explore-editorial-header">
          <h2 className="explore-editorial-title">Find something worth discovering.</h2>
          <p className="explore-editorial-sub">Browse 221 verified stores across Ground, First and Second floors.</p>
        </div>

        {/* Large Search Field */}
        <div className="search-container-wrap" style={{ marginBottom: '12px' }}>
          <form className="search-field-luxury" role="search" onSubmit={e => e.preventDefault()}>
            <Search size={18} color="#635f58" />
            <input
              type="search"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search brand, category, or keyword…"
            />
            <VoiceSearchButton onResult={setQuery} />
          </form>
        </div>

        {/* Category & Floor Filters */}
        <div className="explore-filter-row">
          <select
            className="luxury-select"
            value={selectedFloor}
            onChange={e => setSelectedFloor(e.target.value === 'all' ? 'all' : Number(e.target.value))}
          >
            <option value="all">All Floors (GF, 1F, 2F)</option>
            <option value={0}>Ground Floor</option>
            <option value={1}>First Floor</option>
            <option value={2}>Second Floor</option>
          </select>

          <select
            className="luxury-select"
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories ({categories.length})</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Verified Store Count */}
        <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginBottom: '8px', padding: '0 2px' }}>
          Showing {filteredStores.length} stores
        </div>

        {/* 2-Column Luxury Store Cards */}
        <div className="stores-grid-2col">
          {filteredStores.map(store => {
            const isFav = favorites.includes(store.id)
            return (
              <div key={store.id} className="store-directory-card">
                <div>
                  <div className="store-card-header">
                    <StoreLogo store={store} size="md" />
                    <button
                      type="button"
                      className={`heart-fav-btn ${isFav ? 'is-fav' : ''}`}
                      onClick={() => toggleFavorite(store.id)}
                      aria-label="Save favorite"
                    >
                      <Heart size={16} fill={isFav ? '#dc2626' : 'none'} color={isFav ? '#dc2626' : '#969188'} />
                    </button>
                  </div>
                  <div className="store-card-body" onClick={() => go('detail', store)}>
                    <h3 className="store-card-title">{store.name}</h3>
                    <div className="store-card-meta">{store.category || 'Retail'}</div>
                  </div>
                </div>

                <div className="store-card-footer">
                  <span className="store-floor-pill">
                    {store.floorId === 0 ? 'Ground' : store.floorId === 1 ? '1st Floor' : '2nd Floor'}
                  </span>
                  <button
                    type="button"
                    className="store-nav-cta"
                    onClick={() => go('navigate', store)}
                  >
                    <span>Navigate</span>
                    <ChevronRight size={13} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </main>
      <BottomNavigation screen="explore" go={go} />
    </>
  )
}

// =============================================================================
// 3. STORE DETAIL SCREEN
// =============================================================================

function Detail({
  store,
  go,
  favorite,
  toggleFavorite,
  onOpenEval,
}: {
  store: Store
  go: Go
  favorite: boolean
  toggleFavorite: () => void
  onOpenEval: () => void
}) {
  const { data: nearbyStores } = useSWR(
    store ? ['nearby', store.id] : null,
    () => getNearby(store.id, 4),
    swrOptions
  )

  return (
    <>
      <SubHeader title={store.name} subtitle={store.floor || 'Ground Floor'} onBack={() => go('explore')} onOpenEval={onOpenEval} />
      <main className="page" style={{ paddingTop: '16px' }}>
        <div className="store-detail-container">
          <div className="store-detail-emblem-wrap">
            <StoreLogo store={store} size="lg" />
            <button
              type="button"
              className="store-detail-fav-btn"
              onClick={toggleFavorite}
              aria-label="Favorite store"
            >
              <Heart size={18} fill={favorite ? '#dc2626' : 'none'} color={favorite ? '#dc2626' : '#635f58'} />
            </button>
          </div>

          <div className="store-detail-category">{store.category || 'Retail'}</div>
          <h2 className="store-detail-title">{store.name}</h2>
          <div className="store-detail-location-row">
            <MapPin size={15} color="#a6824e" />
            <span>{store.floor || 'Ground Floor'} · Ambience Mall Gurugram</span>
          </div>

          <button
            type="button"
            className="store-primary-nav-btn"
            onClick={() => go('navigate', store)}
          >
            <Navigation size={18} />
            <span>Navigate to Store</span>
          </button>

          <div className="store-info-panel">
            <h4>Store Details</h4>
            <div className="store-info-grid">
              <div className="store-info-cell">
                <small>Floor Level</small>
                <b>{store.floor || 'Ground Floor'}</b>
              </div>
              <div className="store-info-cell">
                <small>Category</small>
                <b>{store.category || 'Retail'}</b>
              </div>
            </div>
            <p className="store-info-desc">
              {store.description ||
                `Visit ${store.name} at Ambience Mall Gurugram. Direct corridor access with live Q-policy reinforcement learning navigation.`}
            </p>
          </div>

          {/* Nearby Stores in this Wing */}
          {nearbyStores && nearbyStores.length > 0 && (
            <div style={{ width: '100%', textAlign: 'left', marginTop: '10px' }}>
              <div className="section-label-row">
                <span className="section-label">Nearby in this Wing</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                {nearbyStores.map(n => (
                  <div
                    key={n.id}
                    onClick={() => go('detail', n)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      background: '#ffffff',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      boxShadow: 'var(--shadow-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <StoreLogo store={n} size="sm" />
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>{n.name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{n.category} · {n.floor || 'Ground Floor'}</div>
                      </div>
                    </div>
                    <ChevronRight size={16} color="#969188" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
      <BottomNavigation screen="explore" go={go} />
    </>
  )
}

// =============================================================================
// 4. NAVIGATION SCREEN (THE HERO MAP — 75-80% VIEWPORT + FLOATING CONTROLS)
// =============================================================================

function Navigate({
  store,
  go,
  initialStartId = 'G_GATE_1',
  onOpenEval,
}: {
  store?: Store
  go: Go
  initialStartId?: string
  onOpenEval: () => void
}) {
  const [routeMode, setRouteMode] = useState<RouteMode>('standard')
  const [selectedAlgo, setSelectedAlgo] = useState<RouteAlgorithm>('auto')
  const [userFloor, setUserFloor] = useState<number | null>(null)
  const [zoom, setZoom] = useState(1)
  const [resetKey, setResetKey] = useState(0)
  const [showStores, setShowStores] = useState(false)
  const [startGateId, setStartGateId] = useState<string>(initialStartId || 'G_GATE_1')
  const [isSheetExpanded, setIsSheetExpanded] = useState(false)
  const [activeStepIndex, setActiveStepIndex] = useState(0)

  useEffect(() => {
    if (initialStartId) {
      setStartGateId(initialStartId)
    }
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const isExp = params.get('sheet') === 'expanded'
      if (isExp) setIsSheetExpanded(true)
      const urlFrom = params.get('from') || params.get('start')
      if (urlFrom) setStartGateId(urlFrom)
    }
  }, [initialStartId])

  const { data: directoryData } = useSWR('locations', getLocations, swrOptions)
  const gates = directoryData?.gates ?? []

  // Dynamic Route calculation
  const { data: route, error: routeError, isLoading: routeLoading } = useSWR(
    store ? ['route', store.id, startGateId, routeMode, selectedAlgo] : null,
    () =>
      getRoute(store!.id, {
        startId: startGateId,
        profile: routeMode,
        algorithm: selectedAlgo,
      }),
    swrOptions
  )

  const { data: floorData } = useSWR('floors', getFloors, swrOptions)
  const floors = floorData?.length ? floorData : offlineFloors

  const activeFloor = userFloor ?? route?.segments[0]?.floor ?? store?.floorId ?? 0
  const activeFloorName = floors.find(item => item.id === activeFloor)?.name ?? `Floor ${activeFloor}`

  const { data: geometry } = useSWR(
    ['geometry', activeFloor],
    () => getFloorGeometry(activeFloor),
    swrOptions
  )

  const activeSegments = useMemo(
    () => route?.segments.filter(segment => segment.floor === activeFloor) ?? [],
    [route, activeFloor]
  )

  const lastActiveIndex = route
    ? route.segments.reduce((found, segment, index) => (segment.floor === activeFloor ? index : found), -1)
    : -1
  const nextSegment = route && lastActiveIndex >= 0 ? route.segments[lastActiveIndex + 1] : undefined
  const hop = route && nextSegment
    ? route.connectors.find(connector => connector.from.floor === activeFloor && connector.to.floor === nextSegment.floor)
    : undefined

  const evalData = route?.evaluation
  const directions = route?.directions ?? []

  return (
    <>
      <main className="page nav-page">
        <div className="nav-hero-viewport">
          {/* Top Floating Destination Pill */}
          <div className="nav-floating-top-pill">
            <div className="nav-top-pill-left">
              <button
                className="nav-pill-back-btn"
                onClick={() => go(store ? 'detail' : 'home', store)}
                aria-label="Go back"
              >
                <ArrowLeft size={15} />
              </button>
              <div className="nav-pill-info">
                <div className="nav-pill-dest">{store ? store.name : 'Ambience Mall Navigator'}</div>
                <div className="nav-pill-meta">
                  {store ? `${store.floor || 'Ground Floor'} · ${routeMode.toUpperCase()}` : 'Select destination'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="nav-pill-badge">
                <Sparkles size={10} />
                <span>Smart Route</span>
              </span>
            </div>
          </div>

          {/* Floating Minimal Floor Switcher: G | 1 | 2 */}
          <div className="nav-floating-floor-stack">
            {floors.map(floor => {
              const isActive = activeFloor === floor.id
              const hasRoute = route?.floors.includes(floor.id)
              const label = floor.id === 0 ? 'G' : floor.id === 1 ? '1' : '2'
              return (
                <button
                  key={floor.id}
                  className={`floor-circle-btn ${isActive ? 'active' : ''} ${hasRoute ? 'has-route' : ''}`}
                  onClick={() => setUserFloor(floor.id)}
                  title={floor.name}
                >
                  {label}
                </button>
              )
            })}
          </div>

          {/* Floating Minimal Tools Stack (Right) */}
          <div className="nav-floating-tools-stack">
            <button
              className="nav-tool-circle-btn"
              onClick={() => setZoom(v => Math.min(6, v * 1.35))}
              aria-label="Zoom in"
            >
              <Plus size={17} />
            </button>
            <button
              className="nav-tool-circle-btn"
              onClick={() => setZoom(v => Math.max(0.6, v / 1.35))}
              aria-label="Zoom out"
            >
              <Minus size={17} />
            </button>
            <button
              className="nav-tool-circle-btn"
              onClick={() => {
                setZoom(1)
                setResetKey(k => k + 1)
              }}
              aria-label="Recenter map"
            >
              <LocateFixed size={17} />
            </button>
            <button
              className={`nav-tool-circle-btn ${showStores ? 'active' : ''}`}
              onClick={() => setShowStores(s => !s)}
              aria-label="Toggle store labels"
              title="Toggle store pin labels"
            >
              <SlidersHorizontal size={17} />
            </button>
          </div>

          {/* Map Canvas — Occupies 75-80% of Viewport */}
          <RouteMap
            floorId={activeFloor}
            floorName={activeFloorName}
            geometry={geometry}
            segments={activeSegments}
            route={route}
            showStores={showStores}
            zoom={zoom}
            resetKey={resetKey}
          />

          {/* Multi-floor transition floating pill */}
          {nextSegment && (
            <div
              className="floating-connector-banner"
              onClick={() => setUserFloor(nextSegment.floor)}
              title="Click to view next floor"
              style={{ top: '64px' }}
            >
              <span>
                {activeFloor === 0 ? 'Ground' : activeFloor === 1 ? '1st Floor' : '2nd Floor'} → {nextSegment.floor === 0 ? 'Ground' : nextSegment.floor === 1 ? '1st Floor' : '2nd Floor'}
              </span>
              <span>·</span>
              <span>{hop ? connectorLabel(hop.type) : 'Central Escalator'}</span>
              <ChevronRight size={13} />
            </div>
          )}

          {/* Modern Floating Route Bottom Sheet */}
          <div className={`nav-floating-bottom-sheet ${isSheetExpanded ? 'expanded' : 'collapsed'}`}>
            {/* Drag Pill Handle */}
            <div
              className="sheet-handle-pill-wrap"
              onClick={() => setIsSheetExpanded(x => !x)}
            >
              <div className="sheet-handle-pill" />
            </div>

            {/* Collapsed Bar Body */}
            <div className="sheet-collapsed-body">
              {store ? (
                <>
                  <div className="sheet-route-summary-row">
                    <div className="sheet-dest-info-wrap">
                      <StoreLogo store={store} size="sm" />
                      <div className="sheet-dest-titles">
                        <span className="sheet-dest-eyebrow">TO {store.name.toUpperCase()}</span>
                        <h3 className="sheet-dest-heading">{store.name}</h3>
                        <span className="sheet-dest-meta-line">
                          {store.floor || 'Ground Floor'} · {hop ? `via ${connectorLabel(hop.type)}` : 'Direct corridor'}
                        </span>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="sheet-start-nav-btn"
                      onClick={() => setIsSheetExpanded(x => !x)}
                    >
                      <span>{isSheetExpanded ? 'View Map' : 'Start Navigation'}</span>
                      {isSheetExpanded ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                    </button>
                  </div>

                  {/* Smart Route subtle banner with uncalibrated metric policy */}
                  <div className="smart-route-subtle-badge">
                    <span>✦ <b>RL Recommended Route</b></span>
                    <span>
                      {routeLoading
                        ? 'Computing policy…'
                        : route
                        ? `Cost: ${route.pathCost.toFixed(1)} · Walking time uncalibrated`
                        : 'Ready'}
                    </span>
                  </div>
                </>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 0' }}>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>Select Destination</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Choose from 221 stores across 3 floors</div>
                  </div>
                  <button
                    type="button"
                    className="sheet-start-nav-btn"
                    onClick={() => go('explore')}
                  >
                    <span>Find Store</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              )}
            </div>

            {/* Expanded Detailed Route Controls & Turn-by-Turn Steps */}
            {isSheetExpanded && store && (
              <div className="sheet-expanded-content">
                {/* 1. Route Mode Selection (Standard, Crowd-Aware, Accessible) */}
                <div className="mode-toggle-shelf">
                  <button
                    type="button"
                    className={`mode-tab-btn ${routeMode === 'standard' ? 'active mode-standard' : ''}`}
                    onClick={() => setRouteMode('standard')}
                  >
                    <Zap size={13} />
                    <span>Standard</span>
                  </button>
                  <button
                    type="button"
                    className={`mode-tab-btn ${routeMode === 'crowd_aware' ? 'active mode-crowd' : ''}`}
                    onClick={() => setRouteMode('crowd_aware')}
                  >
                    <Users size={13} />
                    <span>Crowd-Aware</span>
                  </button>
                  <button
                    type="button"
                    className={`mode-tab-btn ${routeMode === 'accessible' ? 'active mode-accessible' : ''}`}
                    onClick={() => setRouteMode('accessible')}
                  >
                    <span>♿ Accessible</span>
                  </button>
                </div>

                {/* 2. Route Engine Selection (Auto Recommended, RL Q-Policy, Dijkstra Baseline) */}
                {evalData && (
                  <div className="algo-comparator-shelf">
                    <div className="algo-btn-pair">
                      <button
                        type="button"
                        className={`algo-switch-btn ${selectedAlgo === 'auto' ? 'selected' : ''}`}
                        onClick={() => setSelectedAlgo('auto')}
                      >
                        ✨ Auto
                      </button>
                      <button
                        type="button"
                        className={`algo-switch-btn ${selectedAlgo === 'rl' ? 'selected' : ''}`}
                        onClick={() => setSelectedAlgo('rl')}
                      >
                        🤖 RL Policy
                      </button>
                      <button
                        type="button"
                        className={`algo-switch-btn ${selectedAlgo === 'dijkstra' ? 'selected' : ''}`}
                        onClick={() => setSelectedAlgo('dijkstra')}
                      >
                        📐 Dijkstra
                      </button>
                    </div>
                    <span className="algo-match-badge">
                      {evalData.identicalPath ? 'Identical Optimal' : `Diff: ${(evalData.rl.pathCost - evalData.baseline.pathCost).toFixed(1)}`}
                    </span>
                  </div>
                )}

                {/* Routing Engine Telemetry Indicator */}
                {route && (
                  <div className="algo-engine-indicator">
                    <span>Routing Engine:</span>
                    <span className={`engine-pill ${route.algorithm === 'rl' ? 'rl' : (route.isFallback || route.algorithm === 'dijkstra_fallback') ? 'fallback' : 'dijkstra'}`}>
                      {route.algorithm === 'rl' ? 'RL / Q-LEARNING' : (route.isFallback || route.algorithm === 'dijkstra_fallback') ? 'DIJKSTRA FALLBACK' : 'DIJKSTRA BASELINE'}
                    </span>
                  </div>
                )}

                {/* 3. Starting Gate Selector */}
                <div className="start-point-row">
                  <label htmlFor="gate-select">Starting Point:</label>
                  <select
                    id="gate-select"
                    className="start-gate-select"
                    value={startGateId}
                    onChange={e => setStartGateId(e.target.value)}
                  >
                    <optgroup label="Ground Floor Entrances">
                      {gates.map(gate => (
                        <option key={gate.id} value={gate.id}>
                          {gate.name}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Parking &amp; Valet">
                      <option value="G_GATE_PARKING">Parking Lobby &amp; Valet Entry</option>
                      <option value="G_GATE_4">West Plaza Entry</option>
                      <option value="G_GATE_3">Main Entry / Exit (Gate 1)</option>
                    </optgroup>
                    <optgroup label="Stores &amp; Locations">
                      {(directoryData?.stores ?? []).map(s => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.floor || 'Ground'})
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>

                {/* 4. Turn-by-Turn Guidance Steps */}
                {directions.length > 0 && (
                  <div className="directions-shelf">
                    <h4>Turn-by-Turn Guidance ({directions.length} steps)</h4>
                    {directions.map((step, idx) => (
                      <div
                        key={idx}
                        className={`direction-step-card ${idx === activeStepIndex ? 'active-step' : ''}`}
                        onClick={() => setActiveStepIndex(idx)}
                      >
                        <div className="step-number-bubble">{idx + 1}</div>
                        <div>
                          <div className="step-instruction-text">{step.instruction || step.text}</div>
                          <div className="step-floor-sub">{step.floorName}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 5. RL Viva Technical Telemetry Button */}
                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-light)' }}>
                  <button
                    type="button"
                    onClick={onOpenEval}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: '#fbf7ff',
                      border: '1px solid #e9d5ff',
                      color: '#6b21a8',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                    }}
                  >
                    <Cpu size={14} />
                    <span>RL Viva &amp; Technical Model Scorecard</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      <BottomNavigation screen="navigate" go={go} />
    </>
  )
}

// =============================================================================
// 5. AI CONCIERGE & 2-HOUR VISIT PLANNER SCREEN (Tab 4: AI)
// =============================================================================

function AIScreen({
  go,
  onOpenEval,
  initialMode = 'planner',
}: {
  go: Go
  onOpenEval: () => void
  initialMode?: 'chat' | 'planner'
}) {
  const [mode, setMode] = useState<'chat' | 'planner'>(() => {
    if (typeof window !== 'undefined') {
      const m = new URLSearchParams(window.location.search).get('mode')
      if (m === 'chat' || m === 'planner') return m
    }
    return initialMode
  })
  const { data: directoryData } = useSWR('locations', getLocations, swrOptions)
  const stores = directoryData?.stores ?? []

  // 2-Hour Planner state
  const [selectedPreference, setSelectedPreference] = useState<'SHOP' | 'EAT' | 'COFFEE' | 'ENTERTAINMENT' | 'MIXED'>('MIXED')
  const [itinerary, setItinerary] = useState<Array<{ step: string; store: Store; reason: string; label: string }>>([])
  const [isGenerating, setIsGenerating] = useState(false)

  // Chat state
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'assistant'; text: string; stores?: Store[] }>>([
    {
      sender: 'assistant',
      text: 'Good day! I am your Ambience AI Digital Concierge. How may I curate your visit to Ambience Mall Gurugram today?',
    }
  ])
  const [chatInput, setChatInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)

  // Generate 2-Hour Itinerary using real stores and real routes from backend
  const generateItinerary = async (pref = selectedPreference) => {
    setIsGenerating(true)
    const prefActivitiesMap: Record<string, string[]> = {
      SHOP: ['fashion', 'coffee', 'shopping'],
      EAT: ['dining', 'coffee', 'food'],
      COFFEE: ['coffee', 'shopping', 'cafe'],
      ENTERTAINMENT: ['entertainment', 'dining', 'shopping'],
      MIXED: ['coffee', 'shopping', 'dining'],
    }
    const activities = prefActivitiesMap[pref] || ['coffee', 'shopping', 'dining']

    try {
      const res = await fetch('/api/itinerary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activities, duration_hours: 2.0 }),
      })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data.stops) && data.stops.length > 0) {
          const mappedStops = data.stops.map((item: any) => {
            const rawStore = item.store || {}
            const matchedLocal = stores.find(s => s.id === rawStore.id)
            return {
              step: item.step || '01',
              label: item.label || 'EXPERIENCE',
              store: matchedLocal || {
                id: rawStore.id,
                name: rawStore.name,
                floor: rawStore.floor || 'Ground Floor',
                floorId: rawStore.floorId || 0,
                category: rawStore.category || 'Retail',
                x: rawStore.x,
                y: rawStore.y,
              },
              reason: item.reason || 'Curated stop with verified indoor route.',
            }
          })
          setItinerary(mappedStops)
          setIsGenerating(false)
          return
        }
      }
    } catch (err) {
      console.warn('Backend itinerary planner unavailable, using local store mapping:', err)
    }

    // Local fallback using real catalog stores
    let step1: Store | undefined
    let step2: Store | undefined
    let step3: Store | undefined

    const findStore = (names: string[], fallbackCat: string) => {
      for (const name of names) {
        const match = stores.find(s => s.name.toLowerCase().includes(name.toLowerCase()))
        if (match) return match
      }
      return stores.find(s => s.category?.toLowerCase().includes(fallbackCat.toLowerCase())) || stores[0]
    }

    if (pref === 'SHOP') {
      step1 = findStore(['ZARA', 'Marks & Spencer', 'H&M'], 'Fashion')
      step2 = findStore(["Paul's Bakery", 'Barista', 'Blue Tokai'], 'Food & Dining')
      step3 = findStore(['Diesel', 'Lacoste', 'Uniqlo', 'Nike'], 'Fashion')
    } else if (pref === 'EAT') {
      step1 = findStore(['Haldiram', 'Chili', 'Wow! Momo'], 'Food & Dining')
      step2 = findStore(["Paul's Bakery", 'Bateel', 'Gelato'], 'Food & Dining')
      step3 = findStore(['Barista', 'Nespresso'], 'Food & Dining')
    } else if (pref === 'COFFEE') {
      step1 = findStore(["Paul's Bakery", 'Barista'], 'Food & Dining')
      step2 = findStore(['Marks & Spencer', 'Hamleys'], 'Retail')
      step3 = findStore(['Nespresso', 'Bateel'], 'Food & Dining')
    } else if (pref === 'ENTERTAINMENT') {
      step1 = findStore(['Hamleys', 'LEGO'], 'Entertainment')
      step2 = findStore(["Paul's Bakery", 'Wow! Momo'], 'Food & Dining')
      step3 = findStore(['Nike', 'Asics'], 'Fashion')
    } else {
      step1 = findStore(['ZARA', 'Marks & Spencer'], 'Fashion')
      step2 = findStore(["Paul's Bakery", 'Barista'], 'Food & Dining')
      step3 = findStore(['Nike', 'Asics', 'Hamleys'], 'Fashion')
    }

    setItinerary([
      {
        step: '01',
        label: pref === 'EAT' ? 'DINING' : 'SHOPPING',
        store: step1,
        reason: 'Initial flagship experience with verified access from North Main Entry.',
      },
      {
        step: '02',
        label: 'COFFEE & REFRESH',
        store: step2,
        reason: 'Midpoint artisan coffee and refreshment on verified floor route.',
      },
      {
        step: '03',
        label: pref === 'SHOP' ? 'FLAGSHIP FASHION' : 'EXPLORE & LIFESTYLE',
        store: step3,
        reason: 'Curated shopping discovery with escalator connectivity across floors.',
      },
    ])
    setIsGenerating(false)
  }

  // Pre-populate itinerary on initial load
  useEffect(() => {
    if (stores.length > 0 && itinerary.length === 0) {
      generateItinerary()
    }
  }, [stores])

  // Handle Groq Chat Send
  const handleSendChat = async (textToSend?: string) => {
    const query = (textToSend || chatInput).trim()
    if (!query || isChatLoading) return

    const newMsgs = [...messages, { sender: 'user' as const, text: query }]
    setMessages(newMsgs)
    setChatInput('')
    setIsChatLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMsgs.map(m => ({
            role: m.sender === 'user' ? 'user' : 'assistant',
            content: m.text,
          })),
        }),
      })

      if (res.ok) {
        const data = await res.json()
        const suggested: Store[] = Array.isArray(data.suggestedStores)
          ? data.suggestedStores.map((s: any) => {
              return stores.find(ls => ls.name.toLowerCase() === s.toLowerCase() || ls.id === s.id) || {
                id: s,
                name: s,
                floor: 'Ground Floor',
                category: 'Retail',
              }
            })
          : []

        // If an itinerary was returned in the chat response, update the itinerary tab
        if (Array.isArray(data.itinerary) && data.itinerary.length > 0) {
          const mappedStops = data.itinerary.map((item: any) => {
            const rawStore = item.store || {}
            const matchedLocal = stores.find(s => s.id === rawStore.id)
            return {
              step: item.step || '01',
              label: item.label || 'STOP',
              store: matchedLocal || {
                id: rawStore.id,
                name: rawStore.name,
                floor: rawStore.floor || 'Ground Floor',
                floorId: rawStore.floorId || 0,
                category: rawStore.category || 'Retail',
              },
              reason: item.reason || 'Curated stop with verified indoor route.',
            }
          })
          setItinerary(mappedStops)
        }

        setMessages(prev => [
          ...prev,
          {
            sender: 'assistant',
            text: data.reply || "Here's what I curated for you at Ambience Mall Gurugram:",
            stores: suggested,
          },
        ])
      } else {
        throw new Error('API failed')
      }
    } catch {
      // Local fallback search
      const qLower = query.toLowerCase()
      const matched = stores.filter(s => s.name.toLowerCase().includes(qLower)).slice(0, 3)
      setMessages(prev => [
        ...prev,
        {
          sender: 'assistant',
          text: matched.length > 0
            ? `I found ${matched.length} store(s) matching "${query}" at Ambience Mall:`
            : `You can explore our directory of 221 stores across Ground, First and Second floors.`,
          stores: matched,
        },
      ])
    } finally {
      setIsChatLoading(false)
    }
  }

  return (
    <>
      <main className="page ai-page">
        {/* Concierge Hero Banner */}
        <div className="ai-concierge-hero">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '10.5px', fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--gold-accent)' }}>
              AI Digital Concierge
            </span>
            <span style={{ fontSize: '10px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}>
              <span className="status-dot-pulse" style={{ width: 5, height: 5 }} />
              xAI Grok Online
            </span>
          </div>
          <h2>Ambience AI</h2>
          <p>Intelligent visit curation &amp; live mall guidance.</p>
        </div>

        {/* Dual Mode Switcher: 2-Hour Planner vs Concierge Chat */}
        <div className="ai-mode-tabs">
          <button
            type="button"
            className={`ai-mode-tab ${mode === 'planner' ? 'active' : ''}`}
            onClick={() => setMode('planner')}
          >
            <Clock size={14} />
            <span>2-Hour Visit Planner</span>
          </button>
          <button
            type="button"
            className={`ai-mode-tab ${mode === 'chat' ? 'active' : ''}`}
            onClick={() => setMode('chat')}
          >
            <Sparkles size={14} />
            <span>Concierge Chat</span>
          </button>
        </div>

        {/* VIEW 1: 2-HOUR VISIT PLANNER (TIMELINE REDESIGN) */}
        {mode === 'planner' && (
          <div style={{ background: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '18px', boxShadow: 'var(--shadow-subtle)' }}>
            <div style={{ marginBottom: '14px' }}>
              <span style={{ fontSize: '10.5px', fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--gold-accent)' }}>
                Your Perfect Mall Day
              </span>
              <h3 style={{ margin: '2px 0 4px', fontSize: '17px', fontWeight: 800, color: 'var(--text-primary)' }}>
                What are you in the mood for?
              </h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)' }}>
                Select your focus to construct an optimized multi-floor itinerary.
              </p>
            </div>

            {/* Editorial Choice Tiles */}
            <div className="planner-editorial-tiles">
              {[
                { id: 'MIXED', label: 'Curated Blend', sub: 'Fashion + Coffee + Lifestyle', icon: <Sparkles size={16} strokeWidth={1.8} /> },
                { id: 'SHOP', label: 'Fashion & Luxury', sub: 'ZARA, Diesel, Lacoste', icon: <ShoppingBag size={16} strokeWidth={1.8} /> },
                { id: 'COFFEE', label: 'Artisan Coffee', sub: "Paul's Bakery, Barista", icon: <Coffee size={16} strokeWidth={1.8} /> },
                { id: 'EAT', label: 'Dining Experience', sub: 'Fine food & quick bites', icon: <Utensils size={16} strokeWidth={1.8} /> },
                { id: 'ENTERTAINMENT', label: 'Entertainment', sub: 'Hamleys, Leisure', icon: <Film size={16} strokeWidth={1.8} /> },
              ].map(opt => (
                <div
                  key={opt.id}
                  className={`planner-tile-choice ${selectedPreference === opt.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedPreference(opt.id as any)
                    generateItinerary(opt.id as any)
                  }}
                >
                  <div className="planner-tile-icon">{opt.icon}</div>
                  <b>{opt.label}</b>
                  <small>{opt.sub}</small>
                </div>
              ))}
            </div>

            <div className="duration-chip-row" style={{ marginBottom: '14px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>TIME ALLOTTED:</span>
              <span className="duration-pill">2 HOURS</span>
            </div>

            <button
              type="button"
              className="generate-itinerary-btn"
              onClick={() => generateItinerary()}
              disabled={isGenerating}
            >
              <Sparkles size={15} />
              <span>{isGenerating ? 'Curating Experience…' : 'Regenerate Itinerary'}</span>
            </button>

            {/* Timeline Results */}
            {itinerary.length > 0 && (
              <div style={{ marginTop: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-primary)' }}>
                    Your 2-Hour Experience
                  </span>
                  <span style={{ fontSize: '10.5px', color: 'var(--gold-hover)', fontWeight: 700 }}>
                    3 Verified Stops
                  </span>
                </div>

                <div className="timeline-experience-shelf">
                  <div className="timeline-spine-line" />
                  {itinerary.map(item => (
                    <div key={item.step} className="timeline-step-node">
                      <div className="timeline-node-dot">{item.step}</div>
                      <div className="timeline-card-content">
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontSize: '9.5px', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--gold-accent)' }}>
                            {item.label}
                          </span>
                          <span style={{ fontSize: '10.5px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            {item.store.floor || 'Ground Floor'}
                          </span>
                        </div>

                        <div className="timeline-store-row">
                          <StoreLogo store={item.store} size="sm" />
                          <div>
                            <b>{item.store.name}</b>
                            <small>{item.store.category || 'Retail'}</small>
                          </div>
                        </div>

                        <p className="timeline-reason">{item.reason}</p>

                        <button
                          type="button"
                          className="timeline-nav-btn"
                          onClick={() => go('navigate', item.store)}
                        >
                          <Navigation size={12} />
                          <span>Navigate to Stop {item.step}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* VIEW 2: CONCIERGE CHAT (CONVERSATIONAL SUGGESTION CARDS) */}
        {mode === 'chat' && (
          <div className="concierge-chat-wrap" style={{ height: 'calc(100vh - 290px)', minHeight: '380px', marginBottom: '16px' }}>
            <div className="chat-messages-scroll">
              {/* Conversational Suggestion Prompt Cards */}
              <div className="conversational-prompt-cards">
                <span style={{ fontSize: '10.5px', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--gold-accent)' }}>
                  Concierge Inquiries
                </span>
                {[
                  'Plan a 2-hour shopping and coffee visit.',
                  'Find the best specialty coffee nearby.',
                  'Where is ZARA located?',
                  'Where can I find running shoes & sports apparel?',
                  'Where is the nearest basement parking lobby?',
                ].map(prompt => (
                  <button
                    key={prompt}
                    type="button"
                    className="suggestion-card-btn"
                    onClick={() => handleSendChat(prompt)}
                  >
                    <span>{prompt}</span>
                    <ArrowRight size={13} color="#a6824e" />
                  </button>
                ))}
              </div>

              {/* Chat Message History */}
              {messages.map((m, i) => (
                <div key={i} className={`chat-bubble ${m.sender}`}>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
                  {m.stores && m.stores.length > 0 && (
                    <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {m.stores.map(s => (
                        <div
                          key={s.id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '6px 10px',
                            background: '#ffffff',
                            borderRadius: '6px',
                            border: '1px solid var(--border-light)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <StoreLogo store={s} size="xs" />
                            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>{s.name}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => go('navigate', s)}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '3px',
                              background: 'var(--text-primary)',
                              color: '#ffffff',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '3px 8px',
                              fontSize: '11px',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            <Navigation size={10} />
                            <span>Navigate</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {isChatLoading && (
                <div className="chat-bubble assistant">
                  <span>Curating recommendations with xAI Grok…</span>
                </div>
              )}
            </div>

            {/* Assistant Input Bar */}
            <form
              className="chat-input-bar"
              onSubmit={e => {
                e.preventDefault()
                handleSendChat()
              }}
            >
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask Ambience Concierge anything…"
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={!chatInput.trim() || isChatLoading}
                aria-label="Send message"
              >
                <Send size={14} />
              </button>
            </form>
          </div>
        )}
      </main>
      <BottomNavigation screen="ai" go={go} />
    </>
  )
}

// =============================================================================
// MAIN APPLICATION ROOT
// =============================================================================

export default function MallApp() {
  const [screen, setScreen] = useState<Screen>('home')
  const [activeStore, setActiveStore] = useState<Store | undefined>({
    id: 'G_005',
    name: 'ZARA',
    category: 'Fashion',
    floor: 'Ground Floor',
    floorId: 0,
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [favorites, setFavorites] = useState<string[]>([])
  const [customStartId, setCustomStartId] = useState<string>('G_GATE_1')

  // Modals state
  const [isFacilitiesModalOpen, setIsFacilitiesModalOpen] = useState(false)
  const [isParkingModalOpen, setIsParkingModalOpen] = useState(false)
  const [isEvalModalOpen, setIsEvalModalOpen] = useState(false)

  // Current active route object for AcademicEvalModal
  const { data: currentRoute } = useSWR(
    activeStore ? ['route', activeStore.id, customStartId] : null,
    () => getRoute(activeStore!.id, { startId: customStartId }),
    swrOptions
  )

  const { data: directory } = useSWR('locations', getLocations, swrOptions)
  const allStores = directory?.stores ?? []

  // URL query parameter synchronization on client mount
  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    const tabParam = params.get('tab') as Screen | null
    const storeParam = params.get('store')
    const modalParam = params.get('modal')

    if (tabParam && ['home', 'explore', 'navigate', 'ai', 'detail'].includes(tabParam)) {
      setScreen(tabParam)
    }

    if (storeParam && allStores.length > 0) {
      const match = allStores.find(
        s => s.id === storeParam || s.name.toLowerCase() === storeParam.toLowerCase()
      )
      if (match) setActiveStore(match)
    }

    const fromParam = params.get('from') || params.get('start')
    if (fromParam) setCustomStartId(fromParam)

    if (modalParam === 'facilities') setIsFacilitiesModalOpen(true)
    if (modalParam === 'parking') setIsParkingModalOpen(true)
    if (modalParam === 'eval' || modalParam === 'viva') setIsEvalModalOpen(true)
  }, [allStores])

  // Load favorites from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('ambience_mall_favorites')
      if (saved) setFavorites(JSON.parse(saved))
    } catch {
      // ignore
    }
  }, [])

  const toggleFavorite = (id: string) => {
    setFavorites(prev => {
      const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
      try {
        localStorage.setItem('ambience_mall_favorites', JSON.stringify(next))
      } catch {
        // ignore
      }
      return next
    })
  }

  const go: Go = (nextScreen, store, query) => {
    if (store) setActiveStore(store)
    if (typeof query === 'string') setSearchQuery(query)
    setScreen(nextScreen)
    window.scrollTo(0, 0)

    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      url.searchParams.set('tab', nextScreen)
      if (store) url.searchParams.set('store', store.id)
      else url.searchParams.delete('store')
      window.history.replaceState(null, '', url.toString())
    }
  }

  const handleStartParkingNav = (parkingNodeId: string, store: Store) => {
    setCustomStartId(parkingNodeId)
    setActiveStore(store)
    setScreen('navigate')
  }

  const handleNavigateToFacility = (facilityStore: Store) => {
    setActiveStore(facilityStore)
    setScreen('navigate')
  }

  return (
    <div className="app-shell">
      {screen === 'home' && (
        <Home
          go={go}
          onOpenFacilities={() => setIsFacilitiesModalOpen(true)}
          onOpenEval={() => setIsEvalModalOpen(true)}
          onOpenPlanner={() => setScreen('ai')}
        />
      )}
      {screen === 'explore' && (
        <Explore
          go={go}
          favorites={favorites}
          toggleFavorite={toggleFavorite}
          initialQuery={searchQuery}
          onOpenEval={() => setIsEvalModalOpen(true)}
        />
      )}
      {screen === 'detail' && activeStore && (
        <Detail
          store={activeStore}
          go={go}
          favorite={favorites.includes(activeStore.id)}
          toggleFavorite={() => toggleFavorite(activeStore.id)}
          onOpenEval={() => setIsEvalModalOpen(true)}
        />
      )}
      {screen === 'navigate' && (
        <Navigate
          store={activeStore}
          go={go}
          initialStartId={customStartId}
          onOpenEval={() => setIsEvalModalOpen(true)}
        />
      )}
      {screen === 'ai' && (
        <AIScreen
          go={go}
          onOpenEval={() => setIsEvalModalOpen(true)}
        />
      )}

      {/* Smart Facility & Service Modals */}
      <FacilitiesModal
        isOpen={isFacilitiesModalOpen}
        onClose={() => setIsFacilitiesModalOpen(false)}
        onNavigateToFacility={handleNavigateToFacility}
      />

      <ParkingModal
        isOpen={isParkingModalOpen}
        onClose={() => setIsParkingModalOpen(false)}
        stores={allStores}
        onStartParkingNavigation={handleStartParkingNav}
      />

      <AcademicEvalModal
        isOpen={isEvalModalOpen}
        onClose={() => setIsEvalModalOpen(false)}
        route={currentRoute}
      />
    </div>
  )
}
