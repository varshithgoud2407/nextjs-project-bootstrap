from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import json
import logging
from datetime import datetime

from database import get_db
from models import User, UserProfile, AISession
from dependencies import get_current_active_user
from ai_services.language_detector import LanguageDetector

logger = logging.getLogger(__name__)

router = APIRouter()
language_detector = LanguageDetector()

# Pydantic models
class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    emotional_needs: Optional[List[str]] = None
    timezone: Optional[str] = None
    country: Optional[str] = None
    preferred_language: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    display_name: Optional[str]
    bio: Optional[str]
    interests: Optional[List[str]]
    emotional_needs: Optional[List[str]]
    timezone: Optional[str]
    country: Optional[str]
    onboarding_completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class OnboardingData(BaseModel):
    display_name: str
    interests: List[str]
    emotional_needs: List[str]
    preferred_language: str = "en"
    timezone: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None

class UserStatsResponse(BaseModel):
    total_sessions: int
    total_minutes: int
    total_messages: int
    languages_used: List[str]
    favorite_language: str
    premium_status: bool

# Predefined options for interests and emotional needs
INTEREST_OPTIONS = [
    "Anxiety", "Depression", "Stress", "Relationships", "Work", "Family",
    "Health", "Sleep", "Self-esteem", "Loneliness", "Grief", "Trauma",
    "Career", "Education", "Finances", "Social anxiety", "Panic attacks",
    "Addiction", "Eating disorders", "PTSD", "Bipolar", "OCD",
    "Personal growth", "Mindfulness", "Meditation", "Exercise", "Hobbies",
    "Creativity", "Music", "Art", "Reading", "Travel", "Technology",
    "Gaming", "Sports", "Cooking", "Nature", "Animals", "Spirituality"
]

EMOTIONAL_NEEDS = [
    "Someone to listen without judgment",
    "Emotional validation and support",
    "Help processing difficult emotions",
    "Coping strategies for stress",
    "Motivation and encouragement",
    "Help with decision making",
    "Understanding and empathy",
    "Safe space to express feelings",
    "Help with self-reflection",
    "Support during difficult times",
    "Confidence building",
    "Help with communication skills",
    "Stress relief techniques",
    "Mindfulness and relaxation",
    "Goal setting and achievement"
]

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            # Create default profile if it doesn't exist
            profile = UserProfile(
                user_id=current_user.id,
                display_name=current_user.full_name,
                onboarding_completed=False
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Parse JSON fields
        profile_dict = {
            "id": profile.id,
            "display_name": profile.display_name,
            "bio": profile.bio,
            "interests": json.loads(profile.interests) if profile.interests else [],
            "emotional_needs": json.loads(profile.emotional_needs) if profile.emotional_needs else [],
            "timezone": profile.timezone,
            "country": profile.country,
            "onboarding_completed": profile.onboarding_completed,
            "created_at": profile.created_at
        }
        
        return UserProfileResponse(**profile_dict)
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Update fields
        if profile_update.display_name is not None:
            profile.display_name = profile_update.display_name
        
        if profile_update.bio is not None:
            profile.bio = profile_update.bio
        
        if profile_update.interests is not None:
            profile.interests = json.dumps(profile_update.interests)
        
        if profile_update.emotional_needs is not None:
            profile.emotional_needs = json.dumps(profile_update.emotional_needs)
        
        if profile_update.timezone is not None:
            profile.timezone = profile_update.timezone
        
        if profile_update.country is not None:
            profile.country = profile_update.country
        
        if profile_update.preferred_language is not None:
            if language_detector.is_supported(profile_update.preferred_language):
                current_user.preferred_language = profile_update.preferred_language
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported language"
                )
        
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        # Return updated profile
        profile_dict = {
            "id": profile.id,
            "display_name": profile.display_name,
            "bio": profile.bio,
            "interests": json.loads(profile.interests) if profile.interests else [],
            "emotional_needs": json.loads(profile.emotional_needs) if profile.emotional_needs else [],
            "timezone": profile.timezone,
            "country": profile.country,
            "onboarding_completed": profile.onboarding_completed,
            "created_at": profile.created_at
        }
        
        logger.info(f"Profile updated for user {current_user.id}")
        
        return UserProfileResponse(**profile_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.post("/onboarding")
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete user onboarding"""
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Validate language
        if not language_detector.is_supported(onboarding_data.preferred_language):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported language"
            )
        
        # Update profile with onboarding data
        profile.display_name = onboarding_data.display_name
        profile.interests = json.dumps(onboarding_data.interests)
        profile.emotional_needs = json.dumps(onboarding_data.emotional_needs)
        profile.timezone = onboarding_data.timezone
        profile.country = onboarding_data.country
        profile.bio = onboarding_data.bio
        profile.onboarding_completed = True
        profile.updated_at = datetime.utcnow()
        
        # Update user's preferred language
        current_user.preferred_language = onboarding_data.preferred_language
        
        db.commit()
        
        logger.info(f"Onboarding completed for user {current_user.id}")
        
        return {"message": "Onboarding completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding"
        )

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    try:
        # Get session statistics
        sessions = db.query(AISession).filter(
            AISession.user_id == current_user.id
        ).all()
        
        total_sessions = len(sessions)
        total_minutes = sum(session.duration_minutes or 0 for session in sessions)
        total_messages = sum(session.message_count or 0 for session in sessions)
        
        # Get languages used
        languages_used = list(set(session.language for session in sessions if session.language))
        
        # Find most used language
        language_counts = {}
        for session in sessions:
            if session.language:
                language_counts[session.language] = language_counts.get(session.language, 0) + 1
        
        favorite_language = max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else current_user.preferred_language
        
        return UserStatsResponse(
            total_sessions=total_sessions,
            total_minutes=total_minutes,
            total_messages=total_messages,
            languages_used=languages_used,
            favorite_language=favorite_language,
            premium_status=current_user.is_premium
        )
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.get("/onboarding-options")
async def get_onboarding_options():
    """Get options for onboarding (interests, emotional needs, languages)"""
    return {
        "interests": INTEREST_OPTIONS,
        "emotional_needs": EMOTIONAL_NEEDS,
        "languages": language_detector.get_supported_languages()
    }

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    try:
        # In a real implementation, you would:
        # 1. Cancel any active subscriptions
        # 2. Delete or anonymize user data according to privacy laws
        # 3. Send confirmation email
        
        # For now, just deactivate the account
        current_user.is_active = False
        db.commit()
        
        logger.info(f"Account deactivated for user {current_user.id}")
        
        return {"message": "Account deactivated successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )

@router.post("/change-language")
async def change_language(
    language: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user's preferred language"""
    try:
        if not language_detector.is_supported(language):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported language"
            )
        
        current_user.preferred_language = language
        db.commit()
        
        logger.info(f"Language changed to {language} for user {current_user.id}")
        
        return {
            "message": "Language updated successfully",
            "language": language,
            "language_name": language_detector.get_language_name(language)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change language"
        )
