import streamlit as st
from backend import *
import time
import random
import base64

# Page config
st.set_page_config(
    page_title="ChatDBG - Exploring Ben-Gurion’s Heritage Through AI",
    page_icon="🇮🇱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "last_interaction" not in st.session_state:
    st.session_state.last_interaction = time.time()
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "chat_ended" not in st.session_state:
    st.session_state.chat_ended = False

# Load background image as base64
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image = get_base64_image("./data/background.jpeg")
bg_logo = get_base64_image("./data/logo_v1.2.png")

CLOSING_MESSAGES = [
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

# Initialize backend
@st.cache_resource
def initialize():
    initialize_components()

initialize()

# Auto-end chat logic
def maybe_end_chat():
    now = time.time()
    timeout = now - st.session_state.last_interaction > 60 * 1
    too_many_messages = st.session_state.user_message_count > 5

    if (timeout or too_many_messages) and not st.session_state.chat_ended:
        closing = random.choice(CLOSING_MESSAGES)
        st.session_state.messages.append({"role": "bot", "content": closing})
        st.session_state.chat_ended = True

# Auto refresh logic (checks if we need to auto-close chat)
if not st.session_state.chat_ended:
    maybe_end_chat()
    if st.session_state.chat_ended:
        st.rerun()

# Enhanced RTL and UI Styling
st.markdown("""
    <style>
    .stApp {{
        position: relative;
        z-index: 0;
    }}

    .stApp::before {{
        content: "";
        background-image: url("data:image/jpeg;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.3;
        z-index: -1;
    }}
            
    /* Import Hebrew font */
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap');
    
    /* Global RTL styling */
    .main .block-container {
        direction: rtl;
        text-align: right;
        font-family: 'Assistant', Arial, sans-serif;
    }
    
    /* Streamlit elements RTL override */
    .stMarkdown, .stText, .element-container {
        direction: rtl;
        text-align: right;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        color: #6b7280;
        font-weight: 300;
    }
    
    /* Chat container */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
            
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0 0.5rem 3rem;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        direction: rtl;
        text-align: right;
    }
    
    .bot-message {
        background: white;
        color: #374151;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 3rem 0.5rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        direction: rtl;
        text-align: right;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', Arial, sans-serif;
        border-radius: 25px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Form labels RTL */
    .stTextInput label {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Assistant', Arial, sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        direction: rtl !important;
        text-align: center !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
    }
    
    /* Form submit buttons */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Assistant', Arial, sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        direction: rtl !important;
        text-align: center !important;
    }
    
    /* Clear button styling */
    .clear-button > button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Assistant', Arial, sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
    }
    
    .clear-button > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc, .css-1y4p8pa {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', Arial, sans-serif;
    }
    
    /* Force sidebar content RTL */
    .sidebar .element-container {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Sidebar text elements */
    .sidebar .stMarkdown p, .sidebar .stMarkdown div, .sidebar .stMarkdown li {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Loading animation */
    .thinking-animation {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        background: white;
        border-radius: 20px;
        margin: 0.5rem 3rem 0.5rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .thinking-dots {
        display: flex;
        gap: 4px;
    }
    
    .thinking-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #3b82f6;
        animation: thinking 1.4s infinite ease-in-out both;
    }
    
    .thinking-dot:nth-child(1) { animation-delay: -0.32s; }
    .thinking-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes thinking {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    /* Status indicator */
    .status-indicator {
        padding: 0.5rem 1rem;
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 10px;
        color: #0369a1;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Footer */
    .footer {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #e5e7eb;
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
    }
            
    /* Sidebar styling */
    .css-1d391kg {
        direction: rtl;
    }
    .sidebar-content {
        direction: rtl;
        text-align: right;
    }
    
    body {
    direction: rtl;
    text-align: right;
    }
            
    </style>
""", unsafe_allow_html=True)

# Clear chat function
def clear_chat():
    st.session_state.messages = []
    st.session_state.conversation_started = False
    st.session_state.last_interaction = time.time()
    st.session_state.user_message_count = 0
    st.session_state.chat_ended = False
    st.session_state.user_input = ""

# Process input
def process_user_input():
    user_input = st.session_state.user_input.strip()
    if not user_input or st.session_state.chat_ended:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.last_interaction = time.time()
    st.session_state.user_message_count += 1

    try:
        response, _ = answer_query(user_input, to_print=False)
        st.session_state.messages.append({"role": "bot", "content": response})
        maybe_end_chat()
    except Exception as e:
        st.error(f"שגיאה: {str(e)}")

    st.session_state.user_input = ""

# Sidebar
with st.sidebar:
    try:
        st.markdown(f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{bg_logo}' width='200'/>
        </div>
        """, unsafe_allow_html=True)
    except:
        st.warning("לא ניתן לטעון את התמונה")
    
    st.markdown("### 📖 אודות הצ'אט")
    st.markdown("""
    🎯 **מטרת הצ'אט:**  
    ChatDBG הוא פרויקט לפיתוח בוט המדמה את דמותו של דוד בן גוריון, בטון ובפרספקטיבה, תוך שימוש בטכנולוגיות מתקדמות של עיבוד שפה טבעית. מטרת הפרויקט היא להנגיש את מורשת דוד בן-גוריון לקהל הצעיר.
    
    
    💡 **עצות לשימוש:**
    - שאלו שאלות בעברית או באנגלית
    - התייחסו אליו כאילו הוא באמת נמצא כאן
    - שאלו על כל נושא שמעניין אתכם
    """)
    
    with st.expander("💬 דוגמאות לשאלות"):
        st.markdown("""
        • מה החזון שלך למדינת ישראל?
                    
        • איך התמודדת עם קריאת המדינה?
                    
        • מה דעתך על הנגב?
                    
        • איך ראית את עתיד החינוך בישראל?
                    
        • מה היו האתגרים הגדולים בתקופתך?
        """)
    
    st.markdown("---")
    st.markdown("""
        <div style='direction: ltr; text-align: left;'>
            <strong>⚠️ Disclaimer</strong>
        </div>

                
        <div style='direction: ltr; text-align: left; font-size: 0.85rem;'>
        chatDBG is an AI-powered chatbot designed to simulate the personality and voice of David Ben-Gurion based on historical materials. While it strives to reflect his style, tone, and worldview, it remains a digital creation. It may make mistakes, misinterpret questions, or generate responses that do not fully align with Ben-Gurion's actual views. <strong>Please treat it as a tool for learning and exploration, not a definitive historical source.</strong>
        </div>
        """, unsafe_allow_html=True)

# Main content
col1, col2, col3 = st.columns([0.5, 6, 0.5])
with col2:
    # Header
    st.markdown("""
    <div class="main-header">
        <div style="text-align: center;">
            <div class="main-title">ChatDBG</div>
            <div style="font-size: 2.0rem; color: #1e3a8a; font-weight: 700;">
                Exploring Ben-Gurion's Heritage
            </div>
        </div>
        <div class="main-subtitle">שוחחו עם מייסד המדינה על חזון, היסטוריה ועתיד</div>
    </div>
    """, unsafe_allow_html=True)


    # Welcome message
    if not st.session_state.conversation_started and len(st.session_state.messages) == 0:
        welcome_message = "שלום רב! אני דוד בן-גוריון. אשמח לשוחח איתכם על חזון המדינה, על ההיסטוריה שלנו, ועל האתגרים שעומדים בפנינו. במה תרצו לדון?"
        st.session_state.messages.append({"role": "bot", "content": welcome_message})
        st.session_state.conversation_started = True

    # Chat
    if st.session_state.messages:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            style = "user-message" if msg["role"] == "user" else "bot-message"
            st.markdown(f'<div class="{style}">{msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input
    if st.session_state.conversation_started and not st.session_state.chat_ended:
        prompt = st.chat_input("הקלידו את השאלה כאן...")

        if prompt:
            st.session_state.user_input = prompt
            process_user_input()

        col1, col2 = st.columns(2)
        with col1:
            st.button("📤 שלח הודעה", on_click=process_user_input, use_container_width=True)
        with col2:
            st.button("🗑️ נקה צ'אט", on_click=clear_chat, use_container_width=True)
         

# Footer
st.markdown("""
<div class="footer">
    <strong>ChatDBG</strong> | V3.0 | Developed by Noa & Omer | In collaboration with BGH & BGU <br>
</div>
""", unsafe_allow_html=True)
