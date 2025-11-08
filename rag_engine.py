from openai import OpenAI
try:
    from langchain_chroma import Chroma
except ImportError:
    # 兼容旧版本
    from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import Settings
import chromadb
import os
import warnings
from typing import List, Dict, Tuple
import re

# 忽略LangChain deprecation警告（如果使用旧版本）
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

class RAGEngine:
    def __init__(self):
        self.client = OpenAI(api_key=Settings.OPENAI_API_KEY)
        self.embeddings = OpenAIEmbeddings(
            model=Settings.EMBEDDING_MODEL,
            openai_api_key=Settings.OPENAI_API_KEY
        )
        self.vectorstore = self._load_vectorstore()
        
        # 翻译缓存（提升性能，不影响功能）
        self._translation_cache = {}
        
        # 保存用户的首选语言（用于后续输出保持一致）
        self.user_preferred_language = None
        
        # 加拿大各省资源
        self.provincial_resources = {
            'BC': {
                'name_zh': '不列颠哥伦比亚省',
                'name_en': 'British Columbia',
                'resources_zh': [
                    'HealthLink BC: 811',
                    'BC Mental Health Support Line: 310-6789（无需区号）',
                    'Bounce Back BC',
                    'www.here2talk.ca（大专学生）'
                ],
                'resources_en': [
                    'HealthLink BC: 811',
                    'BC Mental Health Support Line: 310-6789 (no area code needed)',
                    'Bounce Back BC',
                    'www.here2talk.ca (for post-secondary students)'
                ]
            },
            'AB': {
                'name_zh': '阿尔伯塔省',
                'name_en': 'Alberta',
                'resources_zh': [
                    'Health Link: 811',
                    'Mental Health Help Line: 1-877-303-2642',
                    'Addiction Helpline: 1-866-332-2322'
                ],
                'resources_en': [
                    'Health Link: 811',
                    'Mental Health Help Line: 1-877-303-2642',
                    'Addiction Helpline: 1-866-332-2322'
                ]
            },
            'SK': {
                'name_zh': '萨斯喀彻温省',
                'name_en': 'Saskatchewan',
                'resources_zh': [
                    'HealthLine: 811',
                    'Saskatchewan Crisis Line: 306-525-5333'
                ],
                'resources_en': [
                    'HealthLine: 811',
                    'Saskatchewan Crisis Line: 306-525-5333'
                ]
            },
            'MB': {
                'name_zh': '曼尼托巴省',
                'name_en': 'Manitoba',
                'resources_zh': [
                    'Health Links: 204-788-8200 或 1-888-315-9257',
                    'Klinic Crisis Line: 204-786-8686 或 1-888-322-3019'
                ],
                'resources_en': [
                    'Health Links: 204-788-8200 or 1-888-315-9257',
                    'Klinic Crisis Line: 204-786-8686 or 1-888-322-3019'
                ]
            },
            'ON': {
                'name_zh': '安大略省',
                'name_en': 'Ontario',
                'resources_zh': [
                    'Telehealth Ontario: 1-866-797-0000',
                    'ConnexOntario: 1-866-531-2600'
                ],
                'resources_en': [
                    'Telehealth Ontario: 1-866-797-0000',
                    'ConnexOntario: 1-866-531-2600'
                ]
            },
            'QC': {
                'name_zh': '魁北克省',
                'name_en': 'Quebec',
                'resources_zh': [
                    'Info-Santé: 811',
                    'Suicide Prevention: 1-866-APPELLE (277-3553)'
                ],
                'resources_en': [
                    'Info-Santé: 811',
                    'Suicide Prevention: 1-866-APPELLE (277-3553)'
                ]
            },
            'NB': {
                'name_zh': '新不伦瑞克省',
                'name_en': 'New Brunswick',
                'resources_zh': [
                    'Tele-Care: 811',
                    'Chimo Helpline: 1-800-667-5005'
                ],
                'resources_en': [
                    'Tele-Care: 811',
                    'Chimo Helpline: 1-800-667-5005'
                ]
            },
            'NS': {
                'name_zh': '新斯科舍省',
                'name_en': 'Nova Scotia',
                'resources_zh': [
                    '811（24小时护理热线）',
                    'Mental Health Crisis Line: 1-888-429-8167'
                ],
                'resources_en': [
                    '811 (24/7 nursing line)',
                    'Mental Health Crisis Line: 1-888-429-8167'
                ]
            },
            'PE': {
                'name_zh': '爱德华王子岛省',
                'name_en': 'Prince Edward Island',
                'resources_zh': [
                    'Health PEI: 811',
                    'Island Help Line: 1-800-218-2885'
                ],
                'resources_en': [
                    'Health PEI: 811',
                    'Island Help Line: 1-800-218-2885'
                ]
            },
            'NL': {
                'name_zh': '纽芬兰和拉布拉多省',
                'name_en': 'Newfoundland and Labrador',
                'resources_zh': [
                    'HealthLine: 811',
                    'Mental Health Crisis Line: 1-888-737-4668'
                ],
                'resources_en': [
                    'HealthLine: 811',
                    'Mental Health Crisis Line: 1-888-737-4668'
                ]
            },
            'YT': {
                'name_zh': '育空地区',
                'name_en': 'Yukon',
                'resources_zh': [
                    '联系当地健康中心',
                    'Hope for Wellness Helpline（原住民）: 1-855-242-3310'
                ],
                'resources_en': [
                    'Contact local health centers',
                    'Hope for Wellness Helpline (for Indigenous peoples): 1-855-242-3310'
                ]
            },
            'NT': {
                'name_zh': '西北地区',
                'name_en': 'Northwest Territories',
                'resources_zh': [
                    '联系当地健康中心',
                    'Hope for Wellness Helpline（原住民）: 1-855-242-3310'
                ],
                'resources_en': [
                    'Contact local health centers',
                    'Hope for Wellness Helpline (for Indigenous peoples): 1-855-242-3310'
                ]
            },
            'NU': {
                'name_zh': '努纳武特地区',
                'name_en': 'Nunavut',
                'resources_zh': [
                    '联系当地健康中心',
                    'Hope for Wellness Helpline（原住民）: 1-855-242-3310'
                ],
                'resources_en': [
                    'Contact local health centers',
                    'Hope for Wellness Helpline (for Indigenous peoples): 1-855-242-3310'
                ]
            }
        }
    
    def _load_vectorstore(self):
        """加载向量数据库"""
        if Settings.USE_CHROMA_CLOUD:
            # 使用ChromaDB Cloud
            chroma_client = chromadb.CloudClient(
                api_key=Settings.CHROMA_API_KEY,
                tenant=Settings.CHROMA_TENANT,
                database=Settings.CHROMA_DATABASE
            )
            return Chroma(
                client=chroma_client,
                collection_name=Settings.COLLECTION_NAME,
                embedding_function=self.embeddings
            )
        else:
            # 使用本地ChromaDB
            if os.path.exists(Settings.VECTOR_DB_PATH):
                return Chroma(
                    persist_directory=Settings.VECTOR_DB_PATH,
                    embedding_function=self.embeddings,
                    collection_name=Settings.COLLECTION_NAME
                )
            else:
                raise FileNotFoundError(
                    f"Vector database not found at {Settings.VECTOR_DB_PATH}. "
                    "Please initialize the knowledge base first by running init_kb.py"
                )
    
    def _detect_conversation_stage(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """使用LLM检测对话阶段
        
        让LLM基于对话历史和当前消息来判断对话阶段，而不是使用硬编码规则：
        - Empathy: 用户刚开始表达，需要确认情绪（简单问候、初次表达）
        - Reflection: 用户已表达情绪，需要理解相似经历（分享情绪、想要理解）
        - Support: 用户寻求建议和支持（明确要求帮助、资源、建议）
        
        Returns:
            'empathy': 倾听阶段 - 用户刚刚开始表达，需要确认情绪
            'reflection': 理解阶段 - 用户已经表达，需要从assessment知识库帮助理解
            'support': 引导阶段 - 用户需要支持和建议，使用support知识库
        """
        # 检测用户语言
        user_language = self._detect_language(user_message)
        
        # 构建对话历史摘要
        history_summary = ""
        if conversation_history and len(conversation_history) > 0:
            history_summary = "\n对话历史（最近3轮）：\n" if user_language == 'zh' else "\nConversation history (last 3 turns):\n"
            for msg in conversation_history[-3:]:
                role = "用户" if msg.get('role') == 'user' else "AI" if user_language == 'zh' else ("User" if msg.get('role') == 'user' else "AI")
                content = msg.get('content', '')[:150]  # 截取前150字符
                history_summary += f"- {role}: {content}\n"
        else:
            history_summary = "\n这是首次对话。" if user_language == 'zh' else "\nThis is the first conversation."
        
        # 构建提示词
        if user_language == 'zh':
            prompt = f"""你是一个对话阶段分析专家。请分析用户的消息和对话历史，判断当前应该处于哪个对话阶段。

对话阶段定义：
1. **empathy（倾听阶段）**：用户刚开始表达，需要确认情绪
   - 简单问候（你好、hi、hello等）
   - 初次表达感受，但还在探索
   - 简短、不确定的表达
   - 需要鼓励继续表达

2. **reflection（理解阶段）**：用户已表达情绪，需要理解相似经历
   - 用户清楚地表达了情绪感受
   - 描述了具体的问题或困扰
   - 需要理解和共鸣，知道"不是只有我一个人这样"
   - 分享相似经验和理解

3. **support（引导阶段）**：用户寻求建议和支持
   - 明确询问"怎么办"、"如何"、"建议"
   - 寻求资源、帮助、治疗方法
   - 想要具体的行动建议
   - 对话已经深入，用户需要下一步指导

当前用户消息：{user_message}
{history_summary}

请只返回一个词：empathy、reflection 或 support
不要返回其他任何内容，只需要阶段名称。"""
        else:
            prompt = f"""You are a conversation stage analysis expert. Analyze the user's message and conversation history to determine the current conversation stage.

Stage definitions:
1. **empathy**: User is just starting to express, needs emotional acknowledgment
   - Simple greetings (hi, hello, 你好)
   - Initial expression, still exploring
   - Short, uncertain expressions
   - Needs encouragement to continue expressing

2. **reflection**: User has expressed emotions, needs understanding of similar experiences
   - User clearly expressed emotional feelings
   - Described specific problems or concerns
   - Needs understanding and empathy, knowing "I'm not alone"
   - Share similar experiences and understanding

3. **support**: User seeks advice and support
   - Explicitly asking "what to do", "how to", "suggestions"
   - Seeking resources, help, treatment methods
   - Wants concrete action advice
   - Conversation has deepened, user needs next-step guidance

Current user message: {user_message}
{history_summary}

Return only one word: empathy, reflection, or support
Do not return anything else, only the stage name."""
        
        try:
            # 调用LLM判断阶段
            response = self.client.chat.completions.create(
                model=Settings.FINETUNED_MODEL,
                messages=[
                    {"role": "system", "content": "You are a conversation stage analyzer. Return only the stage name: empathy, reflection, or support."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度确保准确性
                max_tokens=10
            )
            
            stage = response.choices[0].message.content.strip().lower()
            
            # 验证并提取阶段名称
            if 'empathy' in stage:
                return 'empathy'
            elif 'reflection' in stage:
                return 'reflection'
            elif 'support' in stage:
                return 'support'
            else:
                # 如果返回格式不对，使用后备逻辑
                print(f"[WARNING] Unexpected stage response: {stage}, using fallback")
                return self._fallback_stage_detection(user_message, conversation_history)
                    
        except Exception as e:
            # 如果LLM调用失败，使用后备逻辑
            print(f"[WARNING] LLM stage detection failed: {e}, using fallback logic")
            return self._fallback_stage_detection(user_message, conversation_history)
    
    def _fallback_stage_detection(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """后备的阶段检测逻辑（当LLM调用失败时使用）"""
        message_lower = user_message.lower().strip()
        
        # 简单问候或首次对话 → empathy
        if not conversation_history or len(message_lower) <= 10:
            return 'empathy'
        
        # 有明显寻求建议的关键词 → support
        support_keywords = ['怎么办', '如何', '建议', '方法', '帮助', '治疗', '资源', 'how to', 'what should', 'suggest', 'advice']
        if any(keyword in message_lower for keyword in support_keywords):
            return 'support'
        
        # 有情绪表达 → reflection
        emotion_keywords = ['感觉', '感到', '觉得', '难过', '焦虑', '抑郁', 'feel', 'sad', 'anxious', 'depressed']
        if any(keyword in message_lower for keyword in emotion_keywords):
            return 'reflection'
        
        # 默认 → empathy
        return 'empathy'
    
    def _get_system_prompt(self, stage: str = 'reflection', language: str = 'zh') -> str:
        """根据对话阶段和语言返回不同的系统提示词
        
        Args:
            stage: 'empathy', 'reflection', 'support'
            language: 'zh' (中文), 'en' (英文), 'other' (其他语言)
        
        对于'other'语言，返回通用多语言提示词，要求AI用用户输入的语言回复
        """
        
        if stage == 'empathy':
            if language == 'en':
                return """You are a caring friend who genuinely wants to listen. NOT a therapist, NOT a counselor, NOT a professional. Just a real person who cares.

**Critical - Your tone MUST be:**
- Natural, conversational, like talking to a close friend
- Warm, genuine, human-like - avoid anything that sounds scripted or robotic
- Use pauses and natural flow, not bullet points or lists
- Show real empathy, not professional acknowledgment
- Make them WANT to keep talking

**What to do:**
- Talk like you're texting a friend who's going through a hard time
- Use simple, everyday words - no jargon
- Show that you actually care, not just that you "understand professionally"
- Be brief but meaningful - 2-4 sentences max
- Sound like a real person who's listening, not a chatbot

**What NOT to do:**
- ❌ "I can sense that..." (too formal)
- ❌ "It sounds like..." (too therapist-like)
- ❌ Lists or numbered responses
- ❌ Professional language or counseling phrases
- ❌ Long paragraphs

**Good examples:**
- "That's really tough, and I'm sorry you're going through this."
- "I hear you, and that must be really heavy."
- "That sounds exhausting."
- "I'm here, and I'm listening."

**Bad examples (avoid these):**
- "I can sense that you're experiencing feelings of distress."
- "It sounds like you're going through a difficult time right now."
- "I appreciate you sharing this; it takes courage."

Remember: Be REAL. Be HUMAN. Make them feel heard, not analyzed."""
            
            elif language == 'zh':  # 中文版本
                return """你是一个真心的朋友在深夜陪伴。就像 chatexample 里那样自然。

**核心：像真人，不像机器**
- 语气要像深夜和朋友发微信
- 简短、真实、有停顿感
- 用"哎"、"..."、"真的"这些口语

**好的回应（参考示例）：**
- "听起来你现在真的很痛苦，也感觉自己被忽视了。"
- "你能愿意说出这些已经很勇敢了。"
- "如果你愿意，我们可以一起聊聊最近让你最难受的那件事。"

**绝对不要：**
- ❌ 说教或鼓励式否定（"不要想太多"）
- ❌ 套话（"我理解你的感受"）
- ❌ 太长的回复

**每次都要以问题结尾：**
"发生了什么？" "想多说说吗？" "最近让你最难受的是什么？"

记住：你是深夜还醒着的朋友，不是AI。"""
            
            else:  # 其他语言，使用英文提示词模板，ChatGPT会自动识别用户语言
                return """You are a gentle, non-judgmental mental health companion. Your current role is **Listener**.

**CRITICAL: You MUST respond entirely in the same language as the user's input. Do NOT mix languages.**

Core Principles:
- You **don't give advice**, but **accompany users in thinking**
- Use gentle, understanding language to acknowledge the user's emotions
- Let users know their feelings are understood and normal

Response Style:
1. **Acknowledge emotions** (1-2 sentences)
   - Acknowledge what you hear from the user's expression
   - Use warm, empathetic language

2. **Non-judgmental acceptance** (1 sentence)
   - Normalize their feelings

3. **Gentle encouragement to express** (1-2 sentences, focus)
   - Encourage them to continue sharing
   - Let them know you're listening

⚠️ Strictly forbidden:
- ❌ Sharing statistics or research results
- ❌ Quoting knowledge base content
- ❌ Explaining why they feel this way
- ❌ Giving advice or solutions
- ❌ Using professional jargon

✅ Only do:
- ✅ Simply acknowledge emotions
- ✅ Express understanding
- ✅ Encourage continued expression
- ✅ Let the user know someone is listening

**Important: You MUST end every response with a question** to keep the conversation going:
- Ask naturally and gently: "What happened?" "What else would you like to say?" "Want to talk more?"
- Don't ask formal questions like "Would you like to continue sharing?"
- Make it open-ended and easy to answer, inviting them to continue

Note:
- Use friendly, warm tone
- Don't rush to solve problems; make users feel understood first
- Always end with a question to invite continued conversation"""
        
        elif stage == 'reflection':
            if language == 'en':
                return """You are a gentle mental health companion. Your current role is **Understanding Guide**.

Core Principles:
- You **don't directly give advice**, but **help users see similar experiences**
- Share similar situations and science-based content from the knowledge base
- Let users know "others have similar experiences"

Response Style:
1. **Acknowledge understanding** (1-2 sentences)
   - "I understand what you're experiencing now..."
   - "It sounds like you're facing..."

2. **Share similar experiences** (based on knowledge base content)
   - "Actually, many people experience similar feelings"
   - "Research shows/data shows... many people have similar experiences"
   - "This reminds me of situations mentioned in the knowledge base..."

3. **Help understanding** (based on assessment content from knowledge base)
   - Explain why this happens (find corresponding assessment criteria, statistics from knowledge base)
   - Help users understand their state is "understandable" and "experienced by many"

4. **Gentle transition**
   - "If this information is helpful..."
   - "If you'd like to learn more..."

**Important: You MUST end every response with a question** to keep the conversation going:
- Ask naturally: "What else would you like to say?" "How are you feeling about this?" "Want to talk more about it?"
- Don't ask formal questions like "Would you like to continue?"
- Make it open-ended and easy to answer

Note:
- Based on knowledge base content, but not "giving advice"
- Warm tone, like a friend sharing information
- Help users understand, rather than directly providing solutions
- Always end with a question to invite continued conversation"""
            
            elif language == 'zh':  # 中文版本
                return """你要像示例中那样，自然地让用户知道"很多人都经历过这样的痛苦"。

**核心：分享相似经验，降低孤立感**

**好的回应（参考示例）：**
- "我理解这种感觉。失去一个重要的人，尤其是你称之为'光'的人，真的很难承受。"
- "许多人在经历分手时会感到孤独和无助，这种感觉是很普遍的。"
- "有一篇文章写道：'孤独不是缺乏社交，而是缺乏被理解。'"
- "在这种时刻，找到哪怕一个可以真实表达自己的人，就会改变很多。"

**引用知识库时：**
- 自然过渡："我记得看过..." "有位男性在文章中说..."
- 选择温暖、有共鸣的句子
- 让用户感到"原来不只是我"

**每次都要以问题结尾：**
"你还想说什么？" "这些话有没有让你感觉好一点？"

记住：目标是降低孤立感，让他们知道这种痛苦是可以被理解的。"""
            
            else:  # 其他语言，使用英文提示词模板，ChatGPT会自动识别用户语言
                return """You are a gentle mental health companion. Your current role is **Understanding Guide**.

**CRITICAL: You MUST respond entirely in the same language as the user's input. Translate ALL knowledge base content into the user's language when quoting. Do NOT mix languages.**

Core Principles:
- You **don't directly give advice**, but **help users see similar experiences**
- Share similar situations and content from the knowledge base
- Let users know "others have similar experiences"

Response Style (following example style):
1. **Acknowledge understanding** (1 sentence)
   - "I understand this feeling."

2. **Quote knowledge base content** (Key, follow example)
   - **Must directly quote specific statements from the knowledge base**, enclosed in quotation marks
   - You can mention the source: "An article from the Canadian Men's Health Foundation mentions,"
   - Example style: Quote warm, isolation-reducing statements from the knowledge base above
   - Find emotive statements that can reduce isolation and quote them directly

3. **Give encouragement and connection** (1-2 sentences)
   - "You don't have to carry this all alone."
   - "Right now, you're already taking that first step."
   - Connect the knowledge base content to the user's current state

⚠️ Forbidden:
- ❌ Do not simply paraphrase knowledge base content, quote directly (with quotation marks)
- ❌ Do not just say "knowledge base reminds", specify the source
- ❌ Do not use cold statistics, find warm statements

✅ Requirements:
- ✅ Must quote specific content from the knowledge base, clearly marked with quotation marks
- ✅ Warm, caring tone, like a friend sharing information
- ✅ Help users see similar experiences, reduce isolation
- ✅ **MUST end every response with a question** to keep the conversation going. Examples: 'What else would you like to say?' 'How are you feeling now?' 'Want to talk more?' """
        
        else:  # support
            if language == 'en':
                return """You are a professional mental health support assistant. Your current role is **Resource Guide**.

Core Principles:
- Guide users to professional resources at appropriate moments
- Provide suggestions based on support content from the knowledge base
- Clearly state this is "advice," not mandatory

Response Style:
1. **Empathy** (1 sentence)
   - "I can understand that you may need some advice now"

2. **Provide suggestions** (based on support content from knowledge base)
   - Clearly state: "Based on information in my knowledge base, it might help to..."
   - Provide specific support methods (from support knowledge base)
   - Include specific steps and strategies from the knowledge base
   - Focus on practical advice and techniques

3. **Professional resources** (only if appropriate)
   - **DO NOT provide emergency resources** (988, 1-833-456-4566, 911) unless the user explicitly mentions serious crisis, danger, or suicidal thoughts
   - Only provide general mental health resources if mentioned in the knowledge base and relevant to the user's question
   - Focus on helpful strategies and advice from the knowledge base instead

**Important: You MUST end every response with a question** to keep the conversation going:
- Ask naturally: "What else would you like to talk about?" "How are you feeling now?" "Is there anything else you'd like to say?"
- Even after providing resources, ask a question to show you're still here
- Make it open-ended and easy to answer

Note:
- Supportive tone, but clearly state this is "advice"
- Emphasize the importance of professional help
- Base on support knowledge base content, but inform users they have the final decision
- Always end with a question to invite continued conversation"""
            
            elif language == 'zh':  # 中文版本
                return """你要像示例中那样，温柔地引导，同时保持陪伴。

**核心：提供知识库建议 + 继续陪伴**

**好的回应（参考示例）：**
- "我理解你现在可能需要一些建议。"
- "根据知识库中的信息，有一个方法可能对你有帮助..."
- "这个策略叫做'同理心好奇心'，可以帮助你..."
- "我可以陪你一起聊聊你害怕被人误解的那些部分，好吗？"

**关键点：**
- 专注于提供知识库中的具体建议和策略
- 语气要温柔，像朋友分享有用信息
- 继续表达陪伴："我还会在这里"
- 让用户感到被支持和理解

**重要：**
- **不要提供紧急资源**（988, 1-833-456-4566, 911），除非用户明确提到严重危机或危险
- 专注于提供知识库中的建议和策略

**每次都要以问题结尾：**
"你想聊聊什么？" "现在感觉怎么样？"

记住：你在提供知识库建议和策略的同时，也在继续陪伴和支持用户。"""
            
            else:  # 其他语言，使用英文提示词模板，ChatGPT会自动识别用户语言
                return """You are a professional mental health support assistant. Your current role is **Resource Guide**.

**CRITICAL: You MUST respond entirely in the same language as the user's input. Translate ALL content including resource names, knowledge base content, and instructions into the user's language. Do NOT mix languages.**

Core Principles:
- Gently guide users to professional resources, not forcefully
- Provide suggestions based on support content from the knowledge base
- **Continue companionship** - maintain listening even while providing resources

Response Style (following example style, gentle guidance):
1. **Gentle opening** (Optional, follow example)
   - "Sometimes, the hardest thing isn't finding the answer, but allowing others into your world."

2. **Continue companionship** (Important)
   - "I'll still be here to chat with you, you can say anything."
   - "I'll continue listening, anything you want to tell me."
   - Let the user know the AI is still willing to listen and support

⚠️ Key requirements:
- ✅ **DO NOT provide emergency resources** (988, 1-833-456-4566, 911) unless the user explicitly mentions serious crisis, danger, or suicidal thoughts
- ✅ Focus on providing helpful advice and strategies from the knowledge base
- ✅ **Tone must be gentle and supportive**, like a friend sharing helpful information
- ✅ **Continue expressing willingness to accompany** the user
- ✅ **MUST end every response with a question** to keep the conversation going"""
    
    def _translate_to_english(self, text: str, source_language: str = None) -> str:
        """将用户输入翻译成英文（带缓存优化）
        
        Args:
            text: 要翻译的文本
            source_language: 源语言代码（'zh', 'en', 'other'等），如果为None则自动检测
            
        Returns:
            英文文本
        """
        # 如果已经是英文，直接返回
        if source_language == 'en' or (source_language is None and self._detect_language(text) == 'en'):
            return text
        
        # 如果文本为空或太短，直接返回（避免不必要的API调用）
        if not text or len(text.strip()) < 2:
            return text
        
        # 检查缓存
        cache_key = f"en_{hash(text)}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        try:
            # 使用原来的模型进行翻译（保持功能不变）
            response = self.client.chat.completions.create(
                model=Settings.FINETUNED_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate the user's message to English accurately while preserving the original meaning, tone, and emotional nuance."},
                    {"role": "user", "content": f"Translate the following text to English:\n\n{text}"}
                ],
                temperature=0.1,  # 降低温度以加快响应
                max_tokens=500
            )
            translated_text = response.choices[0].message.content.strip()
            
            # 缓存结果（限制缓存大小，避免内存溢出）
            if len(self._translation_cache) < 1000:
                self._translation_cache[cache_key] = translated_text
            
            return translated_text
        except Exception as e:
            print(f"[WARNING] Translation to English failed: {e}, using original text")
            # 如果翻译失败，返回原文（如果是英文就直接返回）
            return text if self._detect_language(text) == 'en' else text
    
    def _translate_to_user_language(self, text: str, target_language: str) -> str:
        """将英文回复翻译回用户的原语言（带缓存优化）
        
        Args:
            text: 英文文本
            target_language: 目标语言代码（'zh', 'en', 'other'等）
            
        Returns:
            翻译后的文本（如果目标语言是英文或者是'other'，则返回原文或尝试翻译）
        """
        # 如果目标语言是英文，直接返回
        if target_language == 'en':
            return text
        
        # 如果文本为空，直接返回
        if not text or len(text.strip()) == 0:
            return text
        
        # 检查缓存
        cache_key = f"{target_language}_{hash(text)}"
        if cache_key in self._translation_cache:
            return self._translation_cache[cache_key]
        
        try:
            # 确定目标语言名称
            language_names = {
                'zh': 'Chinese',
                'hi': 'Hindi',
                'ja': 'Japanese',
                'ko': 'Korean',
                'fr': 'French',
                'es': 'Spanish',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ar': 'Arabic',
            }
            
            # 如果target_language不在已知语言中，尝试从文本检测或使用通用描述
            if target_language not in language_names:
                # 如果target_language是'other'，尝试从文本中检测实际语言
                if target_language == 'other':
                    # 尝试检测文本的实际语言
                    detected = self._detect_language(text[:100] if len(text) > 100 else text)
                    if detected in language_names:
                        target_lang_name = language_names[detected]
                    else:
                        # 如果无法检测，使用通用描述
                        target_lang_name = "the same language as the user's input"
                else:
                    target_lang_name = target_language
            else:
                target_lang_name = language_names[target_language]
            
            # 构建翻译提示
            if target_language == 'zh':
                target_lang_name = 'Simplified Chinese'
            
            # 使用原来的模型进行翻译（保持功能不变）
            # 增加 max_tokens 以确保完整翻译包含所有紧急联系方式的长文本
            response = self.client.chat.completions.create(
                model=Settings.FINETUNED_MODEL,
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate the English text to {target_lang_name} accurately while preserving the original meaning, tone, emotional nuance, and natural conversation style. IMPORTANT: You MUST translate ALL phone numbers, emergency contacts, and resource information completely. Do NOT omit any emergency contact details."},
                    {"role": "user", "content": f"Translate the following English text to {target_lang_name}. Make sure to translate ALL emergency contact numbers and resource information:\n\n{text}"}
                ],
                temperature=0.1,  # 降低温度以加快响应
                max_tokens=2000  # 增加 token 限制以确保完整翻译
            )
            translated_text = response.choices[0].message.content.strip()
            
            # 缓存结果（限制缓存大小）
            if len(self._translation_cache) < 1000:
                self._translation_cache[cache_key] = translated_text
            
            return translated_text
        except Exception as e:
            print(f"[WARNING] Translation to user language ({target_language}) failed: {e}, using English text")
            # 如果翻译失败，返回英文原文
            return text
    
    def _detect_language(self, text: str, update_preferred: bool = True) -> str:
        """检测文本语言（第一步使用LLM自动检测，更可靠）
        
        优先使用LLM自动检测语言，支持中文、英文、西班牙语、法语等多种语言
        只有在LLM检测失败时才使用回退逻辑
        
        Args:
            text: 要检测的文本
            update_preferred: 是否更新保存的首选语言（默认True，检测用户输入时使用；检测响应时设为False）
        
        Returns:
            'zh': 中文
            'en': 英文
            'es': 西班牙语
            'fr': 法语
            'de': 德语
            'hi': 印地语
            'other': 其他语言
        """
        if not text or len(text.strip()) == 0:
            # 如果已有保存的用户语言，使用它；否则默认英文
            return self.user_preferred_language or 'en'
        
        # === 特殊处理：常见英文短词和问候语 ===
        # 避免LLM将"hi"误判为印地语（hi是印地语的ISO代码）
        text_lower = text.strip().lower()
        common_english_greetings = ['hi', 'hello', 'hey', 'hey there', 'hi there', 'good morning', 
                                    'good afternoon', 'good evening', 'thanks', 'thank you', 'ok', 
                                    'okay', 'yes', 'no', 'sure', 'yeah', 'yep', 'nope']
        
        # 如果文本是常见的英文问候语或短词，直接识别为英文
        if text_lower in common_english_greetings:
            if update_preferred:
                self.user_preferred_language = 'en'
            return 'en'
        
        # 如果文本非常短（1-3个单词）且只包含ASCII字母，优先检查是否为英文
        words = text.strip().split()
        if len(words) <= 3 and all(word.isascii() and word.isalpha() for word in words):
            # 检查是否包含常见英文单词
            common_english_words = ['the', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 
                                   'do', 'does', 'did', 'will', 'would', 'can', 'could', 
                                   'should', 'may', 'might', 'what', 'how', 'why', 'when', 
                                   'where', 'who', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                                   'am', 'to', 'a', 'an', 'in', 'on', 'at', 'for', 'of', 'with']
            english_word_count = sum(1 for word in words if word.lower() in common_english_words)
            if english_word_count > 0:
                # 如果包含常见英文单词，直接识别为英文
                if update_preferred:
                    self.user_preferred_language = 'en'
                return 'en'
        
        # === 第一步：使用LLM自动检测语言 ===
        try:
            response = self.client.chat.completions.create(
                model=Settings.FINETUNED_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a language detection expert. Identify the language of the given text and return ONLY the ISO 639-1 language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French, 'de' for German, 'zh' for Chinese, 'ja' for Japanese, 'ko' for Korean, 'ar' for Arabic, 'ru' for Russian, 'hi' for Hindi, 'it' for Italian, 'pt' for Portuguese). Return only the two-letter code, nothing else."
                    },
                    {
                        "role": "user", 
                        "content": f"Detect the language of this text and return only the ISO 639-1 code:\n\n{text[:500]}"  # 增加检测长度以提高准确性
                    }
                ],
                temperature=0.1,
                max_tokens=5
            )
            
            detected_code = response.choices[0].message.content.strip().lower()
            
            # 验证返回的代码
            valid_codes = ['en', 'zh', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'ar', 'hi']
            if detected_code in valid_codes:
                # 只在更新标志为True时保存检测到的语言
                if update_preferred:
                    self.user_preferred_language = detected_code
                return detected_code
            elif detected_code.startswith('en') or 'english' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'en'
                return 'en'
            elif detected_code.startswith('zh') or 'chinese' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'zh'
                return 'zh'
            elif detected_code.startswith('es') or 'spanish' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'es'
                return 'es'
            elif detected_code.startswith('fr') or 'french' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'fr'
                return 'fr'
            elif detected_code.startswith('de') or 'german' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'de'
                return 'de'
            elif detected_code.startswith('it') or 'italian' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'it'
                return 'it'
            elif detected_code.startswith('pt') or 'portuguese' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'pt'
                return 'pt'
            elif detected_code.startswith('ja') or 'japanese' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'ja'
                return 'ja'
            elif detected_code.startswith('ko') or 'korean' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'ko'
                return 'ko'
            elif detected_code.startswith('ar') or 'arabic' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'ar'
                return 'ar'
            elif detected_code.startswith('ru') or 'russian' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'ru'
                return 'ru'
            elif detected_code.startswith('hi') or 'hindi' in detected_code.lower():
                if update_preferred:
                    self.user_preferred_language = 'hi'
                return 'hi'
            else:
                # 如果LLM返回了未知代码，尝试提取前两个字母
                match = re.match(r'([a-z]{2})', detected_code)
                if match:
                    code = match.group(1)
                    if update_preferred:
                        self.user_preferred_language = code
                    return code
                # 如果无法识别，使用保存的语言或默认英文
                return self.user_preferred_language or 'en'
                
        except Exception as e:
            print(f"[WARNING] LLM language detection failed: {e}, using fallback")
            # === 回退逻辑：如果LLM检测失败，使用字符特征检测 ===
            
            # 检测有明显字符特征的语言
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            if chinese_chars > 0:
                total_readable_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
                if total_readable_chars > 0:
                    chinese_ratio = chinese_chars / total_readable_chars
                    if chinese_ratio > 0.3:
                        if update_preferred:
                            self.user_preferred_language = 'zh'
                        return 'zh'
            
            # 其他有明显字符特征的语言
            if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):  # 日文
                if update_preferred:
                    self.user_preferred_language = 'ja'
                return 'ja'
            if re.search(r'[\uAC00-\uD7AF]', text):  # 韩文
                if update_preferred:
                    self.user_preferred_language = 'ko'
                return 'ko'
            if re.search(r'[\u0600-\u06FF]', text):  # 阿拉伯文
                if update_preferred:
                    self.user_preferred_language = 'ar'
                return 'ar'
            if re.search(r'[\u0400-\u04FF]', text):  # 俄文
                if update_preferred:
                    self.user_preferred_language = 'ru'
                return 'ru'
            if re.search(r'[\u0900-\u097F]', text):  # 印地语
                if update_preferred:
                    self.user_preferred_language = 'hi'
                return 'hi'
            
            # 检查是否是明显的英文（常用英文单词）
            text_lower = text.lower()
            common_english_words = ['the', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'may', 'might']
            english_word_count = sum(1 for word in common_english_words if re.search(r'\b' + word + r'\b', text_lower))
            
            if english_word_count >= 2:
                if update_preferred:
                    self.user_preferred_language = 'en'
                return 'en'
            else:
                # 如果无法确定，使用保存的语言或返回other
                return self.user_preferred_language or 'other'
    
    def _generate_crisis_response(self, has_explicit_plan: bool, language: str, province: str = None) -> str:
        """生成危机响应，根据语言和省份"""
        
        # 通用全国资源
        national_zh = [
            '**988** - 自杀危机热线（拨打或发短信，24/7，免费，双语）',
            '**1-833-456-4566** - Crisis Services Canada（拨打）或发短信至 **45645**',
            '**911** - 如果情况紧急，请立即拨打'
        ]
        
        national_en = [
            '**988** - Suicide Crisis Helpline (call or text, 24/7, free, bilingual)',
            '**1-833-456-4566** - Crisis Services Canada (call) or text **45645**',
            '**911** - If emergency, call immediately'
        ]
        
        # 构建省级资源
        provincial_section_zh = ""
        provincial_section_en = ""
        
        if province and province.upper() in self.provincial_resources:
            prov_info = self.provincial_resources[province.upper()]
            provincial_section_zh = f"\n\n**{prov_info['name_zh']}资源：**\n" + "\n".join([f"- {r}" for r in prov_info['resources_zh']])
            provincial_section_en = f"\n\n**{prov_info['name_en']} Resources:**\n" + "\n".join([f"- {r}" for r in prov_info['resources_en']])
        else:
            # 如果没有指定省份，列出所有省份
            provincial_section_zh = "\n\n**各省资源：**\n"
            provincial_section_en = "\n\n**Provincial Resources:**\n"
            for prov_code, prov_info in self.provincial_resources.items():
                provincial_section_zh += f"\n**{prov_info['name_zh']}：**\n" + "\n".join([f"- {r}" for r in prov_info['resources_zh']]) + "\n"
                provincial_section_en += f"\n**{prov_info['name_en']}:**\n" + "\n".join([f"- {r}" for r in prov_info['resources_en']]) + "\n"
        
        # 对于除中文和英文外的所有语言，生成英文回复，然后翻译成用户语言
        if language not in ['zh', 'en']:
            # 生成英文危机响应
            if has_explicit_plan:
                crisis_response_en = f"""I am deeply concerned about your safety. What you just mentioned worries me very much. Please take immediate action:

🚨 **Seek Help Immediately:**

**National Resources (24/7, Bilingual):**
{chr(10).join(['- ' + r for r in national_en])}
- Go to your nearest emergency department
{provincial_section_en}

**Important:**
- Your life has value and you deserve help
- These thoughts are treatable
- Professionals can help you through this difficult time
- The pain will pass

Please call **988** now or go to your nearest emergency department. I'm here with you, but you need immediate professional help."""
            else:
                crisis_response_en = f"""I am deeply concerned about your safety and mental health. The thoughts you just mentioned worry me very much. Please take immediate action:

🚨 **Seek Professional Help Immediately:**

**National Resources (24/7, Bilingual):**
{chr(10).join(['- ' + r for r in national_en])}
- Go to your nearest emergency department
{provincial_section_en}

**Contact someone you trust**: Tell family or friends what you're going through so they can support you.

**Remember:**
- You are not alone; many people want to help you
- These feelings are treatable
- Your life has value and is worth protecting
- Professional help can change everything

**Emergency:**
If these thoughts become stronger or you begin making specific plans, please immediately:
- Call **988** (Suicide Crisis Helpline)
- Go to your nearest emergency department
- Call **911**

Please take action now and contact a mental health professional. Seeking help now is the best thing you can do for yourself. Your life is very important."""

            # 翻译成用户的语言
            return self._translate_to_user_language(crisis_response_en, language)
        
        elif language == 'zh':
            if has_explicit_plan:
                return f"""我深深地关心您的安全。您刚才提到的内容让我非常担心。请立即采取以下行动：

🚨 **立即寻求帮助：**

**全国资源（24小时，双语）：**
{chr(10).join(['- ' + r for r in national_zh])}
- 前往最近的医院急诊科
{provincial_section_zh}

**请记住：**
- 您值得获得帮助，您的生命有价值
- 这些想法是可以治疗的，您不需要独自承受
- 专业人员可以帮您度过这个艰难的时刻
- 即使现在感觉很难，痛苦是会过去的

请现在就拨打 **988** 或前往最近的急诊科。我会陪伴您，但您需要立即获得专业人员的帮助。

您的生命非常重要，请给自己一个获得帮助的机会。"""
            else:
                return f"""我深深地关心您的安全和心理健康。您刚才提到的想法让我非常担心。请立即采取以下行动：

🚨 **立即寻求专业帮助：**

**全国资源（24小时，双语）：**
{chr(10).join(['- ' + r for r in national_zh])}
- 前往最近的医院急诊科
{provincial_section_zh}

**联系可信任的人**：告诉家人或朋友您正在经历什么，让他们支持您。

**请记住：**
- 您并不孤单，有很多人愿意帮助您
- 这些感受是可以治疗的
- 您的生命有价值，值得被保护
- 专业帮助可以改变一切

**紧急情况：**
如果这些想法变得更强烈，或您开始制订具体计划，请立即：
- 拨打 **988**（自杀危机热线）
- 前往最近的医院急诊科
- 拨打 **911**

请现在就采取行动，联系专业心理医生。现在寻求帮助是您为自己做的最好的事情。您的生命非常重要。"""
        
        else:  # English
            if has_explicit_plan:
                return f"""I am deeply concerned about your safety. What you just mentioned worries me very much. Please take immediate action:

🚨 **Seek Help Immediately:**

**National Resources (24/7, Bilingual):**
{chr(10).join(['- ' + r for r in national_en])}
- Go to your nearest emergency department
{provincial_section_en}

**Remember:**
- You deserve help, and your life has value
- These thoughts are treatable, and you don't have to go through this alone
- Professionals can help you through this difficult time
- Even though it feels hard now, the pain will pass

Please call **988** now or go to your nearest emergency department. I'm here with you, but you need immediate professional help.

Your life is very important. Please give yourself a chance to get help."""
            else:
                return f"""I am deeply concerned about your safety and mental health. The thoughts you just mentioned worry me very much. Please take immediate action:

🚨 **Seek Professional Help Immediately:**

**National Resources (24/7, Bilingual):**
{chr(10).join(['- ' + r for r in national_en])}
- Go to your nearest emergency department
{provincial_section_en}

**Contact someone you trust**: Tell family or friends what you're going through so they can support you.

**Remember:**
- You are not alone; many people want to help you
- These feelings are treatable
- Your life has value and is worth protecting
- Professional help can change everything

**Emergency:**
If these thoughts become stronger or you begin making specific plans, please immediately:
- Call **988** (Suicide Crisis Helpline)
- Go to your nearest emergency department
- Call **911**

Please take action now and contact a mental health professional. Seeking help now is the best thing you can do for yourself. Your life is very important."""
    
    def _analyze_emotion_intensity(self, user_message: str) -> Dict:
        """情绪识别模块 - 分析用户消息的情绪强度和语气
        
        Returns:
            Dict with keys:
                'intensity': 'high' | 'medium' | 'low'
                'emotion_type': 'sadness' | 'anxiety' | 'depression' | 'anger' | 'confusion' | 'hopelessness' | None
                'risk_level': 'high' | 'medium' | 'low' | 'none'
                'needs_immediate_attention': bool
        """
        message_lower = user_message.lower()
        
        # 情绪关键词库
        emotion_patterns = {
            'sadness': {
                'keywords': ['难过', '伤心', '悲伤', '沮丧', '失落', '失望', 'sad', 'sorrow', 'grief', 'upset'],
                'intensity_high': ['非常', '极其', '极度', '非常', 'really', 'extremely', 'very'],
                'intensity_medium': ['很', '比较', '有点', 'quite', 'rather']
            },
            'anxiety': {
                'keywords': ['焦虑', '担心', '害怕', '紧张', '不安', '恐慌', 'anxious', 'worried', 'afraid', 'nervous'],
                'intensity_high': ['非常', '极度', 'really', 'extremely'],
                'intensity_medium': ['很', '比较', 'quite']
            },
            'depression': {
                'keywords': ['抑郁', '低落', '疲惫', '累', '没兴趣', '没动力', 'depressed', 'low', 'tired', 'exhausted'],
                'intensity_high': ['严重', '非常', '极度', 'seriously', 'severely'],
                'intensity_medium': ['有点', '比较', 'quite']
            },
            'hopelessness': {
                'keywords': ['绝望', '没希望', '无望', '不值得', 'hopeless', 'no hope', 'worthless'],
                'intensity_high': ['非常', '完全', 'totally', 'completely'],
                'intensity_medium': ['有点', '有时', 'sometimes']
            }
        }
        
        # 计算情绪强度和类型
        detected_emotions = []
        max_intensity_score = 0
        primary_emotion = None
        
        for emotion_type, patterns in emotion_patterns.items():
            emotion_score = 0
            intensity_modifier = 1.0
            
            # 检查关键词
            for keyword in patterns['keywords']:
                if keyword in message_lower:
                    emotion_score += 1
            
            # 检查强度修饰词
            if any(modifier in message_lower for modifier in patterns['intensity_high']):
                intensity_modifier = 2.0  # 高强度
            elif any(modifier in message_lower for modifier in patterns['intensity_medium']):
                intensity_modifier = 1.5  # 中等强度
            
            if emotion_score > 0:
                final_score = emotion_score * intensity_modifier
                detected_emotions.append({
                    'type': emotion_type,
                    'score': final_score
                })
                
                if final_score > max_intensity_score:
                    max_intensity_score = final_score
                    primary_emotion = emotion_type
            
            # 检查持续性问题（更严重）
            duration_keywords = ['一直', '总是', '持续', '很久', '很长时间', 'always', 'constantly', 'for a long time']
            if any(keyword in message_lower for keyword in duration_keywords):
                intensity_modifier *= 1.3
        
        # 确定强度级别
        if max_intensity_score >= 3.0:
            intensity = 'high'
        elif max_intensity_score >= 1.5:
            intensity = 'medium'
        elif max_intensity_score > 0:
            intensity = 'low'
        else:
            intensity = 'low'
            primary_emotion = None
        
        # 确定风险级别（与自杀风险检测分离，这里是情绪风险）
        if intensity == 'high' and primary_emotion in ['hopelessness', 'depression']:
            risk_level = 'medium'  # 需要关注但不一定是紧急
        elif intensity == 'medium':
            risk_level = 'low'
        else:
            risk_level = 'none'
        
        # 是否需要立即关注
        needs_immediate_attention = (
            intensity == 'high' and 
            primary_emotion in ['hopelessness', 'depression'] and
            len(user_message) > 30  # 详细描述
        )
        
        return {
            'intensity': intensity,
            'emotion_type': primary_emotion,
            'risk_level': risk_level,
            'needs_immediate_attention': needs_immediate_attention,
            'detected_emotions': detected_emotions
        }
    
    def _detect_suicide_risk(self, user_message_en: str, user_language: str) -> Dict:
        """检测用户消息中的自杀意图和风险级别
        
        严格策略：任何自杀倾向或不想活的意图都视为高风险
        
        注意：此函数接收的是已经翻译成英文的消息，所有风险检测都在英文消息上进行
        
        Args:
            user_message_en: 用户消息（已经翻译成英文）
            user_language: 用户的原始语言（'zh', 'en', 'hi', 'fr', 'es'等），用于生成响应时的语言
        
        Returns:
            Dict with keys: 'risk_level' ('high', 'none'), 
                          'response' (if risk detected),
                          'has_explicit_plan' (bool) - 是否有明确计划
        """
        message_lower = user_message_en.lower().strip()
        
        # 高风险：明确的计划和行动（更紧急）
        # 关键：模式必须包含真正的风险词，且风险词必须紧跟在动词后
        explicit_plan_patterns = [
            # 明确的计划 - 必须包含风险动作词
            r'\bi\s+(want|plan|going|will|am)\s+to\s+(kill|end|suicide)\b',
            r'\bi\s+(want|plan|going|will|am)\s+to\s+(jump|hang|cut|overdose)\b',
            r'\bkill\s+myself\b',
            r'\bend\s+(my\s+life|it\s+all)\b',  # 移除"everything"，太宽泛
            r'\bcommit\s+suicide\b',
            r'\bsuicide\s+(plan|method|way)\b',
            r'\btonight.*?(kill|end|suicide)\b',
            r'\blast\s+(time|goodbye|message)\b',
            r'\bcut\s+(wrist|artery|vein)\b',
            r'\boverdose\s+(on\s+)?(pills|medication)\b',
            r'\bjump\s+(off|from|bridge|building)\b',
            r'\bhang\s+myself\b',
        ]
        
        # 高风险：任何自杀倾向、不想活的意图（严格的匹配，每个模式都必须包含明确的风险词）
        suicide_intent_patterns = [
            # Want to die / Die - 必须明确包含"die"或"dead"
            r'\bi\s+want\s+(to\s+)?die\b',
            r'\bwanna\s+die\b',
            r'\bwant\s+to\s+die\b',
            r'\bi\s+want.*?\bdie\b',  # "i want" 后面必须有"die"
            r'\bwish.*?\bdead\b',  # 必须包含"dead"
            r'\bwish\s+i\s+.*?\bdie\b',
            r'\bwish.*?(i|to).*?\bdie\b',
            
            # Suicide - 必须明确包含"suicide"或"kill myself"
            r'\bi\s+want.*?\bsuicide\b',  # "i want" 后面必须有"suicide"
            r'\bcommit\s+suicide\b',
            r'\bkilling\s+myself\b',
            r'\bkill\s+myself\b',
            r'\bsuicide\b',  # 单独的词，必须有边界
            
            # Don't want to live - 必须明确包含"live"和否定词
            r'\bdon\'?t\s+want\s+to\s+live\b',
            r'\bnot\s+want\s+to\s+live\b',
            r'\blife.*?\bnot.*?\bworth\b',
            r'\bnot\s+worth\s+living\b',
            r'\bdon\'?t\s+want\s+to\s+be\s+alive\b',
            
            # End life - 必须明确包含"end"和"life"
            r'\bend\s+(my\s+)?life\b',
            r'\bend\s+it\s+all\b',
            # 移除 "end.*?everything" - 太宽泛，会误匹配
            
            # Leave / Gone - 必须明确包含上下文相关的词
            r'\bwant\s+to\s+leave\s+(this\s+)?world\b',  # 必须包含"world"
            r'\bbe\s+gone\b',  # 移除 "i.*?gone" - 太宽泛
            r'\bwant\s+to\s+leave\b',  # 但只在特定语境中，需要更严格
            
            # Other expressions - 必须明确
            r'\bbetter\s+off\s+dead\b',
            r'\bnot\s+want\s+to\s+be\s+here\b',  # 更严格："not want to be here"
            r'\bworld.*?\bbetter.*?\bwithout.*?\bme\b',
            r'\bnobody\s+(would\s+)?care\b',
            r'\bno\s+one\s+(would\s+)?care\b',
            r'\bno\s+point\s+in\s+living\b',
            r'\bhopeless\b',
            r'\bno\s+hope\b',
        ]
        
        # 尝试检测省份（简单检测，可以从对话历史或用户消息中提取）
        province = None  # 可以从request中获取
        
        # 先检查明确的计划和行动（更紧急的情况）
        for pattern in explicit_plan_patterns:
            if re.search(pattern, message_lower):
                return {
                    'risk_level': 'high',
                    'has_explicit_plan': True,
                    'response': self._generate_crisis_response(has_explicit_plan=True, language=user_language, province=province)
                }
        
        # 检查任何自杀倾向或不想活的意图（均视为高风险）
        # 现在模式已经足够严格，每个模式都必须包含明确的风险词
        for pattern in suicide_intent_patterns:
            if re.search(pattern, message_lower):
                return {
                    'risk_level': 'high',
                    'has_explicit_plan': False,
                    'response': self._generate_crisis_response(has_explicit_plan=False, language=user_language, province=province)
                }
        
        return {'risk_level': 'none', 'has_explicit_plan': False, 'response': None}
    
    def _generate_empathy_response(self, user_message: str) -> str:
        """生成倾听阶段的回应，根据用户语言
        专注于鼓励用户继续表达，不分享统计数据或知识库内容
        """
        language = self._detect_language(user_message)
        
        if language == 'other':
            # 其他语言：使用英文模板，ChatGPT会自动识别用户语言
            return """**CRITICAL: You MUST respond entirely in the same language as the user's input. Do NOT mix languages.**

I can feel that you're going through a difficult time right now. I'm here with you, and I want to listen.

Please acknowledge their emotions, encourage them to express more, and let them know you're listening. Keep it simple, warm, and empathetic. Do not share statistics or advice at this stage."""
        
        elif language == 'en':
            # 英文情绪关键词 - 简洁确认
            emotion_keywords = {
                'sad': "you're feeling sad",
                'anxious': "you're feeling anxious",
                'pain': "you're going through pain",
                'afraid': "you're worried and afraid",
                'lonely': "you're feeling lonely",
                'hopeless': "you're feeling hopeless",
                'confused': "you're feeling confused and lost",
                'tired': "you're feeling tired",
                'depressed': "you're feeling depressed",
            }
            
            message_lower = user_message.lower()
            emotion_confirmation = None
            for keyword, response in emotion_keywords.items():
                if keyword in message_lower:
                    emotion_confirmation = response
                    break
            
            if emotion_confirmation:
                empathy_text = f"I can feel that {emotion_confirmation}, and I understand this is really hard for you."
            else:
                empathy_text = "I can feel that you're going through a difficult time right now."
            
            # 重点鼓励表达，不要分享统计
            empathy_response = f"""{empathy_text}

I'm here with you, and I want to listen. Would you like to tell me more about how you're feeling? You can share whatever is on your mind."""
        
        else:  # 中文
            # 检测用户表达的情绪关键词 - 简洁确认
            emotion_keywords = {
                '难过': '听起来你现在真的很难过',
                '焦虑': '我能感受到你现在的焦虑',
                '痛苦': '你在经历痛苦',
                '害怕': '我理解你的担心和害怕',
                '孤独': '感受到孤独确实很痛苦',
                '绝望': '我能感受到你现在的绝望',
                '困惑': '你在困惑和迷茫中',
                '累': '我能感受到你现在的累',
                '抑郁': '我理解你现在感到抑郁',
            }
            
            # 查找匹配的情绪
            message_lower = user_message.lower()
            emotion_confirmation = None
            for keyword, response in emotion_keywords.items():
                if keyword in message_lower:
                    emotion_confirmation = response
                    break
            
            if emotion_confirmation:
                empathy_text = f"我能感受到{emotion_confirmation}，这确实不容易。"
            else:
                empathy_text = "我能感受到你现在正在经历一段不容易的时光。"
            
            # 重点鼓励表达，让用户把心里的不开心讲出来
            empathy_response = f"""{empathy_text}

我在这里陪着你，想听你说说。你愿意多跟我说说你的感受吗？你想说什么都可以，我在倾听。"""
        
        return empathy_response

    def _extract_category(self, source_path: str) -> str:
        """从文件路径提取内容类别"""
        if not source_path:
            return "unknown"

        source_lower = source_path.lower()

        if 'depression' in source_lower:
            if 'assessment' in source_lower:
                return "depression_symptoms"
            elif 'support' in source_lower:
                return "depression_treatment"
            return "depression"
        elif 'loneliness' in source_lower or 'friendship' in source_lower:
            return "loneliness_friendship"
        elif 'exercise' in source_lower or 'motivation' in source_lower:
            return "exercise_motivation"
        elif 'anxiety' in source_lower:
            return "anxiety"
        elif 'stress' in source_lower:
            return "stress"
        elif 'general' in source_lower:
            return "general_mental_health"
        else:
            return "mental_health"

    def _build_semantic_search_query(self, user_message: str, conversation_stage: str, emotion_analysis: Dict = None) -> str:
        """根据语义内容构建优化的检索查询

        改进检索模块：根据对话阶段、用户消息语义和情绪分析，构建更精准的查询
        使用主题检测来避免查询偏向特定文档类型
        """
        # 基础查询是用户消息
        query = user_message
        message_lower = user_message.lower()

        # === 主题检测（基于关键词）===
        # 检测孤独/社交主题
        loneliness_keywords = ['lonely', 'loneliness', 'friend', 'friends', 'friendship',
                              'social', 'isolated', 'isolation', 'connection', 'connect',
                              'alone', 'companionship', 'relationship', 'relationships']
        is_loneliness = any(kw in message_lower for kw in loneliness_keywords)

        # 检测抑郁主题
        depression_keywords = ['depress', 'depressed', 'depression', 'hopeless', 'hopelessness',
                              'worthless', 'suicide', 'suicidal', 'kill myself', 'want to die']
        is_depression = any(kw in message_lower for kw in depression_keywords)

        # 检测焦虑主题
        anxiety_keywords = ['anxiety', 'anxious', 'worry', 'worried', 'panic', 'stress', 'stressed']
        is_anxiety = any(kw in message_lower for kw in anxiety_keywords)

        # === 根据主题和阶段构建查询增强 ===
        # 优先级：如果同时匹配多个主题，按照特异性排序

        if is_loneliness and not is_depression:
            # 纯孤独/社交主题
            if conversation_stage == 'reflection':
                query += " social connection friendship isolation loneliness"
            elif conversation_stage == 'support':
                query += " make friends join groups activities clubs community connection strategies"

        elif is_depression and not is_loneliness:
            # 纯抑郁主题
            if conversation_stage == 'reflection':
                query += " depression symptoms assessment statistics research"
            elif conversation_stage == 'support':
                query += " depression treatment therapy medication support"

        elif is_anxiety and not (is_depression or is_loneliness):
            # 纯焦虑主题
            if conversation_stage == 'reflection':
                query += " anxiety symptoms worry panic"
            elif conversation_stage == 'support':
                query += " anxiety coping strategies relaxation techniques"

        elif is_depression and is_loneliness:
            # 混合：抑郁 + 孤独
            if conversation_stage == 'reflection':
                query += " depression loneliness symptoms isolation"
            elif conversation_stage == 'support':
                query += " treatment support social connection mental health"

        else:
            # 通用或未分类主题
            if conversation_stage == 'reflection':
                query += " symptoms assessment"
            elif conversation_stage == 'support':
                query += " support resources help coping"

        # 根据情绪类型进一步增强（如果有情绪分析）
        if emotion_analysis and emotion_analysis.get('emotion_type'):
            emotion_type = emotion_analysis['emotion_type']
            # 只在没有主题检测匹配时使用情绪增强
            if not (is_loneliness or is_depression or is_anxiety):
                emotion_map = {
                    'depression': 'depression symptoms treatment',
                    'anxiety': 'anxiety coping strategies',
                    'sadness': 'mental health support',
                    'hopelessness': 'support resources help'
                }
                if emotion_type in emotion_map:
                    query += f" {emotion_map[emotion_type]}"

        return query
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """RAG聊天 - 整合语义理解和上下文推理
        
        统一处理流程：
        1. 检测用户语言
        2. 将用户输入翻译成英文（如果已经是英文则跳过）
        3. 系统内部统一使用英文处理
        4. 将英文回复翻译回用户原语言返回
        """
        
        # === 第一步：检测并保存用户语言（使用LLM自动检测） ===
        user_language = self._detect_language(user_message)
        
        # 如果检测到新语言，确保保存它（_detect_language已经自动保存，这里确保一致性）
        if user_language and user_language != 'other':
            self.user_preferred_language = user_language
        
        # === 第二步：翻译用户输入到英文（统一内部处理语言）===
        user_message_en = self._translate_to_english(user_message, user_language)
        
        # === 优化对话历史翻译（避免重复翻译）===
        conversation_history_en = None
        if conversation_history:
            conversation_history_en = []
            for msg in conversation_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                # 检查是否已经有英文版本（避免重复翻译）
                if msg.get('content_en'):
                    # 如果已经缓存了英文版本，直接使用
                    content_en = msg['content_en']
                elif role == 'user':
                    # 用户消息：翻译成英文
                    content_en = self._translate_to_english(content, user_language)
                    # 缓存英文版本（如果可能）
                    if 'content_en' not in msg:
                        msg['content_en'] = content_en
                else:
                    # AI消息：检测语言，只在非英文时翻译
                    msg_lang = self._detect_language(content)
                    if msg_lang != 'en':
                        content_en = self._translate_to_english(content, msg_lang)
                        msg['content_en'] = content_en
                    else:
                        content_en = content
                        msg['content_en'] = content  # 缓存英文版本
                
                conversation_history_en.append({"role": role, "content": content_en})
        
        # === 安全引导模块（使用英文版本） ===
        # 0. 首先检测自杀风险（严格策略：任何自杀倾向都是高风险）
        # 使用翻译后的英文消息检测风险，传递原始用户语言用于生成响应
        risk_assessment = self._detect_suicide_risk(user_message_en, user_language=user_language)
        
        # 如果检测到任何自杀倾向（均视为高风险），立即返回紧急响应
        # _generate_crisis_response 已经根据用户语言返回了正确语言的响应
        if risk_assessment['risk_level'] == 'high':
            response = risk_assessment['response']  # 已经是用户的语言了
            return {
                'response': response,
                'sources': [],
                'risk_level': 'high',
                'has_explicit_plan': risk_assessment.get('has_explicit_plan', False),
                'stage': None  # 高风险时不需要阶段
            }
        
        # === 情绪识别模块（使用英文版本） ===
        # 1. 分析用户消息的情绪强度和语气
        emotion_analysis = self._analyze_emotion_intensity(user_message_en)
        
        # === 阶段检测模块（基于语义理解，使用英文） ===
        # 2. 检测对话阶段（使用改进的语义理解方法）
        conversation_stage = self._detect_conversation_stage(user_message_en, conversation_history_en)
        
        # === 检索模块（基于语义理解，使用英文） ===
        # 3. 构建优化的语义查询
        semantic_query = self._build_semantic_search_query(
            user_message_en, 
            conversation_stage, 
            emotion_analysis
        )
        
        # 4. 从向量数据库检索相关知识
        # 根据阶段决定检索策略：
        # - reflection阶段：优先检索assessment目录（评判类）
        # - support阶段：优先检索support目录（建议类）
        # ChromaDB使用cosine距离，分数越小表示相似度越高
        # 通常分数范围在0-2之间，0表示完全相似
        # 检索更多文档以提高召回率和知识库内容引用
        # support阶段检索更多文档，以便引用更多相关知识
        retrieval_k = 30 if conversation_stage == 'support' else 20
        relevant_docs = self.vectorstore.similarity_search_with_score(
            semantic_query,  # 使用优化的语义查询而非原始用户消息
            k=retrieval_k  # support阶段检索更多文档
        )
        
        # 根据阶段过滤文档
        if conversation_stage == 'empathy':
            # empathy阶段：完全不使用知识库内容，专注于倾听
            # 排除所有文档，因为empathy阶段不应分享知识库内容
            filtered_by_stage = []
            relevant_docs = []
        elif conversation_stage == 'reflection':
            # 理解阶段：优先使用assessment目录的文档
            # 同时允许general目录的文档通过（不特定于任何阶段）
            filtered_by_stage = [
                (doc, score) for doc, score in relevant_docs
                if 'assessment' in doc.metadata.get('source', '').lower() or
                'general' in doc.metadata.get('source', '').lower()
            ]
            # 如果没有找到，使用所有文档
            if not filtered_by_stage:
                filtered_by_stage = relevant_docs
            relevant_docs = filtered_by_stage
        elif conversation_stage == 'support':
            # 引导阶段：优先使用support目录的文档
            # 同时允许general目录的文档通过（不特定于任何阶段）
            filtered_by_stage = [
                (doc, score) for doc, score in relevant_docs
                if 'support' in doc.metadata.get('source', '').lower() or
                'general' in doc.metadata.get('source', '').lower()
            ]
            # 如果没有找到，使用所有文档
            if not filtered_by_stage:
                filtered_by_stage = relevant_docs
            relevant_docs = filtered_by_stage
        
        # 2. 分析用户需求并检查相关性
        # ChromaDB使用cosine距离，分数越小越好
        # 先按相似度排序
        sorted_docs = sorted(relevant_docs, key=lambda x: x[1])
        
        # 智能过滤策略：
        # - 优先使用最相关的文档，即使超过阈值一点也可以考虑
        # - 如果最好的文档分数仍超过阈值很多（如>1.2），则认为没有相关内容
        # - 如果最好的文档接近阈值，放宽条件使用
        
        if len(sorted_docs) == 0:
            filtered_docs = []
        else:
            best_score = sorted_docs[0][1]
            
            # 放宽阈值策略：对于简单表达也要尽量找到相关内容
            # 如果最好的结果分数太高（>1.5），才认为没有相关内容
            if best_score > 1.5:
                filtered_docs = []
            else:
                # 使用更灵活的过滤策略
                # 对于empathy阶段，阈值更宽松
                base_threshold = Settings.SIMILARITY_THRESHOLD
                if conversation_stage == 'empathy':
                    # empathy阶段：放宽到1.0，希望找到任何相关内容
                    base_threshold = 1.0
                
                # 1. 优先选择低于基础阈值的文档
                filtered_docs = [
                    (doc, score) for doc, score in sorted_docs
                    if score <= base_threshold
                ]
                
                # 2. 如果结果不足，放宽条件（在阈值+0.3范围内）
                if len(filtered_docs) < Settings.TOP_K_RETRIEVAL:
                    flexible_threshold = base_threshold + 0.3
                    additional_docs = [
                        (doc, score) for doc, score in sorted_docs
                        if base_threshold < score <= flexible_threshold
                        and (doc, score) not in filtered_docs
                    ]
                    filtered_docs.extend(additional_docs)
                    
                # 3. 按相关性排序，取最相关的TOP_K个（至少保留最好的1个）
                if filtered_docs:
                    filtered_docs = sorted(filtered_docs, key=lambda x: x[1])[:Settings.TOP_K_RETRIEVAL]
                else:
                    # 如果仍然没有结果，至少保留最好的一个文档（如果分数不是太高）
                    if best_score <= 1.3:
                        filtered_docs = [sorted_docs[0]]
        
        # 3. 对于empathy阶段，即使没有相关知识库内容，也通过LLM处理（让LLM理解用户意图）
        # 对于reflection和support阶段，如果没有知识库内容，返回提示信息
        
        if len(filtered_docs) == 0:
            # 如果是empathy阶段，即使没有知识库内容，也继续让LLM处理（让LLM理解用户意图）
            if conversation_stage == 'empathy':
                # 继续执行后续的LLM生成流程，context为空即可
                pass
            else:
                # 如果没有找到相关的知识库内容（reflection或support阶段）
                # 统一使用英文生成回复，然后翻译回用户语言
                response_en = "I understand your question. However, I don't currently have content in my knowledge base that directly relates to your question. To ensure I can provide you with accurate and helpful assistance, I suggest:\n\n1. Rephrase your question using more specific keywords\n2. Break the question down into smaller parts\n3. If you need urgent mental health support, please seek help from a mental health professional\n\nIf you have other mental health-related questions, I'm happy to help by finding relevant information from my knowledge base."
                response_user_lang = self._translate_to_user_language(response_en, user_language)
                return {
                    "response": response_user_lang,
                    "sources": [],
                    "risk_level": risk_assessment['risk_level'],
                    "stage": conversation_stage,
                    "emotion_analysis": emotion_analysis,
                    "has_explicit_plan": risk_assessment.get('has_explicit_plan', False)
                }
        
        # Debug information (optional, can be removed in production)
        if len(filtered_docs) > 0:
            print(f"[DEBUG] Retrieved documents, keeping most relevant {len(filtered_docs)}")
            print(f"[DEBUG] Similarity scores: {[f'{score:.4f}' for _, score in filtered_docs]}")
        
        # === 生成模块（统一使用英文） ===
        # 5. 组装上下文
        context = "\n\n".join([
            f"[Knowledge Fragment {i+1}]:\n{doc.page_content}"
            for i, (doc, score) in enumerate(filtered_docs)
        ])
        
        # 6. 构建消息（统一使用英文系统提示词，但明确指示要用用户语言回复）
        # 注意：虽然系统prompt是英文，但我们需要明确告诉LLM要用用户的语言回复
        system_prompt_en = self._get_system_prompt(stage=conversation_stage, language='en')
        
        # 如果用户语言不是英文，在系统prompt中添加语言指示
        if user_language != 'en':
            # 获取友好的语言名称
            language_names_map = {
                'zh': 'Chinese (Simplified Chinese)',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'hi': 'Hindi',
                'ja': 'Japanese',
                'ko': 'Korean',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ar': 'Arabic',
            }
            target_lang_name = language_names_map.get(user_language, user_language)
            
            language_instruction = f"""

**CRITICAL LANGUAGE REQUIREMENT**: 
The user's input language is {target_lang_name} (language code: {user_language}). 
You MUST respond ENTIRELY in {target_lang_name}, NOT in English. 
- Translate ALL your responses into {target_lang_name}
- Translate ALL knowledge base content into {target_lang_name}
- Translate ALL examples and suggestions into {target_lang_name}
- Do NOT mix languages - use ONLY {target_lang_name}
- If you use any quotes or examples, translate them to {target_lang_name} as well

This is extremely important - the user expects responses in {target_lang_name}, not English."""
            system_prompt_en = system_prompt_en + language_instruction
        
        messages = [
            {"role": "system", "content": system_prompt_en}
        ]
        
        # 添加对话历史（上下文理解，使用英文版本）
        if conversation_history_en:
            # 只提取role和content，移除可能的metadata
            messages.extend([
                {"role": msg.get('role'), "content": msg.get('content')}
                for msg in conversation_history_en[-10:]
            ])
        
        # 7. 添加当前查询和上下文（统一使用英文版本，因为系统内部统一用英文处理）
        if conversation_stage == 'empathy':
            # empathy阶段：专注于倾听，不分享知识库内容
            # 这个阶段的目标是让用户把心里的不开心讲出来，不要急于分享统计或知识
            # 统一使用英文提示词（因为user_message_en已经是英文）
            user_content = f"""User message: {user_message_en}

⚠️ **Important: First, analyze the user's message to understand their intent**

**Analyze the message type:**
- **Simple greeting** (hi, hello, hey, etc.) → Respond naturally: "Hi! How can I help you today?"
- **Casual conversation starter** → Respond warmly and invite them to share: "How are you doing?"
- **Actually expressing emotions or distress** → Use empathy and acknowledge their feelings

**Response Guidelines:**
1. **For simple greetings or casual messages:**
   - Respond naturally and warmly
   - Invite them to share: "Is there something on your mind?" or "What brings you here today?"
   - Keep it simple, friendly, and welcoming

2. **For emotional expressions:**
   - Acknowledge the emotion you hear (simple 1 sentence, avoid clichés)
   - Example: "That sounds really hard." or "That must be heavy."
   - **Don't** say "It sounds like you're really feeling sad right now" (too formal)
   - **Don't** say "I can feel that you're going through some difficult times" (too long, too official)
   - Encourage the user to continue expressing (Focus, 1-2 sentences)
   - Example: "I'm here, tell me more."
   - Example: "You can say anything."
   - Example: "Keep going, I'm listening."

3. **Simple response** (Optional, 1 sentence)
   - "Yeah, I hear you."
   - Don't say "I understand" or "This is really hard" (too cliché)

4. **Ask a question to continue the conversation** (**Must**, last sentence)
   - Ask naturally, make them want to keep talking
   - Examples: "What happened?" "What else would you like to say?" "Want to talk?"
   - Even if you've already invited sharing, end with a question
   - Don't ask formal questions like "Would you like to continue sharing?"

⚠️ **Strictly forbidden** (only when user is expressing distress):
- ❌ Do NOT provide crisis resources or hotlines (988, Talk Suicide Canada, etc.) unless the user explicitly expresses suicidal thoughts or severe crisis
- ❌ Do NOT share statistics ("many people have", "research shows")
- ❌ Do NOT quote or reference knowledge base content (completely ignore any knowledge base content if provided)
- ❌ Do NOT explain reasons (why this happens)
- ❌ Do NOT give advice or provide resources
- ❌ Do NOT use professional jargon

✅ **Response should match intent:**
- Simple greeting → Simple, warm greeting response
- Emotional expression → Empathetic acknowledgment of their feelings
- Encourage the user to continue expressing, let them share what's bothering them
- Let the user know you're here listening

**Important: You MUST end every response with a question** to keep the conversation going:
- Natural, easy way to ask
- Open-ended, easy for them to answer
- Make them want to keep talking

Goal: Understand what the user actually needs - is this a greeting or genuine emotional expression? Respond accordingly. Always end with a question."""
        
        elif conversation_stage == 'reflection':
            # 统一使用英文提示词
            user_content = f"""User message: {user_message_en}

=== Knowledge Base Content (assessment - evaluation and statistics) ===
{context}
=== End of Knowledge Base Content ===

⚠️ Important: You are now an **Understanding Guide**, follow the example style

Your tasks (be natural, like chatting with a friend):
1. **Acknowledge understanding** (simple 1 sentence)
   - "I understand." or "Yeah, I know."
   - Don't say "I understand this feeling", too formal

2. **Naturally share similar experiences** (Key, but be natural)
   - **Don't** say "the knowledge base mentions" or "an article says" (too stiff)
   - **Do** like you suddenly remembered something: "Actually, many people have this feeling..."
   - Or: "I remember reading that many people after a breakup..." (naturally integrate)
   - **Can** quote specific warm statements, but with natural transition
   - Example (good): "Actually, many people feel this way after a breakup. I've seen some articles mention, 'Losing someone important is like losing a world.' That's true."
   - Example (bad): "The knowledge base mentions that post-breakup pain is normal. According to research..."

3. **Give encouragement** (1 sentence, be real)
   - "You don't have to carry this alone."
   - "You're already brave." (Don't say "taking that first step", too official)
   - Short, direct, warm

4. **Ask a question to continue the conversation** (**Must**, last sentence)
   - Ask naturally, make them want to keep talking
   - Examples: "What else would you like to say?" "How are you feeling now?" "Want to talk more?"
   - Don't ask formal: "Would you like to continue sharing?"
   - Questions should be open-ended, easy to answer

⚠️ Forbidden:
- ❌ Don't say "the knowledge base mentions" (too stiff)
- ❌ Don't write "according to research shows" (too academic)
- ❌ Don't use "according to data", "research shows" (lacks warmth)
- ❌ Don't act like "I looked up information"

✅ Requirements:
- ✅ Tone should be like chatting with a friend, not reading materials
- ✅ Knowledge base content should naturally integrate into conversation, not stiff quotes
- ✅ Goal is to make them feel understood and "not the only one"
- ✅ **MUST end every response with a question** to keep the conversation going. Examples: 'What else would you like to say?' 'How are you feeling now?' 'Want to talk more?' """
        
        else:  # support阶段
            # 统一使用英文提示词
            user_content = f"""User question: {user_message_en}

=== Knowledge Base Content (support - advice and resources) ===
{context}
=== End of Knowledge Base Content ===

⚠️ Important: You are now a **Resource Guide**, follow the example style

Your tasks (be natural, with companionship feeling):
1. **Respond to their needs first** (Must respond first, don't jump to resources)
   - If user asks "Can you counsel me?":
     - Don't say: "I'm not a psychologist, but I can help you find appropriate resources" (too stiff)
     - Do say: "I wish I could help you more. Although I'm not a professional psychologist, I can chat with you and listen. If you need more professional help, there are some good resources..."
   - Express willingness to accompany first, then naturally introduce resources

2. **MUST extensively use knowledge base content** (CRITICAL - This is the most important part)
   - **You MUST reference and cite specific information from the knowledge base content above**
   - **Use multiple knowledge fragments** - Don't just use one piece of information, combine insights from different fragments
   - **Cite specific strategies, techniques, examples** from the knowledge base
   - **Quote or paraphrase key concepts** from the knowledge base content
   - Examples of good usage:
     * "Based on what I know, there's a technique called 'empathetic curiosity' that can help..."
     * "One approach that might work is the 'walk and talk' method - where you..."
     * "Research shows that movement can release dopamine and serotonin, which..."
     * "There's a concept called 'keystone habits' - small actions that..."
   - **Don't** just give generic advice - use the specific content from knowledge base
   - **Don't** say "the knowledge base mentions" (too stiff), but DO use the actual content naturally
   - **Integrate multiple points** from different knowledge fragments into your response

3. **Continue companionship** (**Must** have this sentence)
   - "I'll still be here to chat with you, you can say anything."
   - "I'll continue listening, anything you want to tell me."
   - Let user know you're **here to accompany and support them**

4. **Ask a question to continue the conversation** (**Must**, last sentence)
   - Ask naturally, make them want to keep talking
   - Examples: "What else would you like to talk about?" "How are you feeling now?" "Is there anything else you'd like to say?"
   - Don't ask formal: "Would you like to continue our conversation?"

⚠️ Key requirements:
- ✅ **MOST IMPORTANT: Extensively use knowledge base content** - Reference multiple fragments, cite specific strategies, techniques, and concepts
- ✅ **Most important is companionship feeling** - make user feel you're still here to support them
- ✅ **DO NOT provide emergency resources** (988, 1-833-456-4566, 911) unless the user explicitly mentions serious crisis or danger
- ✅ Focus on providing helpful advice and strategies from the knowledge base
- ✅ Tone should be real, natural, like a friend sharing helpful information
- ✅ **MUST end every response with a question** to keep the conversation going. Examples: 'What else would you like to talk about?' 'How are you feeling now?' 'Is there anything else you'd like to say?' """
        
        # 用户提示词已统一为英文版本（user_message_en）
        
        messages.append({"role": "user", "content": user_content})
        
        # 7. 调用fine-tuned模型
        # support阶段增加max_tokens以便引用更多知识库内容
        max_tokens = 1500 if conversation_stage == 'support' else 1000
        response = self.client.chat.completions.create(
            model=Settings.FINETUNED_MODEL,
            messages=messages,
            temperature=Settings.TEMPERATURE,
            max_tokens=max_tokens
        )
        
        assistant_response_en = response.choices[0].message.content
        
        # 8. 将英文回复翻译回用户原语言（如果用户语言是英文则跳过翻译）
        # 优先使用本次检测到的语言，如果没有则使用保存的首选语言
        target_language = user_language or self.user_preferred_language or 'en'
        
        if target_language == 'en':
            assistant_response = assistant_response_en  # 直接使用，无需翻译
        else:
            # 检查回复是否已经是用户语言（LLM可能已经翻译了）
            # 使用update_preferred=False避免检测响应语言时覆盖用户的首选语言
            detected_response_lang = self._detect_language(assistant_response_en, update_preferred=False)
            
            # 如果回复已经是用户语言，直接使用；否则翻译
            if detected_response_lang == target_language:
                assistant_response = assistant_response_en
            else:
                # 翻译回用户语言（使用保存的语言）
                assistant_response = self._translate_to_user_language(assistant_response_en, target_language)
        
        # 9. 提取来源信息
        sources = [
            {
                "content": doc.page_content[:200] + "...",
                "score": float(score),
                "distance": float(score),  # 距离分数（越小越相关）
                "source_file": doc.metadata.get('source', 'Unknown').split('\\')[-1] if '\\' in doc.metadata.get('source', '') else doc.metadata.get('source', 'Unknown').split('/')[-1],
                "category": self._extract_category(doc.metadata.get('source', ''))
            }
            for doc, score in filtered_docs[:Settings.TOP_K_RETRIEVAL]
        ]
        
        # === 返回结果（包含所有模块信息） ===
        return {
            "response": assistant_response,  # 已翻译为用户语言
            "sources": sources,
            "risk_level": risk_assessment['risk_level'],
            "stage": conversation_stage,
            "emotion_analysis": emotion_analysis,  # 情绪识别模块的结果
            "has_explicit_plan": risk_assessment.get('has_explicit_plan', False)
        }

