from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import base64
import json
import logging
from datetime import datetime

from database import get_db
from models import User, AISession, SessionMessage, UserProfile
from dependencies import get_current_active_user, get_premium_user
from ai_services.ai_companion import AICompanion
from ai_services.language_detector import LanguageDetector
from ai_services.voice_processor import VoiceProcessor
from ai_services.meeting_integration import MeetingIntegration
from utils import generate_session_id
from exceptions import AIServiceException, VoiceProcessingException

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize AI services
ai_companion = AICompanion()
language_detector = LanguageDetector()
voice_processor = VoiceProcessor()
meeting_integration = MeetingIntegration()

# Pydantic models
class SessionCreate(BaseModel):
    preferred_language: Optional[str] = None
    meeting_platform: str = "webrtc"  # webrtc, zoom, google_meet

class SessionResponse(BaseModel):
    id: int
    session_id: str
    language: str
    status: str
    meeting_id: Optional[str]
    meeting_platform: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str
    audio_data: Optional[str] = None  # Base64 encoded audio

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    language: str
    audio_duration: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class VoiceMessageResponse(BaseModel):
    user_message: str
    ai_response: str
    language: str
    response_audio: Optional[str] = None  # Base64 encoded audio
    session_id: str

@router.post("/start-session", response_model=SessionResponse)
async def start_ai_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a new AI companion session"""
    try:
        # Generate unique session ID
        session_id = generate_session_id(current_user.id)
        
        # Determine language
        language = session_data.preferred_language or current_user.preferred_language or "en"
        
        # Create meeting room
        meeting = await meeting_integration.create_meeting(
            str(current_user.id), 
            session_data.meeting_platform
        )
        
        # Create AI session in database
        ai_session = AISession(
            user_id=current_user.id,
            session_id=session_id,
            language=language,
            meeting_id=meeting["id"],
            meeting_platform=meeting["platform"],
            status="active"
        )
        
        db.add(ai_session)
        db.commit()
        db.refresh(ai_session)
        
        # Join meeting as AI bot
        await meeting_integration.join_meeting_as_bot(meeting["id"], ai_companion)
        
        # Send welcome message
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        user_context = {}
        if user_profile:
            user_context = {
                "preferred_name": user_profile.display_name,
                "interests": user_profile.interests,
                "emotional_needs": user_profile.emotional_needs
            }
        
        welcome_message = language_detector.get_greeting(language)
        
        # Save welcome message
        welcome_msg = SessionMessage(
            session_id=ai_session.id,
            role="assistant",
            content=welcome_message,
            language=language
        )
        db.add(welcome_msg)
        db.commit()
        
        logger.info(f"AI session started: {session_id} for user {current_user.id}")
        
        return SessionResponse.from_orm(ai_session)
        
    except Exception as e:
        logger.error(f"Failed to start AI session: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start AI session"
        )

@router.post("/send-message", response_model=MessageResponse)
async def send_text_message(
    message_data: MessageCreate,
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a text message to AI companion"""
    try:
        # Get AI session
        ai_session = db.query(AISession).filter(
            AISession.session_id == session_id,
            AISession.user_id == current_user.id,
            AISession.status == "active"
        ).first()
        
        if not ai_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active session not found"
            )
        
        # Detect language
        detected_language = language_detector.detect_language(message_data.content)
        
        # Save user message
        user_message = SessionMessage(
            session_id=ai_session.id,
            role="user",
            content=message_data.content,
            language=detected_language
        )
        db.add(user_message)
        
        # Get user context
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        user_context = {}
        if user_profile:
            user_context = {
                "preferred_name": user_profile.display_name,
                "interests": user_profile.interests,
                "emotional_needs": user_profile.emotional_needs
            }
        
        # Generate AI response
        ai_response = await ai_companion.generate_response(
            message_data.content,
            detected_language,
            str(current_user.id),
            user_context
        )
        
        # Save AI response
        ai_message = SessionMessage(
            session_id=ai_session.id,
            role="assistant",
            content=ai_response,
            language=detected_language
        )
        db.add(ai_message)
        
        # Update session stats
        ai_session.message_count += 2
        
        db.commit()
        db.refresh(ai_message)
        
        logger.info(f"Message processed in session {session_id}")
        
        return MessageResponse.from_orm(ai_message)
        
    except AIServiceException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.post("/voice-message", response_model=VoiceMessageResponse)
async def process_voice_message(
    session_id: str,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process voice message and return AI response"""
    try:
        # Get AI session
        ai_session = db.query(AISession).filter(
            AISession.session_id == session_id,
            AISession.user_id == current_user.id,
            AISession.status == "active"
        ).first()
        
        if not ai_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active session not found"
            )
        
        # Check if user has premium for voice features
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required for voice messages"
            )
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Validate audio format
        if not voice_processor.validate_audio_format(audio_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio format. Supported formats: WAV, FLAC, AIFF"
            )
        
        # Convert speech to text
        user_text = await voice_processor.speech_to_text(audio_data, ai_session.language)
        
        # Detect language
        detected_language = language_detector.detect_language(user_text)
        
        # Save user message
        user_message = SessionMessage(
            session_id=ai_session.id,
            role="user",
            content=user_text,
            language=detected_language,
            audio_duration=len(audio_data) / 16000  # Approximate duration
        )
        db.add(user_message)
        
        # Get user context
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        user_context = {}
        if user_profile:
            user_context = {
                "preferred_name": user_profile.display_name,
                "interests": user_profile.interests,
                "emotional_needs": user_profile.emotional_needs
            }
        
        # Generate AI response
        ai_response = await ai_companion.generate_response(
            user_text,
            detected_language,
            str(current_user.id),
            user_context
        )
        
        # Convert response to speech
        response_audio = await voice_processor.text_to_speech(ai_response, detected_language)
        response_audio_b64 = base64.b64encode(response_audio).decode()
        
        # Save AI response
        ai_message = SessionMessage(
            session_id=ai_session.id,
            role="assistant",
            content=ai_response,
            language=detected_language,
            audio_duration=len(response_audio) / 16000  # Approximate duration
        )
        db.add(ai_message)
        
        # Update session stats
        ai_session.message_count += 2
        
        db.commit()
        
        logger.info(f"Voice message processed in session {session_id}")
        
        return VoiceMessageResponse(
            user_message=user_text,
            ai_response=ai_response,
            language=detected_language,
            response_audio=response_audio_b64,
            session_id=session_id
        )
        
    except VoiceProcessingException:
        raise
    except AIServiceException:
        raise
    except Exception as e:
        logger.error(f"Failed to process voice message: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice message"
        )

@router.get("/session/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages from a session"""
    try:
        # Get AI session
        ai_session = db.query(AISession).filter(
            AISession.session_id == session_id,
            AISession.user_id == current_user.id
        ).first()
        
        if not ai_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get messages
        messages = db.query(SessionMessage).filter(
            SessionMessage.session_id == ai_session.id
        ).order_by(SessionMessage.created_at).all()
        
        return [MessageResponse.from_orm(msg) for msg in messages]
        
    except Exception as e:
        logger.error(f"Failed to get session messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )

@router.post("/session/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """End an AI session"""
    try:
        # Get AI session
        ai_session = db.query(AISession).filter(
            AISession.session_id == session_id,
            AISession.user_id == current_user.id,
            AISession.status == "active"
        ).first()
        
        if not ai_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active session not found"
            )
        
        # End meeting
        if ai_session.meeting_id:
            await meeting_integration.end_meeting(ai_session.meeting_id)
        
        # Update session
        ai_session.status = "completed"
        ai_session.ended_at = datetime.utcnow()
        
        # Calculate duration
        duration = (ai_session.ended_at - ai_session.created_at).total_seconds() / 60
        ai_session.duration_minutes = int(duration)
        
        db.commit()
        
        # Clear conversation history
        ai_companion.clear_conversation_history(str(current_user.id))
        
        logger.info(f"AI session ended: {session_id}")
        
        return {"message": "Session ended successfully", "duration_minutes": ai_session.duration_minutes}
        
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session"
        )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's AI sessions"""
    try:
        sessions = db.query(AISession).filter(
            AISession.user_id == current_user.id
        ).order_by(AISession.created_at.desc()).limit(50).all()
        
        return [SessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": language_detector.get_supported_languages(),
        "meeting_platforms": meeting_integration.get_meeting_platforms()
    }
