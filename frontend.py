import streamlit as st
from streamlit_chat import message
from backend import *
import base64
from PIL import Image
import io


# Page config
st.set_page_config(
    page_title="ChatDBG",
    page_icon="🇮🇱",
    layout="wide"
)

# Convert PIL Image to base64 string for avatar
@st.cache_resource
def get_image_base64():
    try:
        image = Image.open("./data/bengurion.jpg")
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        st.error(f"Could not load avatar image: {e}")
        return None

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Function to clear chat
def clear_chat():
    st.session_state.messages = []
    st.session_state.conversation_started = False
    st.session_state.user_input = ""

# Function to process user input
def process_user_input():
    if st.session_state.user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": st.session_state.user_input})
        
        # Get bot response
        with st.spinner("חושב..."):
            response, _ = answer_query(st.session_state.user_input, to_print=False)
            bot_message = response["text"]
            
            # Add bot message
            st.session_state.messages.append({"role": "bot", "content": bot_message})
        
        # Clear input
        st.session_state.user_input = ""

# RTL Styling
st.markdown(
    """
    <style>
    body {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', Arial, sans-serif;
    }
    .chat-message {
        direction: rtl;
        text-align: right;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .stAvatar img {
        width: 45px !important;
        height: 45px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0066cc !important;
    }
    .stButton>button {
        background-color: #0066cc;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 2rem;
    }
    /* Sidebar styling */
    .css-1d391kg {
        direction: rtl;
    }
    .sidebar-content {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize backend
@st.cache_resource
def initialize():
    initialize_components()

initialize()

# Sidebar
with st.sidebar:
    try:
        st.image("./data/dbg_emoji.png", width=200)
    except:
        st.error("לא ניתן לטעון את התמונה")
    
    st.title("אודות")
    st.markdown("""
    <div class="sidebar-content">
    צ'אט זה מאפשר לכם לשוחח עם דוד בן-גוריון, ראש הממשלה הראשון של מדינת ישראל.
    
    הצ'אט מבוסס על טכנולוגיית בינה מלאכותית ומתוכנת לענות בסגנונו הייחודי של בן-גוריון.
    
    📝 **הנחיות לשימוש:**
    * שאלו שאלות בעברית או באנגלית
    * ניתן לשאול על הכל! אירועים היסטוריים, דעותיו, והחלטותיו
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔍 דוגמאות לשאלות"):
        st.markdown("""
        * מה דעתך על הקמת המדינה?
        * איך התמודדת עם האתגרים בתקופת העלייה הגדולה?
        * מה החזון שלך למדינת ישראל?
        """)

# Main chat interface
col1, col2, col3 = st.columns([0.5, 5, 0.5])
with col2:
    st.title("צ'אט עם דוד בן-גוריון")
    st.markdown("שאלו כל שאלה, והצ'אט יענה לכם בטון ובסגנון של דוד בן-גוריון!")

    # Welcome message - Remove duplication
    if not st.session_state.conversation_started:
        welcome_message = "שלום רב! אני דוד בן-גוריון. אשמח לשוחח איתכם על חזון המדינה, על ההיסטוריה שלנו, ועל האתגרים שעומדים בפנינו. במה תרצו לדון?"
        
        # Ensure the message is not duplicated
        if not any(msg["content"] == welcome_message for msg in st.session_state.messages):
            st.session_state.messages.append({
                "role": "bot",
                "content": welcome_message
            })
        
        st.session_state.conversation_started = True

    # Display chat messages
    with st.container():
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=f"user_{i}")
            else:
                message(msg["content"], key=f"bot_{i}")

    # User input
    st.text_input(
        "אתם:",
        placeholder="הקלידו את השאלה כאן...",
        key="user_input",
        label_visibility="collapsed"
    )

# Buttons in a horizontal container
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("שלח", on_click=process_user_input, key="send_button")
    with col2:
        st.button("נקה צ'אט", on_click=clear_chat, key="clear_button")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
with st.container():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center'> ChatDBG | V1.0 | Developed by Noa & Omer | In collaboration with BGH & BGU </div>", unsafe_allow_html=True)
