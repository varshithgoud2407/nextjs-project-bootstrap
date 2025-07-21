import asyncio
import json
import logging
from typing import Dict, Optional, Any
from config import settings
from exceptions import MeetingException

logger = logging.getLogger(__name__)

class MeetingIntegration:
    def __init__(self):
        self.active_meetings: Dict[str, Dict] = {}
        self.zoom_configured = bool(settings.ZOOM_API_KEY and settings.ZOOM_API_SECRET)
        self.google_meet_configured = bool(settings.GOOGLE_MEET_API_KEY)
        
    async def create_meeting(self, user_id: str, platform: str = "zoom") -> Dict[str, Any]:
        """Create a meeting room for AI session"""
        try:
            if platform == "zoom" and self.zoom_configured:
                return await self._create_zoom_meeting(user_id)
            elif platform == "google_meet" and self.google_meet_configured:
                return await self._create_google_meet(user_id)
            else:
                # Fallback to simple meeting room
                return await self._create_simple_meeting(user_id)
                
        except Exception as e:
            logger.error(f"Failed to create meeting: {e}")
            raise MeetingException(f"Could not create meeting room: {str(e)}")
    
    async def _create_zoom_meeting(self, user_id: str) -> Dict[str, Any]:
        """Create a Zoom meeting (placeholder - requires Zoom SDK integration)"""
        # This would integrate with Zoom SDK
        # For now, return a mock meeting structure
        meeting_id = f"zoom_{user_id}_{int(asyncio.get_event_loop().time())}"
        
        meeting_data = {
            "id": meeting_id,
            "platform": "zoom",
            "join_url": f"https://zoom.us/j/{meeting_id}",
            "meeting_id": meeting_id,
            "password": "openheart123",
            "host_key": f"host_{meeting_id}",
            "created_at": asyncio.get_event_loop().time(),
            "user_id": user_id,
            "status": "created"
        }
        
        self.active_meetings[meeting_id] = meeting_data
        logger.info(f"Created Zoom meeting {meeting_id} for user {user_id}")
        
        return meeting_data
    
    async def _create_google_meet(self, user_id: str) -> Dict[str, Any]:
        """Create a Google Meet (placeholder - requires Google Meet API integration)"""
        # This would integrate with Google Meet API
        # For now, return a mock meeting structure
        meeting_id = f"meet_{user_id}_{int(asyncio.get_event_loop().time())}"
        
        meeting_data = {
            "id": meeting_id,
            "platform": "google_meet",
            "join_url": f"https://meet.google.com/{meeting_id}",
            "meeting_id": meeting_id,
            "created_at": asyncio.get_event_loop().time(),
            "user_id": user_id,
            "status": "created"
        }
        
        self.active_meetings[meeting_id] = meeting_data
        logger.info(f"Created Google Meet {meeting_id} for user {user_id}")
        
        return meeting_data
    
    async def _create_simple_meeting(self, user_id: str) -> Dict[str, Any]:
        """Create a simple meeting room (WebRTC-based)"""
        meeting_id = f"simple_{user_id}_{int(asyncio.get_event_loop().time())}"
        
        meeting_data = {
            "id": meeting_id,
            "platform": "webrtc",
            "join_url": f"/meeting/{meeting_id}",
            "meeting_id": meeting_id,
            "created_at": asyncio.get_event_loop().time(),
            "user_id": user_id,
            "status": "created",
            "webrtc_config": {
                "iceServers": [
                    {"urls": "stun:stun.l.google.com:19302"},
                    {"urls": "stun:stun1.l.google.com:19302"}
                ]
            }
        }
        
        self.active_meetings[meeting_id] = meeting_data
        logger.info(f"Created simple meeting {meeting_id} for user {user_id}")
        
        return meeting_data
    
    async def join_meeting_as_bot(self, meeting_id: str, ai_companion) -> bool:
        """Join meeting as AI bot to listen and respond"""
        try:
            meeting = self.active_meetings.get(meeting_id)
            if not meeting:
                raise MeetingException("Meeting not found")
            
            # Update meeting status
            meeting["status"] = "ai_joined"
            meeting["ai_joined_at"] = asyncio.get_event_loop().time()
            
            logger.info(f"AI bot joined meeting {meeting_id}")
            
            # Start listening loop (this would be implemented with actual WebRTC/SDK)
            asyncio.create_task(self._ai_listening_loop(meeting_id, ai_companion))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to join meeting as bot: {e}")
            return False
    
    async def _ai_listening_loop(self, meeting_id: str, ai_companion):
        """AI listening loop for the meeting (placeholder)"""
        try:
            meeting = self.active_meetings.get(meeting_id)
            if not meeting:
                return
            
            logger.info(f"AI listening loop started for meeting {meeting_id}")
            
            # This would be the actual listening loop with WebRTC/SDK
            # For now, just maintain the meeting status
            while meeting.get("status") == "ai_joined":
                await asyncio.sleep(1)
                # In real implementation:
                # 1. Listen for audio from user
                # 2. Convert speech to text
                # 3. Generate AI response
                # 4. Convert response to speech
                # 5. Play AI response in meeting
                
        except Exception as e:
            logger.error(f"Error in AI listening loop: {e}")
    
    async def end_meeting(self, meeting_id: str) -> bool:
        """End a meeting"""
        try:
            meeting = self.active_meetings.get(meeting_id)
            if not meeting:
                return False
            
            meeting["status"] = "ended"
            meeting["ended_at"] = asyncio.get_event_loop().time()
            
            logger.info(f"Meeting {meeting_id} ended")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end meeting: {e}")
            return False
    
    async def get_meeting_info(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting information"""
        return self.active_meetings.get(meeting_id)
    
    async def list_active_meetings(self, user_id: str) -> list:
        """List active meetings for a user"""
        user_meetings = []
        for meeting_id, meeting in self.active_meetings.items():
            if meeting.get("user_id") == user_id and meeting.get("status") in ["created", "ai_joined"]:
                user_meetings.append(meeting)
        return user_meetings
    
    def get_meeting_platforms(self) -> Dict[str, bool]:
        """Get available meeting platforms"""
        return {
            "zoom": self.zoom_configured,
            "google_meet": self.google_meet_configured,
            "webrtc": True  # Always available as fallback
        }
    
    async def cleanup_old_meetings(self, max_age_hours: int = 24):
        """Clean up old meetings"""
        current_time = asyncio.get_event_loop().time()
        max_age_seconds = max_age_hours * 3600
        
        meetings_to_remove = []
        for meeting_id, meeting in self.active_meetings.items():
            if current_time - meeting.get("created_at", 0) > max_age_seconds:
                meetings_to_remove.append(meeting_id)
        
        for meeting_id in meetings_to_remove:
            del self.active_meetings[meeting_id]
            logger.info(f"Cleaned up old meeting {meeting_id}")
        
        return len(meetings_to_remove)

# WebRTC signaling for simple meetings
class WebRTCSignaling:
    def __init__(self):
        self.connections: Dict[str, Dict] = {}
    
    async def handle_offer(self, meeting_id: str, offer: Dict) -> Dict:
        """Handle WebRTC offer"""
        # This would handle WebRTC signaling
        # Return answer for the offer
        return {
            "type": "answer",
            "sdp": "mock_answer_sdp"
        }
    
    async def handle_ice_candidate(self, meeting_id: str, candidate: Dict):
        """Handle ICE candidate"""
        # This would handle ICE candidates for WebRTC
        pass
    
    async def add_connection(self, meeting_id: str, connection_id: str):
        """Add a connection to the meeting"""
        if meeting_id not in self.connections:
            self.connections[meeting_id] = {}
        
        self.connections[meeting_id][connection_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "status": "connected"
        }
