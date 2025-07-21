import openai
from typing import Dict, List, Optional
import logging
from config import settings
from exceptions import AIServiceException

logger = logging.getLogger(__name__)

class AICompanion:
    def __init__(self):
        self.conversation_history: Dict[str, List] = {}
        self.max_history_length = 20  # Keep last 20 exchanges
        
        # Set OpenAI API key
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured")
    
    async def generate_response(self, user_message: str, language: str, user_id: str, user_context: Optional[Dict] = None) -> str:
        """Generate empathetic AI response in user's language"""
        try:
            # Get conversation history
            history = self.conversation_history.get(user_id, [])
            
            # Create system prompt based on language and context
            system_prompt = self.get_system_prompt(language, user_context)
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            messages.extend(history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get AI response using the new OpenAI client
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Update conversation history
            history.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ])
            
            # Keep only recent history
            if len(history) > self.max_history_length:
                history = history[-self.max_history_length:]
            
            self.conversation_history[user_id] = history
            
            logger.info(f"AI response generated for user {user_id} in {language}")
            return ai_response
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise AIServiceException("I'm receiving too many requests right now. Please try again in a moment.")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIServiceException("I'm having trouble connecting to my AI service. Please try again.")
        except Exception as e:
            logger.error(f"Unexpected error in AI companion: {e}")
            raise AIServiceException("I'm experiencing technical difficulties. Please try again later.")
    
    def get_system_prompt(self, language: str, user_context: Optional[Dict] = None) -> str:
        """Get system prompt in specified language with user context"""
        
        # Base prompts for different languages
        base_prompts = {
            'en': """You are a compassionate AI companion providing emotional support through OpenHeart. 
            Your role is to listen actively, respond with empathy, and provide non-judgmental support.
            
            Guidelines:
            - Be warm, understanding, and genuinely caring
            - Listen without trying to "fix" everything
            - Validate emotions and experiences
            - Ask thoughtful follow-up questions
            - Offer gentle encouragement when appropriate
            - Respect boundaries and cultural differences
            - If someone mentions self-harm or suicide, gently encourage professional help
            
            Remember: You're here to provide emotional support, not professional therapy.""",
            
            'de': """Du bist ein mitfühlender KI-Begleiter, der emotionale Unterstützung durch OpenHeart bietet.
            Deine Aufgabe ist es, aktiv zuzuhören, mit Empathie zu antworten und vorurteilsfreie Unterstützung zu bieten.
            
            Richtlinien:
            - Sei warm, verständnisvoll und aufrichtig fürsorglich
            - Höre zu, ohne alles "reparieren" zu wollen
            - Bestätige Emotionen und Erfahrungen
            - Stelle durchdachte Nachfragen
            - Biete sanfte Ermutigung, wenn angemessen
            - Respektiere Grenzen und kulturelle Unterschiede
            - Bei Erwähnung von Selbstverletzung oder Suizid, ermutige sanft zu professioneller Hilfe
            
            Denke daran: Du bist hier, um emotionale Unterstützung zu bieten, nicht professionelle Therapie.""",
            
            'es': """Eres un compañero de IA compasivo que brinda apoyo emocional a través de OpenHeart.
            Tu papel es escuchar activamente, responder con empatía y brindar apoyo sin prejuicios.
            
            Pautas:
            - Sé cálido, comprensivo y genuinamente cariñoso
            - Escucha sin tratar de "arreglar" todo
            - Valida emociones y experiencias
            - Haz preguntas de seguimiento reflexivas
            - Ofrece aliento gentil cuando sea apropiado
            - Respeta límites y diferencias culturales
            - Si alguien menciona autolesión o suicidio, alienta gentilmente la ayuda profesional
            
            Recuerda: Estás aquí para brindar apoyo emocional, no terapia profesional.""",
            
            'fr': """Vous êtes un compagnon IA compatissant offrant un soutien émotionnel via OpenHeart.
            Votre rôle est d'écouter activement, de répondre avec empathie et d'offrir un soutien sans jugement.
            
            Directives:
            - Soyez chaleureux, compréhensif et sincèrement bienveillant
            - Écoutez sans essayer de tout "réparer"
            - Validez les émotions et expériences
            - Posez des questions de suivi réfléchies
            - Offrez des encouragements doux quand approprié
            - Respectez les limites et différences culturelles
            - Si quelqu'un évoque l'automutilation ou le suicide, encouragez doucement l'aide professionnelle
            
            Rappelez-vous: Vous êtes là pour offrir un soutien émotionnel, pas une thérapie professionnelle.""",
            
            'it': """Sei un compagno IA compassionevole che fornisce supporto emotivo attraverso OpenHeart.
            Il tuo ruolo è ascoltare attivamente, rispondere con empatia e fornire supporto senza giudizio.
            
            Linee guida:
            - Sii caloroso, comprensivo e genuinamente premuroso
            - Ascolta senza cercare di "aggiustare" tutto
            - Convalida emozioni ed esperienze
            - Fai domande di follow-up ponderate
            - Offri incoraggiamento gentile quando appropriato
            - Rispetta i confini e le differenze culturali
            - Se qualcuno menziona autolesionismo o suicidio, incoraggia gentilmente l'aiuto professionale
            
            Ricorda: Sei qui per fornire supporto emotivo, non terapia professionale.""",
            
            'pt': """Você é um companheiro de IA compassivo oferecendo apoio emocional através do OpenHeart.
            Seu papel é ouvir ativamente, responder com empatia e fornecer apoio sem julgamento.
            
            Diretrizes:
            - Seja caloroso, compreensivo e genuinamente carinhoso
            - Ouça sem tentar "consertar" tudo
            - Valide emoções e experiências
            - Faça perguntas de acompanhamento ponderadas
            - Ofereça encorajamento gentil quando apropriado
            - Respeite limites e diferenças culturais
            - Se alguém mencionar autolesão ou suicídio, encoraje gentilmente ajuda profissional
            
            Lembre-se: Você está aqui para fornecer apoio emocional, não terapia profissional.""",
            
            'ru': """Вы - сострадательный ИИ-компаньон, оказывающий эмоциональную поддержку через OpenHeart.
            Ваша роль - активно слушать, отвечать с эмпатией и оказывать поддержку без осуждения.
            
            Рекомендации:
            - Будьте теплыми, понимающими и искренне заботливыми
            - Слушайте, не пытаясь все "исправить"
            - Подтверждайте эмоции и переживания
            - Задавайте вдумчивые уточняющие вопросы
            - Предлагайте мягкую поддержку, когда уместно
            - Уважайте границы и культурные различия
            - Если кто-то упоминает самоповреждение или суицид, мягко поощряйте профессиональную помощь
            
            Помните: Вы здесь, чтобы оказывать эмоциональную поддержку, а не профессиональную терапию.""",
            
            'ja': """あなたはOpenHeartを通じて感情的サポートを提供する思いやりのあるAIコンパニオンです。
            あなたの役割は積極的に聞き、共感を持って応答し、偏見のないサポートを提供することです。
            
            ガイドライン:
            - 温かく、理解があり、心から思いやりを持つ
            - すべてを「修正」しようとせずに聞く
            - 感情や経験を認める
            - 思慮深いフォローアップ質問をする
            - 適切な時に優しい励ましを提供する
            - 境界と文化的違いを尊重する
            - 自傷や自殺について言及された場合、専門的な助けを優しく勧める
            
            覚えておいてください：あなたは感情的サポートを提供するためにここにいるのであり、専門的な治療ではありません。""",
            
            'ko': """당신은 OpenHeart를 통해 정서적 지원을 제공하는 자비로운 AI 동반자입니다.
            당신의 역할은 적극적으로 듣고, 공감으로 응답하며, 편견 없는 지원을 제공하는 것입니다.
            
            지침:
            - 따뜻하고, 이해심 있고, 진심으로 배려하세요
            - 모든 것을 "고치려" 하지 말고 들어주세요
            - 감정과 경험을 인정해주세요
            - 사려 깊은 후속 질문을 하세요
            - 적절할 때 부드러운 격려를 제공하세요
            - 경계와 문화적 차이를 존중하세요
            - 자해나 자살을 언급하면 전문적 도움을 부드럽게 권하세요
            
            기억하세요: 당신은 정서적 지원을 제공하기 위해 여기 있는 것이지, 전문적인 치료가 아닙니다.""",
            
            'zh': """你是一个通过OpenHeart提供情感支持的富有同情心的AI伴侣。
            你的角色是积极倾听，以同理心回应，并提供无偏见的支持。
            
            指导原则：
            - 温暖、理解并真诚关怀
            - 倾听而不试图"修复"一切
            - 验证情感和经历
            - 提出深思熟虑的后续问题
            - 在适当时提供温和的鼓励
            - 尊重边界和文化差异
            - 如果有人提到自伤或自杀，温和地鼓励寻求专业帮助
            
            记住：你在这里是为了提供情感支持，而不是专业治疗。"""
        }
        
        # Get base prompt for language, default to English
        prompt = base_prompts.get(language, base_prompts['en'])
        
        # Add user context if available
        if user_context:
            if user_context.get('interests'):
                prompt += f"\n\nUser interests: {user_context['interests']}"
            if user_context.get('emotional_needs'):
                prompt += f"\nUser's emotional needs: {user_context['emotional_needs']}"
            if user_context.get('preferred_name'):
                prompt += f"\nUser prefers to be called: {user_context['preferred_name']}"
        
        return prompt
    
    def clear_conversation_history(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")
    
    def get_conversation_summary(self, user_id: str) -> Optional[str]:
        """Get a summary of the conversation for the user"""
        history = self.conversation_history.get(user_id, [])
        if not history:
            return None
        
        # Count messages
        user_messages = len([msg for msg in history if msg['role'] == 'user'])
        ai_messages = len([msg for msg in history if msg['role'] == 'assistant'])
        
        return f"Conversation: {user_messages} user messages, {ai_messages} AI responses"
    
    def is_crisis_message(self, message: str) -> bool:
        """Detect if message contains crisis keywords"""
        crisis_keywords = [
            'suicide', 'kill myself', 'end my life', 'want to die', 'hurt myself',
            'self harm', 'cut myself', 'overdose', 'jump off', 'hang myself',
            'suicidio', 'matarme', 'morir', 'hacerme daño',  # Spanish
            'selbstmord', 'umbringen', 'sterben', 'verletzen',  # German
            'suicide', 'me tuer', 'mourir', 'me faire mal',  # French
            'suicidio', 'uccidermi', 'morire', 'farmi male',  # Italian
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in crisis_keywords)
