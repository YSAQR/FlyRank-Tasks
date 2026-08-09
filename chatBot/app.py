import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# إعداد مفتاح API لـ Gemini
# يجب التأكد من وجود المتغير GEMINI_API_KEY في ملف .env
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    st.error("⚠️ لم يتم العثور على مفتاح GEMINI_API_KEY أو لم يتم تعديله. الرجاء إضافته في ملف .env")
    st.stop()

# إعداد إعدادات الاتصال بـ Google Gemini
genai.configure(api_key=api_key)

# 2. إعداد إعدادات الصفحة في Streamlit
st.set_page_config(page_title="Gemini Smart Chatbot", page_icon="🤖", layout="centered")

st.title("🤖 Your AI ChatBot ")
st.markdown("مرحباً بك! أنا مساعدك الذكي . كيف يمكنني مساعدتك اليوم؟")

# 3. تحميل وإعداد نموذج Gemini
# نستخدم نموذج gemini-1.5-flash كونه سريع ومناسب جداً للمحادثات
@st.cache_resource
def load_model():
    return genai.GenerativeModel('gemini-3.5-flash')

model = load_model()

# 4. إعداد ذاكرة المحادثة (Chat History) باستخدام session_state
# هذه الخطوة مهمة جداً لكي يتذكر البوت سياق المحادثة
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. عرض سجل المحادثة السابق على الشاشة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. استقبال إدخال المستخدم الجديد
user_input = st.chat_input("اكتب رسالتك هنا...")

if user_input:
    # أ. عرض رسالة المستخدم على الشاشة وتخزينها في الواجهة
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ب. إرسال الرسالة للنموذج واستقبال الرد
    with st.chat_message("assistant"):
        with st.spinner("جارٍ التفكير..."):
            try:
                # نرسل الرسالة لجلسة المحادثة لكي يتم أخذ السياق في الاعتبار
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                
                # ج. تخزين رد المساعد في الذاكرة الخاصة بالواجهة
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"حدث خطأ أثناء الاتصال بالنموذج: {e}")
