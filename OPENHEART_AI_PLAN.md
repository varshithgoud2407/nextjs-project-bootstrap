# OpenHeart AI Voice Companion - Implementation Plan

## Overview
OpenHeart now features an AI-powered voice companion that provides emotional support through real-time voice conversations in multiple languages via Zoom/Google Meet integration.

## Core Changes from Original Plan

### 1. Remove Human Matchmaking & Booking
- ❌ Remove: Tinder-like swipe interface
- ❌ Remove: 24-hour advance booking system
- ❌ Remove: Human listener profiles
- ✅ Add: Direct AI companion access
- ✅ Add: Instant voice session initiation

### 2. AI Voice Integration Features
- **Real-time Voice Processing**: AI listens and responds during video calls
- **Language Detection**: Automatically detects user's language
- **Multilingual Response**: AI responds in the detected language
- **Emotional Intelligence**: AI provides empathetic, supportive responses
- **Video Call Integration**: Works with Zoom/Google Meet APIs

## Updated Project Structure

### Backend Directory Structure
```
/backend
  ├── main.py                    # FastAPI entry point
  ├── config.py                  # App configuration
  ├── database.py                # Database connection
  ├── models.py                  # User, Session, Payment models
  ├── dependencies.py            # Auth dependencies
  ├── exceptions.py              # Error handling
  ├── utils.py                   # JWT and utilities
  ├── ai_services/               # AI integration services
  │   ├── __init__.py
  │   ├── voice_processor.py     # Voice-to-text and text-to-voice
  │   ├── language_detector.py   # Language detection service
  │   ├── ai_companion.py        # Main AI conversation logic
  │   └── meeting_integration.py # Zoom/Google Meet API integration
  └── routes/
      ├── auth.py                # Authentication endpoints
      ├── users.py               # User profile management
      ├── ai_sessions.py         # AI conversation sessions
      ├── payments.py            # Payment processing
      └── meetings.py            # Video call management
```

### Frontend Structure Updates
```
/src
  ├── app/
  │   ├── page.tsx               # Landing page
  │   ├── layout.tsx             # Root layout
  │   ├── login/page.tsx         # Authentication
  │   ├── register/page.tsx      # User registration
  │   ├── dashboard/page.tsx     # User dashboard
  │   ├── ai-companion/page.tsx  # AI companion interface
  │   ├── meeting/page.tsx       # Video call interface
  │   └── payment/page.tsx       # Subscription management
  ├── components/
  │   ├── ui/                    # Existing shadcn components
  │   └── openheart/             # Custom components
  │       ├── AICompanion.tsx    # AI chat interface
  │       ├── VoiceControls.tsx  # Voice session controls
  │       ├── LanguageSelector.tsx # Language preference
  │       ├── MeetingRoom.tsx    # Video call component
  │       └── PaymentPlans.tsx   # Subscription plans
  ├── hooks/
  │   ├── useAuth.ts             # Authentication hook
  │   ├── useAISession.ts        # AI session management
  │   └── useVoiceCall.ts        # Voice call management
  └── lib/
      ├── api.ts                 # API client
      ├── meeting-sdk.ts         # Zoom/Meet SDK wrapper
      └── utils.ts               # Utilities
```

## Technical Implementation Details

### 1. AI Services Integration

#### Voice Processing Service (`ai_services/voice_processor.py`)
```python
import openai
import speech_recognition as sr
from gtts import gTTS
import io
import base64

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    async def speech_to_text(self, audio_data: bytes, language: str = "auto") -> str:
        """Convert speech to text using OpenAI Whisper or Google Speech API"""
        # Implementation for converting audio to text
        pass
        
    async def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """Convert text to speech in specified language"""
        # Implementation for converting text to audio
        pass
```

#### Language Detection (`ai_services/language_detector.py`)
```python
from langdetect import detect
import pycountry

class LanguageDetector:
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'de': 'German', 
            'es': 'Spanish',
            'fr': 'French',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese'
        }
    
    def detect_language(self, text: str) -> str:
        """Detect language from text input"""
        try:
            detected = detect(text)
            return detected if detected in self.supported_languages else 'en'
        except:
            return 'en'  # Default to English
```

#### AI Companion (`ai_services/ai_companion.py`)
```python
import openai
from typing import Dict, List

class AICompanion:
    def __init__(self):
        self.conversation_history: Dict[str, List] = {}
        
    async def generate_response(self, user_message: str, language: str, user_id: str) -> str:
        """Generate empathetic AI response in user's language"""
        
        # Get conversation history
        history = self.conversation_history.get(user_id, [])
        
        # Create system prompt based on language
        system_prompt = self.get_system_prompt(language)
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message}
        ]
        
        # Get AI response
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Update conversation history
        history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ])
        self.conversation_history[user_id] = history[-10:]  # Keep last 10 exchanges
        
        return ai_response
    
    def get_system_prompt(self, language: str) -> str:
        """Get system prompt in specified language"""
        prompts = {
            'en': "You are a compassionate AI companion providing emotional support. Listen actively and respond with empathy.",
            'de': "Du bist ein mitfühlender KI-Begleiter, der emotionale Unterstützung bietet. Höre aktiv zu und antworte mit Empathie.",
            'es': "Eres un compañero de IA compasivo que brinda apoyo emocional. Escucha activamente y responde con empatía.",
            'fr': "Vous êtes un compagnon IA compatissant offrant un soutien émotionnel. Écoutez activement et répondez avec empathie.",
            # Add more languages...
        }
        return prompts.get(language, prompts['en'])
```

#### Meeting Integration (`ai_services/meeting_integration.py`)
```python
import asyncio
import websockets
from zoom_sdk import ZoomSDK
from google_meet_api import GoogleMeetAPI

class MeetingIntegration:
    def __init__(self):
        self.zoom_sdk = ZoomSDK()
        self.meet_api = GoogleMeetAPI()
        
    async def create_zoom_meeting(self, user_id: str) -> dict:
        """Create a Zoom meeting for AI session"""
        meeting_config = {
            "topic": "OpenHeart AI Companion Session",
            "type": 1,  # Instant meeting
            "settings": {
                "host_video": False,
                "participant_video": True,
                "audio": "both",
                "auto_recording": "none"
            }
        }
        return await self.zoom_sdk.create_meeting(meeting_config)
    
    async def join_meeting_as_bot(self, meeting_id: str, user_id: str):
        """Join meeting as AI bot to listen and respond"""
        # Implementation for bot joining meeting
        pass
```

### 2. Frontend Implementation

#### AI Companion Interface (`components/openheart/AICompanion.tsx`)
```typescript
'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useAISession } from '@/hooks/useAISession'
import { useVoiceCall } from '@/hooks/useVoiceCall'

export default function AICompanion() {
  const [isListening, setIsListening] = useState(false)
  const [currentLanguage, setCurrentLanguage] = useState('en')
  const { startSession, sendMessage, messages } = useAISession()
  const { startVoiceCall, isCallActive } = useVoiceCall()

  const handleStartVoiceSession = async () => {
    try {
      await startVoiceCall()
      await startSession()
      setIsListening(true)
    } catch (error) {
      console.error('Failed to start voice session:', error)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card className="p-8 text-center">
        <h1 className="text-3xl font-bold mb-4">Your AI Companion</h1>
        <p className="text-muted-foreground mb-6">
          Start a voice conversation with your multilingual AI companion
        </p>
        
        <div className="space-y-4">
          <Button 
            onClick={handleStartVoiceSession}
            size="lg"
            className="w-full max-w-md"
            disabled={isCallActive}
          >
            {isCallActive ? 'Session Active' : 'Start Voice Session'}
          </Button>
          
          {isCallActive && (
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-green-800">
                🎤 AI is listening... Speak in any language
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Chat History */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Conversation</h2>
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-50 ml-8' 
                  : 'bg-gray-50 mr-8'
              }`}
            >
              <p className="text-sm font-medium mb-1">
                {message.role === 'user' ? 'You' : 'AI Companion'}
              </p>
              <p>{message.content}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
```

#### Voice Call Hook (`hooks/useVoiceCall.ts`)
```typescript
import { useState, useCallback } from 'react'
import { meetingSDK } from '@/lib/meeting-sdk'

export function useVoiceCall() {
  const [isCallActive, setIsCallActive] = useState(false)
  const [meetingId, setMeetingId] = useState<string | null>(null)

  const startVoiceCall = useCallback(async () => {
    try {
      // Create meeting room
      const meeting = await meetingSDK.createMeeting({
        type: 'ai-companion',
        audio: true,
        video: true
      })
      
      setMeetingId(meeting.id)
      setIsCallActive(true)
      
      // Join meeting
      await meetingSDK.joinMeeting(meeting.id)
      
      return meeting
    } catch (error) {
      console.error('Failed to start voice call:', error)
      throw error
    }
  }, [])

  const endVoiceCall = useCallback(async () => {
    if (meetingId) {
      await meetingSDK.leaveMeeting(meetingId)
      setIsCallActive(false)
      setMeetingId(null)
    }
  }, [meetingId])

  return {
    isCallActive,
    meetingId,
    startVoiceCall,
    endVoiceCall
  }
}
```

### 3. API Endpoints

#### AI Sessions Route (`routes/ai_sessions.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from ai_services.ai_companion import AICompanion
from ai_services.language_detector import LanguageDetector
from ai_services.voice_processor import VoiceProcessor

router = APIRouter()
ai_companion = AICompanion()
language_detector = LanguageDetector()
voice_processor = VoiceProcessor()

@router.post("/start-session")
async def start_ai_session(user_id: str = Depends(get_current_user)):
    """Start a new AI companion session"""
    # Initialize session
    return {"session_id": f"session_{user_id}_{int(time.time())}"}

@router.post("/voice-message")
async def process_voice_message(
    audio_data: str,  # Base64 encoded audio
    user_id: str = Depends(get_current_user)
):
    """Process voice message and return AI response"""
    try:
        # Convert audio to text
        audio_bytes = base64.b64decode(audio_data)
        user_text = await voice_processor.speech_to_text(audio_bytes)
        
        # Detect language
        language = language_detector.detect_language(user_text)
        
        # Generate AI response
        ai_response = await ai_companion.generate_response(
            user_text, language, user_id
        )
        
        # Convert response to speech
        response_audio = await voice_processor.text_to_speech(
            ai_response, language
        )
        
        return {
            "user_message": user_text,
            "ai_response": ai_response,
            "language": language,
            "response_audio": base64.b64encode(response_audio).decode()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Payment Integration Updates

#### Updated Payment Plans
```python
PAYMENT_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "features": [
            "30 minutes AI conversation per week",
            "Text-based chat only",
            "Basic emotional support"
        ]
    },
    "premium": {
        "name": "Premium",
        "price": 9.99,
        "features": [
            "Unlimited AI voice conversations",
            "All languages supported",
            "Video call integration",
            "Advanced emotional intelligence",
            "Priority support"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 29.99,
        "features": [
            "Everything in Premium",
            "Custom AI personality",
            "Integration with corporate wellness",
            "Analytics and reporting",
            "24/7 priority support"
        ]
    }
}
```

## Environment Variables Required

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost/openheart
JWT_SECRET=your-jwt-secret-key
OPENAI_API_KEY=your-openai-api-key
ZOOM_API_KEY=your-zoom-api-key
ZOOM_API_SECRET=your-zoom-api-secret
GOOGLE_MEET_API_KEY=your-google-meet-api-key
STRIPE_API_KEY=your-stripe-api-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ZOOM_SDK_KEY=your-zoom-sdk-key
NEXT_PUBLIC_GOOGLE_MEET_CLIENT_ID=your-google-meet-client-id
```

## Deployment Considerations

1. **Real-time Audio Processing**: Requires WebRTC or WebSocket connections
2. **AI API Costs**: Monitor OpenAI API usage for cost optimization
3. **Meeting SDK Integration**: Proper Zoom/Google Meet SDK setup
4. **Language Models**: Consider using specialized multilingual models
5. **Scalability**: Implement proper session management for concurrent users

## Security & Privacy

1. **Audio Data**: Encrypt audio data in transit and at rest
2. **Conversation Logs**: Implement data retention policies
3. **Language Detection**: Ensure privacy in language processing
4. **Meeting Security**: Secure meeting room creation and access
5. **GDPR Compliance**: Handle multilingual privacy requirements

This updated plan transforms OpenHeart into an AI-powered voice companion that provides instant, multilingual emotional support through integrated video calling platforms.
