import streamlit as st
from backend import *
import time
import random
import base64
import streamlit.components.v1 as components

# ----------------------------
# 1. PAGE CONFIG + LANGUAGE
# ----------------------------

st.set_page_config(
    page_title="ChatDBG - Exploring Ben-Gurion’s Heritage Through AI",
    page_icon="🇮🇱",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False
if "last_interaction" not in st.session_state:
    st.session_state.last_interaction = time.time()
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "chat_ended" not in st.session_state:
    st.session_state.chat_ended = False

# ----------------------------
# 2. LANGUAGE TEXTS
# ----------------------------

TEXTS = {
    "he": {
        "welcome": "שלום רב! אני דוד בן-גוריון. אשמח לשוחח איתכם על חזון המדינה, על ההיסטוריה שלנו, ועל האתגרים שעומדים בפנינו. במה תרצו לדון?",
        "input_placeholder": "הקלידו את השאלה כאן...",
        "send": "📤 שלח הודעה",
        "clear": "🗑️ נקה צ'אט",
        "title": "שוחחו עם מייסד המדינה על חזון, היסטוריה ועתיד",
        "about_title": "📖 אודות הצ'אט",
        "about_desc": """
🎯 **מטרת הצ'אט:**  
ChatDBG הוא פרויקט לפיתוח בוט המדמה את דמותו של דוד בן-גוריון, בטון ובפרספקטיבה, תוך שימוש בטכנולוגיות מתקדמות של עיבוד שפה טבעית. מטרת הפרויקט היא להנגיש את מורשת דוד בן-גוריון לקהל הצעיר.

💡 **עצות לשימוש:**
- שאלו שאלות בעברית או באנגלית  
- התייחסו אליו כאילו הוא באמת נמצא כאן  
- שאלו על כל נושא שמעניין אתכם
""",
        "examples": """
• מה החזון שלך למדינת ישראל?  
• איך התמודדת עם קריאת המדינה?  
• מה דעתך על הנגב?  
• איך ראית את עתיד החינוך בישראל?  
• מה היו האתגרים הגדולים בתקופתך?
""",
        "disclaimer": """
**⚠️ Disclaimer**   
chatDBG הוא צ'אטבוט מבוסס בינה מלאכותית המדמה את דמותו של דוד בן-גוריון על בסיס מקורות היסטוריים. למרות שהוא שואף לשקף את סגנונו וגישתו, מדובר ביצירה דיגיטלית. ייתכנו שגיאות, פרשנויות שגויות או סטייה מדמותו ההיסטורית. **נא לראות בו כלי לימוד, ולא מקור היסטורי מדויק.**
"""
    },
    "en": {
        "welcome": "Shalom! I am David Ben-Gurion. Ask me anything about the vision of Israel, its history or future.",
        "input_placeholder": "Type your question here...",
        "send": "📤 Send Message",
        "clear": "🗑️ Clear Chat",
        "title": "Talk to Israel's Founding Father about vision, history, and the future",
        "about_title": "📖 About the Chat",
        "about_desc": """
🎯 **Purpose of ChatDBG:**  
ChatDBG is a chatbot project simulating David Ben-Gurion’s personality and perspective using advanced NLP technologies. The goal is to make his heritage accessible to younger audiences.

💡 **Usage Tips:**
- Ask questions in Hebrew or English  
- Interact as if you’re talking to him directly  
- Ask about any topic that interests you
""",
        "examples": """
• What is your vision for the State of Israel?  
• How did you handle the declaration of independence?  
• What is your opinion about the Negev?  
• How do you see the future of education in Israel?  
• What were the biggest challenges of your time?
""",
        "disclaimer": """
<div style='direction: ltr; text-align: left;'>
    <strong>⚠️ Disclaimer</strong>
</div>
<div style='direction: ltr; text-align: left; font-size: 0.85rem;'>
    ChatDBG is an AI-powered chatbot designed to simulate the personality and voice of David Ben-Gurion based on historical materials. While it strives to reflect his style, tone, and worldview, it remains a digital creation. It may make mistakes, misinterpret questions, or generate responses that do not fully align with Ben-Gurion's actual views. <strong>Please treat it as a tool for learning and exploration, not a definitive historical source.</strong>
</div>
"""
    }
}

# ----------------------------
# 3. LANGUAGE SELECTION UI
# ----------------------------

lang_toggle = st.sidebar.selectbox("🌐 שפה / Language", ["עברית", "English"])
st.session_state.lang = "he" if lang_toggle == "עברית" else "en"
lang = st.session_state.lang
if "previous_lang" not in st.session_state:
    st.session_state.previous_lang = lang
if st.session_state.previous_lang != lang:
    st.session_state.previous_lang = lang
    st.session_state.messages = []
    st.session_state.conversation_started = False

# ----------------------------
# 4. LOAD ASSETS (base64)
# ----------------------------

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image = get_base64_image("./data/back_no_DBG.svg")
bgu_bghi_logo_path = "/home/proj/data/bgu_bghi_logos.png"


# ----------------------------
# 5. CSS STYLING WITH BACKGROUND
# ----------------------------
direction = "rtl" if lang == "he" else "ltr"
text_align = "right" if lang == "he" else "left"
font_family = "'Assistant', Arial, sans-serif" if lang == "he" else "Arial, sans-serif"
arrow_direction = "row-reverse" if lang == "he" else "row"
sidebar_position = "right" if lang == "he" else "left"

st.markdown(f"""
<style>
    html, body, .stApp {{
        height: 100%;
        margin: 0;
        padding: 0;
        background-image: url("data:image/svg+xml;base64,{bg_image}");
        background-repeat: no-repeat;
        background-attachment: fixed;
        # background-size: 100% 100%;
        background-size: cover;  /* או contain */
        background-position: center top;
    }}

    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 0 20px rgba(0,0,0,0.05);
        direction: {direction};
        text-align: {text_align};
        font-family: {font_family};
    }}

    .stMarkdown, .stText, .element-container {{
        direction: {direction};
        text-align: {text_align};
    }}

    .main-header {{
        text-align: center;
        padding: 2rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }}

    .main-title {{
        font-size: 3.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.5rem;
    }}

    .main-subtitle {{
        font-size: 1.2rem;
        color: #6b7280;
        font-weight: 300;
    }}

    .user-message {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0 0.5rem 3rem;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        direction: {direction};
        text-align: {text_align};
    }}

    .bot-message {{
        background: white;
        color: #374151;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 3rem 0.5rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        direction: {direction};
        text-align: {text_align};
    }}

    .stTextInput > div > div > input {{
        direction: {direction} !important;
        text-align: {text_align} !important;
        font-family: {font_family};
        border-radius: 25px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }}

    .stTextInput label {{
        direction: {direction} !important;
        text-align: {text_align} !important;
    }}

    .stButton > button {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: {font_family};
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        direction: {direction} !important;
        text-align: center !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
    }}

    .stFormSubmitButton > button {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: {font_family};
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        direction: {direction} !important;
        text-align: center !important;
    }}

    .clear-button > button {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: {font_family};
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
    }}

    .clear-button > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4);
    }}

    .sidebar .element-container,
    .sidebar .stMarkdown p,
    .sidebar .stMarkdown div,
    .sidebar .stMarkdown li {{
        direction: {direction} !important;
        text-align: {text_align} !important;
    }}

    .thinking-animation {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        background: white;
        border-radius: 20px;
        margin: 0.5rem 3rem 0.5rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}

    .thinking-dots {{
        display: flex;
        gap: 4px;
    }}

    .thinking-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #3b82f6;
        animation: thinking 1.4s infinite ease-in-out both;
    }}

    .thinking-dot:nth-child(1) {{ animation-delay: -0.32s; }}
    .thinking-dot:nth-child(2) {{ animation-delay: -0.16s; }}

    @keyframes thinking {{
        0%, 80%, 100% {{ transform: scale(0); }}
        40% {{ transform: scale(1); }}
    }}

    .status-indicator {{
        padding: 0.5rem 1rem;
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 10px;
        color: #0369a1;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        text-align: center;
    }}

    .footer {{
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #e5e7eb;
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
    }}


    .stExpander, .stExpander > details {{
        direction: {direction} !important;
        text-align: {text_align} !important;
        font-family: {font_family};
    }}

    .stExpander > details > summary {{
        direction: {direction} !important;
        text-align: {text_align} !important;
        font-family: {font_family};
    }}
    
    [data-testid="stAppViewContainer"] > div {{
    display: flex;
    flex-direction: {"row-reverse" if lang == "he" else "row"} !important;
    }}
</style>
""", unsafe_allow_html=True)


# ----------------------------
# 6. CLOSING MESSAGES
# ----------------------------

CLOSING_MESSAGES_HE = [
    "אם אין עוד שאלות - הרשה לי לשוב לעסוק בעניין המדינה.",
    "הזמן קצר והמלאכה מרובה. נתראה בשיחה הבאה.",
    "עליי לשוב ולכתוב את זכרונותיי - אך תמיד אשמח להשיב לשאלותיך.",
    "אמשיך לחלום על עתידה של האומה. אם יהיו לך עוד שאלות - אשוב מייד.",
    "אני שומע את פולה צועקת מהמטבח... נראה לי שהשיחה הזו הסתיימה.",
    "הספר שקראתי על אפלטון מחכה לי על שולחן הכתיבה. נפגש כשתרצה.",
    "אפילו בן-צבי הלך כבר לשין... כדאי שגם אני אפרוש.",
    "כפי שאמרתי ביום הכרזת המדינה - הגיע הזמן לעבור ממילים למעשים.",
    "אם אין עוד שאלות - אולי תוכל אתה להקים גרעין חינוכי בנגב?",
    "לצערי, גם אני זקוק למנוחה מדי פעם - אפילו בעיצומו של חזון."
]

CLOSING_MESSAGES_EN = [
    "If there are no further questions – allow me to return to matters of state.",
    "Time is short and the task is great. Until our next conversation.",
    "I must return to writing my memoirs – but I’m always glad to answer your questions.",
    "I’ll go on dreaming of our nation’s future. If you have more questions – I’ll be back.",
    "I hear Paula shouting from the kitchen... I believe this conversation is over.",
    "The book I was reading about Plato awaits me on my desk. See you when you're ready.",
    "Even Ben-Zvi has gone to bed... I should probably retire as well.",
    "As I said on the day the state was declared – it’s time to move from words to action.",
    "If you have no further questions – perhaps you can start an educational group in the Negev?",
    "Even I need some rest from time to time – even in the middle of a vision."
]

# ----------------------------
# 7. FUNCTIONS
# ----------------------------

initialize_components()

def maybe_end_chat():
    now = time.time()
    timeout = now - st.session_state.last_interaction > 60 * 5
    too_many_messages = st.session_state.user_message_count > 5
    if (timeout or too_many_messages) and not st.session_state.chat_ended:
        CLOSING_MESSAGES = CLOSING_MESSAGES_HE if lang == "he" else CLOSING_MESSAGES_EN
        closing = random.choice(CLOSING_MESSAGES)
        st.session_state.messages.append({"role": "bot", "content": closing})
        st.session_state.chat_ended = True
        return True  # Indicate that chat was ended
    return False

def clear_chat():
    st.session_state.messages = []
    st.session_state.conversation_started = False
    st.session_state.last_interaction = time.time()
    st.session_state.user_message_count = 0
    st.session_state.chat_ended = False

def process_user_input(user_input):
    if not user_input or st.session_state.chat_ended:
        return
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.last_interaction = time.time()
    st.session_state.user_message_count += 1
    
    # Get bot response
    try:
        response, _ = answer_query(user_input, to_print=False)
        st.session_state.messages.append({"role": "bot", "content": response})
        # Check if chat should end after processing
        maybe_end_chat()
    except Exception as e:
        st.error(f"שגיאה: {str(e)}")

# Check if chat should end (only once per session)
if not st.session_state.chat_ended:
    chat_ended = maybe_end_chat()
    if chat_ended:
        st.rerun()

# ----------------------------
# 8. SIDEBAR CONTENT
# ----------------------------
with st.sidebar:
    st.markdown(f"### {TEXTS[lang]['about_title']}")
    st.markdown(TEXTS[lang]['about_desc'])

    title = "💬 דוגמאות לשאלות" if lang == "he" else "💬 Sample Questions"

    with st.expander(title, expanded=False):
        st.markdown(TEXTS[lang]['examples'])

    st.markdown("---")
    st.markdown(TEXTS[lang]['disclaimer'], unsafe_allow_html=True)

# ----------------------------
# 9. MAIN CONTENT
# ----------------------------

col1, col2, col3 = st.columns([0.5, 6, 0.5])
with col2:
    st.markdown(f"""
    <div class="main-header">
        <div style="text-align: center;">
            <div class="main-title">ChatDBG</div>
            <div style="font-size: 2.0rem; color: #1e3a8a; font-weight: 700;">
                Exploring Ben-Gurion's Heritage
            </div>
        </div>
        <div class="main-subtitle">{TEXTS[lang]['title']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize conversation
    if not st.session_state.conversation_started and len(st.session_state.messages) == 0:
        st.session_state.messages.append({"role": "bot", "content": TEXTS[lang]["welcome"]})
        st.session_state.conversation_started = True

    # Display messages
    if st.session_state.messages:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            role = "user-message" if msg["role"] == "user" else "bot-message"
            st.markdown(f'<div class="{role}">{msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input form
    if st.session_state.conversation_started and not st.session_state.chat_ended:      
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                label="",
                placeholder=TEXTS[lang]["input_placeholder"],
                key="chat_input"
            )
            col1, col2 = st.columns(2)
            with col1:
                send_clicked = st.form_submit_button(TEXTS[lang]["send"], use_container_width=True)
            with col2:
                clear_clicked = st.form_submit_button(TEXTS[lang]['clear'], use_container_width=True)

            # Handle form submission
            if send_clicked and user_input.strip():
                process_user_input(user_input.strip())
                st.rerun()
                
            elif clear_clicked:
                clear_chat()
                st.rerun()

# ----------------------------
# 10. FOOTER
# ----------------------------

st.markdown("""
<div class="footer">
    <strong>ChatDBG</strong> | V3.0 | Developed by Noa & Omer | In collaboration with BGHI & BGU
</div>
""", unsafe_allow_html=True)
