'use client'

import React, { useState } from 'react'
import { Store } from 'lucide-react'
import { getStoreLogo, type StoreLogoResult } from '@/lib/store-logo-map'

export interface StoreLogoProps {
  store: {
    name: string
    category?: string
    image?: string
    id?: string
  }
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number
  className?: string
  rounded?: boolean
  showIcon?: boolean
}

export default function StoreLogo({
  store,
  size = 'md',
  className = '',
  rounded = false,
}: StoreLogoProps) {
  const [imgError, setImgError] = useState(false)
  const logoInfo: StoreLogoResult = getStoreLogo(store)

  const sizePx =
    typeof size === 'number'
      ? size
      : size === 'xs'
      ? 24
      : size === 'sm'
      ? 36
      : size === 'md'
      ? 48
      : size === 'lg'
      ? 92
      : 120

  const borderRadius = rounded
    ? '50%'
    : sizePx <= 28
    ? '6px'
    : sizePx <= 48
    ? '10px'
    : sizePx <= 92
    ? '16px'
    : '20px'

  // Proportional padding so logos have breathing room and don't touch container borders
  const paddingPx =
    sizePx <= 24
      ? 3
      : sizePx <= 36
      ? 5
      : sizePx <= 48
      ? 8
      : sizePx <= 92
      ? 14
      : 18

  const iconSize = Math.max(14, Math.round(sizePx * 0.38))

  // 1. Official Verified Brand Logo
  if (logoInfo.hasLogo && logoInfo.logoUrl && !imgError) {
    return (
      <div
        className={`store-logo-wrapper ${className}`}
        style={{
          width: sizePx,
          height: sizePx,
          borderRadius,
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#FFFFFF',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow:
            sizePx >= 48
              ? '0 2px 10px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04)'
              : '0 1px 4px rgba(0, 0, 0, 0.05)',
          flexShrink: 0,
          boxSizing: 'border-box',
          position: 'relative',
        }}
        title={logoInfo.brandName || store?.name}
      >
        <img
          src={logoInfo.logoUrl}
          alt={`${logoInfo.brandName || store?.name} logo`}
          onError={() => setImgError(true)}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            width: 'auto',
            height: 'auto',
            objectFit: 'contain',
            padding: `${paddingPx}px`,
            display: 'block',
          }}
        />
      </div>
    )
  }

  // 2. Clean Neutral Fallback for unverified stores / OCR fragments
  const storeDisplayName = store?.name?.trim() || 'Store'
  const fallbackLetter = storeDisplayName.charAt(0).toUpperCase()

  return (
    <div
      className={`store-logo-fallback ${className}`}
      role="img"
      aria-label={`${storeDisplayName} store`}
      title={storeDisplayName}
      style={{
        width: sizePx,
        height: sizePx,
        borderRadius,
        backgroundColor: '#F3F4F6',
        border: '1px solid rgba(0, 0, 0, 0.08)',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#6B7280',
        flexShrink: 0,
        boxSizing: 'border-box',
        userSelect: 'none',
        position: 'relative',
      }}
    >
      {sizePx >= 48 ? (
        <>
          <Store size={iconSize} strokeWidth={1.8} style={{ color: '#4B5563' }} />
          {sizePx >= 92 && (
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                marginTop: '6px',
                color: '#6B7280',
                maxWidth: '85%',
                textAlign: 'center',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {storeDisplayName}
            </span>
          )}
        </>
      ) : (
        <span
          style={{
            fontSize: `${Math.max(10, Math.round(sizePx * 0.42))}px`,
            fontWeight: 700,
            lineHeight: 1,
            color: '#4B5563',
          }}
        >
          {fallbackLetter}
        </span>
      )}
    </div>
  )
}
