'use client'

import React, { useState, useRef, useEffect } from 'react'
import {
  Sparkles,
  Send,
  Mic,
  MicOff,
  Navigation,
  X,
  Phone,
  Car,
  Layers,
  RotateCcw,
} from 'lucide-react'
import { type Store } from '@/lib/api'
import StoreLogo from '@/components/store-logo'

interface AIAssistantProps {
  isOpen: boolean
  onClose: () => void
  stores: Store[]
  onNavigate: (store: Store) => void
  onSelectStore: (store: Store) => void
  onOpenParking?: () => void
  onOpenFacilities?: () => void
}

interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  text: string
  suggestedStores?: Store[]
  navigationTarget?: Store | null
  action?: 'navigate' | 'call_concierge' | 'parking' | 'facilities' | null
}

// Markdown renderer helper
function FormattedText({ text }: { text: string }) {
  // Split lines
  const lines = text.split('\n')

  return (
    <div className="ai-markdown-content">
      {lines.map((line, idx) => {
        const trimmed = line.trim()
        if (!trimmed) return <div key={idx} style={{ height: 6 }} />

        // Headings
        if (trimmed.startsWith('### ')) {
          return <h4 key={idx}>{parseInlineFormatting(trimmed.slice(4))}</h4>
        }
        if (trimmed.startsWith('## ')) {
          return <h3 key={idx}>{parseInlineFormatting(trimmed.slice(3))}</h3>
        }

        // Bullet points
        if (trimmed.startsWith('• ') || trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
          return (
            <div key={idx} style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
              <span style={{ color: '#ed1b2f', fontWeight: 'bold' }}>•</span>
              <div>{parseInlineFormatting(trimmed.replace(/^([•*-]\s*)/, ''))}</div>
            </div>
          )
        }

        // Regular line
        return <p key={idx}>{parseInlineFormatting(line)}</p>
      })}
    </div>
  )
}

function parseInlineFormatting(str: string) {
  // Parse **bold** and *italic*
  const parts = str.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} style={{ color: '#0f172a', fontWeight: 600 }}>
          {part.slice(2, -2)}
        </strong>
      )
    }
    return part
  })
}

const INITIAL_WELCOME: ChatMessage = {
  id: 'welcome',
  sender: 'assistant',
  text: 'Hello! I am your **Ambience AI Concierge**, powered by xAI Grok intelligence. Ask me anything like *"Find running shoes and coffee"*, *"Where is ZARA?"*, *"Plan a 2-hour itinerary"*, or *"Where should I park?"*',
}

export default function AIAssistantModal({
  isOpen,
  onClose,
  stores,
  onNavigate,
  onSelectStore,
  onOpenParking,
  onOpenFacilities,
}: AIAssistantProps) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_WELCOME])
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) {
      setTimeout(scrollToBottom, 50)
    }
  }, [isOpen, messages, isLoading])

  const handleClearChat = () => {
    setMessages([INITIAL_WELCOME])
  }

  const handleSend = async (customQuery?: string) => {
    const query = (customQuery !== undefined ? customQuery : input).trim()
    if (!query || isLoading) return

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: query,
    }

    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setInput('')
    setIsLoading(true)

    try {
      // Call our Next.js API route backed by Groq LLM
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedMessages.map(m => ({
            role: m.sender === 'user' ? 'user' : 'assistant',
            content: m.text,
          })),
        }),
      })

      if (!res.ok) {
        throw new Error(`Chat API error: ${res.status}`)
      }

      const data = await res.json()

      // Convert returned store items to the component Store interface
      const suggested: Store[] = Array.isArray(data.suggestedStores)
        ? data.suggestedStores.map((s: any) => {
            const matchedLocal = stores.find(ls => ls.id === s.id || ls.name.toLowerCase() === s.name?.toLowerCase())
            return (
              matchedLocal || {
                id: s.id,
                name: s.name,
                category: s.category || 'Retail',
                floor: s.floor_name || (s.floor === 0 ? 'Ground Floor' : s.floor === 1 ? 'First Floor' : 'Second Floor'),
                floorId: typeof s.floor === 'number' ? s.floor : 0,
                x: s.x || 500,
                y: s.y || 500,
                status: 'verified',
              }
            )
          })
        : []

      let targetStore: Store | null = null
      if (data.navigationTarget) {
        targetStore =
          stores.find(
            ls =>
              ls.id === data.navigationTarget.id ||
              ls.name.toLowerCase() === data.navigationTarget.name?.toLowerCase()
          ) || null
      }

      setMessages(prev => [
        ...prev,
        {
          id: String(Date.now() + 1),
          sender: 'assistant',
          text: data.reply || "Here's what I found for you in Ambience Mall:",
          suggestedStores: suggested,
          navigationTarget: targetStore,
          action: data.action,
        },
      ])
    } catch (err: any) {
      console.warn('Groq chat error, falling back to local search:', err)

      // Fallback local heuristic
      const qLower = query.toLowerCase()
      const matched = stores
        .filter(s => s.name.toLowerCase().includes(qLower) || (s.category && s.category.toLowerCase().includes(qLower)))
        .slice(0, 4)

      setMessages(prev => [
        ...prev,
        {
          id: String(Date.now() + 1),
          sender: 'assistant',
          text:
            matched.length > 0
              ? `I found ${matched.length} store(s) matching "${query}" in Ambience Mall:`
              : `I couldn't find an exact store for "${query}". You can browse our directory of 221 stores or ask about categories like coffee, sneakers, or electronics.`,
          suggestedStores: matched,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const toggleVoice = () => {
    if (typeof window === 'undefined') return
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert('Voice search is not supported by your browser. Please type your query!')
      return
    }

    if (isListening) {
      setIsListening(false)
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-IN'

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        setInput(transcript)
        setIsListening(false)
        handleSend(transcript)
      }

      recognition.onerror = () => {
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognition.start()
    } catch {
      setIsListening(false)
    }
  }

  const quickPrompts = [
    '⚡ Plan 2-hr visit',
    '☕ Best coffee & food',
    '👟 Sneaker stores',
    '💻 Laptops & electronics',
    '👑 Luxury brands on GF',
    '🚗 Where to park?',
  ]

  if (!isOpen) return null

  return (
    <div className="ai-modal-backdrop" onClick={onClose}>
      <div className="ai-modal-sheet" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="ai-modal-header">
          <div className="ai-modal-title">
            <div className="ai-icon-bubble">
              <Sparkles size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <h3>Ask Ambience AI</h3>
                <span
                  style={{
                    fontSize: 9,
                    fontWeight: 700,
                    background: '#fee2e2',
                    color: '#b91c1c',
                    padding: '1px 6px',
                    borderRadius: 10,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  xAI Grok
                </span>
              </div>
              <small>Real-time Mall Concierge · 221 Stores</small>
            </div>
          </div>
          <div className="ai-header-actions">
            <button
              type="button"
              className="ai-header-btn"
              onClick={handleClearChat}
              title="Reset conversation"
              aria-label="Reset conversation"
            >
              <RotateCcw size={15} />
            </button>
            <button
              type="button"
              className="ai-close-btn"
              onClick={onClose}
              aria-label="Close assistant"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Quick Prompts Bar */}
        <div className="ai-quick-prompts">
          {quickPrompts.map(qp => (
            <button
              key={qp}
              type="button"
              className="ai-quick-chip"
              onClick={() => handleSend(qp.replace(/^[^\s]+\s/, ''))}
            >
              {qp}
            </button>
          ))}
        </div>

        {/* Message Thread */}
        <div className="ai-chat-thread">
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`ai-message-row ${msg.sender === 'user' ? 'user-row' : 'assistant-row'}`}
            >
              <div className={`ai-bubble ${msg.sender === 'user' ? 'user-bubble' : 'assistant-bubble'}`}>
                <FormattedText text={msg.text} />

                {/* Primary Action Banner */}
                {msg.action === 'navigate' && msg.navigationTarget && (
                  <div className="ai-action-banner">
                    <div className="ai-action-info">
                      <Navigation size={16} color="#ed1b2f" />
                      <span>Ready to guide you to <b>{msg.navigationTarget.name}</b></span>
                    </div>
                    <button
                      type="button"
                      className="ai-action-btn"
                      onClick={() => {
                        if (msg.navigationTarget) {
                          onNavigate(msg.navigationTarget)
                          onClose()
                        }
                      }}
                    >
                      Start Route
                    </button>
                  </div>
                )}

                {msg.action === 'call_concierge' && (
                  <div className="ai-action-banner">
                    <div className="ai-action-info">
                      <Phone size={16} color="#ed1b2f" />
                      <span>Official Ambience Helpline</span>
                    </div>
                    <a
                      href="tel:+918860800800"
                      className="ai-action-btn"
                      style={{ textDecoration: 'none' }}
                    >
                      Call +91 88608 00800
                    </a>
                  </div>
                )}

                {msg.action === 'parking' && onOpenParking && (
                  <div className="ai-action-banner">
                    <div className="ai-action-info">
                      <Car size={16} color="#ed1b2f" />
                      <span>Find your car or vehicle entrance</span>
                    </div>
                    <button
                      type="button"
                      className="ai-action-btn"
                      onClick={() => {
                        onOpenParking()
                        onClose()
                      }}
                    >
                      Open Parking
                    </button>
                  </div>
                )}

                {msg.action === 'facilities' && onOpenFacilities && (
                  <div className="ai-action-banner">
                    <div className="ai-action-info">
                      <Layers size={16} color="#ed1b2f" />
                      <span>Restrooms, Lifts, Escalators</span>
                    </div>
                    <button
                      type="button"
                      className="ai-action-btn"
                      onClick={() => {
                        onOpenFacilities()
                        onClose()
                      }}
                    >
                      View Facilities
                    </button>
                  </div>
                )}

                {/* Suggested Store Cards */}
                {msg.suggestedStores && msg.suggestedStores.length > 0 && (
                  <div className="ai-store-suggestions">
                    {msg.suggestedStores.map(store => (
                      <div key={store.id} className="ai-suggestion-card">
                        <StoreLogo store={store} size="sm" />
                        <div className="ai-sug-info" style={{ flex: 1, minWidth: 0 }}>
                          <b>{store.name}</b>
                          <div className="ai-sug-meta">
                            <span>{store.floor || 'Ground Floor'}</span>
                            <span>•</span>
                            <span>{store.category || 'Retail'}</span>
                          </div>
                        </div>
                        <div className="ai-sug-actions">
                          <button
                            type="button"
                            className="ai-view-btn"
                            onClick={() => {
                              onSelectStore(store)
                              onClose()
                            }}
                          >
                            Details
                          </button>
                          <button
                            type="button"
                            className="ai-nav-btn"
                            onClick={() => {
                              onNavigate(store)
                              onClose()
                            }}
                          >
                            <Navigation size={12} />
                            <span>Navigate</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="ai-message-row assistant-row">
              <div className="ai-typing-row">
                <div className="ai-typing-dots">
                  <div className="ai-typing-dot" />
                  <div className="ai-typing-dot" />
                  <div className="ai-typing-dot" />
                </div>
                <span className="ai-typing-text">Ambience AI is thinking…</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="ai-input-bar">
          <button
            type="button"
            className={`ai-mic-btn ${isListening ? 'listening' : ''}`}
            onClick={toggleVoice}
            aria-label="Voice search"
            title={isListening ? 'Listening…' : 'Tap to speak'}
          >
            {isListening ? <MicOff size={18} color="#ef4444" /> : <Mic size={18} color="#64748b" />}
          </button>
          <input
            type="text"
            className="ai-text-input"
            placeholder={isListening ? 'Listening…' : 'Ask anything (e.g. Find coffee, where is ZARA)…'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') handleSend()
            }}
            disabled={isLoading}
          />
          <button
            type="button"
            className="ai-send-btn"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            aria-label="Send query"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
