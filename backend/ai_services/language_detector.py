from langdetect import detect, DetectorFactory
from typing import Dict, Optional
import logging

# Set seed for consistent results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

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
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'he': 'Hebrew'
        }
        
        self.language_greetings = {
            'en': "Hello! I'm here to listen and support you. How are you feeling today?",
            'de': "Hallo! Ich bin hier, um zuzuhören und dich zu unterstützen. Wie fühlst du dich heute?",
            'es': "¡Hola! Estoy aquí para escuchar y apoyarte. ¿Cómo te sientes hoy?",
            'fr': "Bonjour! Je suis là pour écouter et vous soutenir. Comment vous sentez-vous aujourd'hui?",
            'it': "Ciao! Sono qui per ascoltare e supportarti. Come ti senti oggi?",
            'pt': "Olá! Estou aqui para ouvir e apoiá-lo. Como você está se sentindo hoje?",
            'ru': "Привет! Я здесь, чтобы слушать и поддерживать вас. Как вы себя чувствуете сегодня?",
            'ja': "こんにちは！私はあなたの話を聞き、サポートするためにここにいます。今日はどんな気分ですか？",
            'ko': "안녕하세요! 저는 당신의 이야기를 듣고 지원하기 위해 여기 있습니다. 오늘 기분이 어떠세요?",
            'zh': "你好！我在这里倾听并支持你。你今天感觉怎么样？",
            'ar': "مرحبا! أنا هنا للاستماع ودعمك. كيف تشعر اليوم؟",
            'hi': "नमस्ते! मैं यहाँ आपकी बात सुनने और आपका साथ देने के लिए हूँ। आज आप कैसा महसूस कर रहे हैं?",
            'nl': "Hallo! Ik ben hier om te luisteren en je te steunen. Hoe voel je je vandaag?",
            'sv': "Hej! Jag är här för att lyssna och stödja dig. Hur mår du idag?",
            'no': "Hei! Jeg er her for å lytte og støtte deg. Hvordan har du det i dag?",
            'da': "Hej! Jeg er her for at lytte og støtte dig. Hvordan har du det i dag?",
            'fi': "Hei! Olen täällä kuuntelemassa ja tukemassa sinua. Miltä sinusta tuntuu tänään?",
            'pl': "Cześć! jestem tutaj, żeby słuchać i wspierać cię. Jak się dziś czujesz?",
            'tr': "Merhaba! Seni dinlemek ve desteklemek için buradayım. Bugün nasıl hissediyorsun?",
            'he': "שלום! אני כאן כדי להקשיב ולתמוך בך. איך אתה מרגיש היום?"
        }
    
    def detect_language(self, text: str) -> str:
        """Detect language from text input"""
        if not text or len(text.strip()) < 3:
            return 'en'  # Default to English for very short texts
            
        try:
            detected = detect(text)
            if detected in self.supported_languages:
                logger.info(f"Detected language: {detected} ({self.supported_languages[detected]})")
                return detected
            else:
                logger.warning(f"Unsupported language detected: {detected}, defaulting to English")
                return 'en'
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}, defaulting to English")
            return 'en'
    
    def get_language_name(self, language_code: str) -> str:
        """Get full language name from code"""
        return self.supported_languages.get(language_code, "English")
    
    def get_greeting(self, language_code: str) -> str:
        """Get greeting message in specified language"""
        return self.language_greetings.get(language_code, self.language_greetings['en'])
    
    def is_supported(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in self.supported_languages
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.supported_languages.copy()
