import speech_recognition as sr
from gtts import gTTS
import io
import base64
import tempfile
import os
from typing import Optional
import logging
from exceptions import VoiceProcessingException

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
    async def speech_to_text(self, audio_data: bytes, language: str = "auto") -> str:
        """Convert speech to text using Google Speech Recognition"""
        try:
            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            try:
                # Load audio file
                with sr.AudioFile(temp_audio_path) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    # Record the audio
                    audio = self.recognizer.record(source)
                
                # Convert language code for Google Speech Recognition
                google_lang = self._convert_language_code(language)
                
                # Recognize speech
                if language == "auto":
                    # Try multiple languages if auto-detection
                    for lang in ["en-US", "de-DE", "es-ES", "fr-FR", "it-IT"]:
                        try:
                            text = self.recognizer.recognize_google(audio, language=lang)
                            logger.info(f"Speech recognized in {lang}: {text[:50]}...")
                            return text
                        except sr.UnknownValueError:
                            continue
                    raise VoiceProcessingException("Could not understand audio in any supported language")
                else:
                    text = self.recognizer.recognize_google(audio, language=google_lang)
                    logger.info(f"Speech recognized: {text[:50]}...")
                    return text
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except sr.UnknownValueError:
            logger.error("Could not understand audio")
            raise VoiceProcessingException("Could not understand the audio. Please speak clearly.")
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            raise VoiceProcessingException("Speech recognition service is temporarily unavailable.")
        except Exception as e:
            logger.error(f"Unexpected error in speech-to-text: {e}")
            raise VoiceProcessingException("An error occurred while processing your voice.")
    
    async def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """Convert text to speech using Google Text-to-Speech"""
        try:
            # Convert language code for gTTS
            gtts_lang = self._convert_to_gtts_language(language)
            
            # Create gTTS object
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_bytes = audio_buffer.getvalue()
            logger.info(f"Text-to-speech generated for language {gtts_lang}, size: {len(audio_bytes)} bytes")
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            raise VoiceProcessingException("Could not generate speech audio.")
    
    def _convert_language_code(self, language: str) -> str:
        """Convert language code to Google Speech Recognition format"""
        language_mapping = {
            'en': 'en-US',
            'de': 'de-DE',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'zh': 'zh-CN',
            'ar': 'ar-SA',
            'hi': 'hi-IN',
            'nl': 'nl-NL',
            'sv': 'sv-SE',
            'no': 'no-NO',
            'da': 'da-DK',
            'fi': 'fi-FI',
            'pl': 'pl-PL',
            'tr': 'tr-TR',
            'he': 'he-IL'
        }
        return language_mapping.get(language, 'en-US')
    
    def _convert_to_gtts_language(self, language: str) -> str:
        """Convert language code to gTTS format"""
        # gTTS uses ISO 639-1 codes, which are mostly the same as our codes
        gtts_mapping = {
            'zh': 'zh-cn',  # Chinese simplified
            'he': 'iw'      # Hebrew uses 'iw' in gTTS
        }
        return gtts_mapping.get(language, language)
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate if audio data is in supported format"""
        try:
            # Check if it's a valid audio file by trying to create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                with sr.AudioFile(temp_path) as source:
                    # Try to read a small portion
                    self.recognizer.record(source, duration=0.1)
                return True
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return [".wav", ".flac", ".aiff", ".aif"]
