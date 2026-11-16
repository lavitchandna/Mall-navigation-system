'use client'

import React, { useState } from 'react'
import { Mic, MicOff } from 'lucide-react'

interface VoiceSearchButtonProps {
  onResult: (transcript: string) => void
  className?: string
}

export default function VoiceSearchButton({ onResult, className = '' }: VoiceSearchButtonProps) {
  const [listening, setListening] = useState(false)

  const handleToggle = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (typeof window === 'undefined') return
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert('Voice recognition is not supported in this browser. Please use the text search bar.')
      return
    }

    if (listening) {
      setListening(false)
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-IN'

      recognition.onstart = () => {
        setListening(true)
      }

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        setListening(false)
        if (transcript) {
          onResult(transcript)
        }
      }

      recognition.onerror = () => {
        setListening(false)
      }

      recognition.onend = () => {
        setListening(false)
      }

      recognition.start()
    } catch {
      setListening(false)
    }
  }

  return (
    <button
      type="button"
      className={`voice-search-trigger ${listening ? 'listening' : ''} ${className}`}
      onClick={handleToggle}
      aria-label={listening ? 'Listening to voice...' : 'Search by voice'}
      title={listening ? 'Listening…' : 'Tap to speak'}
    >
      {listening ? <MicOff size={18} color="#ef4444" /> : <Mic size={18} color="#64748b" />}
    </button>
  )
}
