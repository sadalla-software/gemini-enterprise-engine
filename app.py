import streamlit as st
import json
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests
import hashlib
import base64
import io
import os

# Maktaba za ReportLab kwa ajili ya kutengeneza PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Gemini Enterprise Engine", layout="wide", initial_sidebar_state="collapsed")

# Hakikisha maktaba ya sauti ipo
try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("Tafadhali sakinisha maktaba ya sauti kwa kupiga: pip install streamlit-mic-recorder")
    st.stop()

# =====================================================================
# FUNCTION ZA KUBADILISHA PICHA KUWA BASE64 (Kwa ajili ya HTML/CSS)
# =====================================================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Kusoma Logo na Picha ya Background
logo_b64 = get_base64_image("Sadallah Software3.png")
bg_b64 = get_base64_image("Abc.jpg")

# =====================================================================
# 1. FUNGUO ZA KUSHUGULIKIA SEVA
# =====================================================================
SUPABASE_URL = "https://ndpuprbdulfrjwxakfmm.supabase.co"

try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_TOKEN = st.secrets["GEMINI_TOKEN"]
except Exception:
    st.error("Tafadhali hakikisha umeweka SUPABASE_KEY na GEMINI_TOKEN kwenye Secrets za Streamlit.")
    st.stop()

try:
    clean_url = str(SUPABASE_URL).strip()
    clean_key = str(SUPABASE_KEY).strip()
    supabase: Client = create_client(clean_url, clean_key)
except Exception as e:
    st.error(f"Hitilafu ya Supabase: {e}")
    st.stop()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# =====================================================================
# 2. DESIGN & STYLING (SPLIT-SCREEN DESIGN LIKE THE UPLOADED SPEC)
# =====================================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["business_name"] = ""

if not st.session_state["logged_in"]:
    background_css = f"""
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-color: #1e1e24 !important;
        font-family: 'Syne', sans-serif !important;
    }}
    """
else:
    background_css = """
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        font-family: 'Syne', sans-serif !important;
        background: #ffffff !important;
    }}
    """

custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&display=swap');

    {background_css}
    
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Split Screen Container */
    .split-container {{
        display: flex;
        width: 100%;
        max-width: 1100px;
        min-height: 580px;
        background-color: #26262b;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        margin: 40px auto;
    }}

    /* Left Poster Section */
    .poster-side {{
        width: 50%;
        position: relative;
        background-image: linear-gradient(to top, rgba(15, 15, 18, 0.95), rgba(15, 15, 18, 0.3)), url("data:image/jpeg;base64,{bg_b64}");
        background-size: cover;
        background-position: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 40px;
        overflow: hidden;
    }}

    /* Slider / Poster Text Sliding Animation (Kulia kwenda Kushoto) */
    .sliding-text {{
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.3;
        margin-bottom: 20px;
        transform: translateX(100%);
        animation: slideFromRight 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        animation-delay: 0.4s;
    }}

    /* Right Form Section */
    .form-side {{
        width: 50%;
        padding: 45px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: #ffffff;
    }}

    .form-title {{
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 5px;
    }}

    .form-subtitle {{
        font-size: 14px;
        color: #a0a0ab;
        margin-bottom: 30px;
    }}

    /* Input Field Overrides to Match Dark Spec */
    div[data-testid="stTextInput"] input {{
        font-family: 'Syne', sans-serif !important;
        border-radius: 8px !important;
        border: 1px solid #44444f !important;
        background-color: #1e1e24 !important;
        padding: 12px !important;
        height: 48px !important;
        color: #ffffff !important;
    }}
    
    div[data-testid="stTextInput"] input:focus {{
        border-color: #00b4d8 !important;
    }}

    /* Custom Submit Button mimicking premium UI */
    div.stButton > button {{
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        background-color: #6366f1 !important;
        color: white !important;
        border-radius: 8px !important;
        width: 100% !important;
        height: 48px !important;
        border: none !important;
        transition: all 0.3s ease;
        margin-top: 15px;
    }}
    
    div.stButton > button:hover {{
        background-color: #4f46e5 !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }}
    
    /* Logo Animations Inside Poster Area */
    .header-logo-container {{
        display: flex;
        align-items: center;
        gap: 14px;
    }}

    .header-logo-img {{
        width: 52px;
        height: auto;
    }}

    .logo-text-wrapper {{
        display: flex;
        flex-direction: column;
        line-height: 1.1;
        text-align: left;
    }}

    .anim-sadallah {{
        font-weight: 800;
        font-size: 26px;
        letter-spacing: -0.5px;
        color: #ffffff;
        display: block;
        opacity: 0;
        transform: translateY(-25px);
        animation: slideFromTop 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    .anim-software {{
        font-weight: 700;
        font-size: 22px;
        letter-spacing: -0.5px;
        color: #00b4d8 !important;
        display: block;
        opacity: 0;
        transform: translateY(25px);
        animation: slideFromBottom 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        animation-delay: 0.18s;
    }}

    /* Dots indicator for look and feel */
    .indicator-dots {{
        display: flex;
        gap: 8px;
        margin-top: 15px;
    }}
    .dot {{
        width: 24px;
        height: 4px;
        background-color: #ffffff;
        border-radius: 2px;
    }}
    .dot.inactive {{
        width: 12px;
        background-color: #52525b;
    }}

    /* KEYFRAMES */
    @keyframes slideFromTop {{
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes slideFromBottom {{
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes slideFromRight {{
        to {{
            transform: translateX(0);
        }}
    }}
    
    div[data-testid="stRadio"] label {{
        color: #ffffff !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# =====================================================================
# 3. Mfumo wa Kuingia (Split Login UI Trigger)
# =====================================================================
if not st.session_state["logged_in"]:
    
    # Tunatumia st.columns za Streamlit kutengeneza space ya katikati
    _, main_wrapper, _ = st.columns([0.2, 9, 0.2])
    
    with main_wrapper:
        # Sehemu ya kuchagua log in au sign up ipo juu ya kibox
        form_mode = st.radio("Chagua Kitendo", ["Kuingia (Log In)", "Kujisajili (Sign Up)"], label_visibility="collapsed", horizontal=True)
        
        # Nembo na picha base64 assembly
        img_tag = f'<img src="data:image/png;base64,{logo_b64}" class="header-logo-img" />' if logo_b64 else ''
        
        # Kuanza kutengeneza ule muundo wa pande mbili kwa HTML
        poster_html = f'''
        <div class="split-container">
            <div class="poster-side">
                <div class="header-logo-container">
                    {img_tag}
                    <div class="logo-text-wrapper">
                        <span class="anim-sadallah">Sadallah</span>
                        <span class="anim-software">Software</span>
                    </div>
                </div>
                
                <div>
                    <div class="sliding-text">
                        Capturing Moments,<br/>Creating Future Technology.
                    </div>
                    <div class="indicator-dots">
                        <div class="dot"></div>
                        <div class="dot inactive"></div>
                        <div class="dot inactive"></div>
                    </div>
                </div>
            </div>
            
            <div class="form-side">
        '''
        st.markdown(poster_html, unsafe_allow_html=True)
        
        # Kuweka input controllers ndani ya eneo la Kulia la Fomu
        if form_mode == "Kuingia (Log In)":
            st.markdown('<div class="form-title">Create an account</div><div class="form-subtitle">Already have an account? Log in below.</div>', unsafe_allow_html=True)
            
            login_email = st.text_input("Email Address", placeholder="name@example.com", key="login_email_key").strip()
            login_pass = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass_key").strip()
            
            if st.button("Continue with Email", key="btn_login"):
                if login_email and login_pass:
                    try:
                        res = supabase.table("business_users").select("*").eq("email", login_email).execute()
                        user_data = res.data
                        
                        if user_data and user_data[0]["password_hash"] == hash_password(login_pass):
                            st.session_state["logged_in"] = True
                            st.session_state["business_name"] = user_data[0]["business_name"]
                            st.success(f"Karibu tena {st.session_state['business_name']}!")
                            st.rerun()
                        else:
                            st.error("Email au Password si sahihi. Tafadhali jaribu tena.")
                    except Exception as e:
                        st.error(f"Hitilafu ya kuingia: {e}")
                else:
                    st.warning("Tafadhali jaza nafasi zote.")
                    
        else:
            st.markdown('<div class="form-title">Create account</div><div class="form-subtitle">Tengeneza akaunti ya biashara yako sasa hivi</div>', unsafe_allow_html=True)
            
            reg_biz = st.text_input("Business Name", placeholder="Mfano: Sadallah Software", key="reg_biz_key").strip()
            reg_email = st.text_input("Email Address", placeholder="name@example.com", key="reg_email_key").strip()
            reg_pass = st.text_input("Password", type="password", placeholder="Create an enterprise password", key="reg_pass_key").strip()
            
            if st.button("Create Account", key="btn_reg"):
                if reg_biz and reg_email and reg_pass:
                    try:
                        hashed = hash_password(reg_pass)
                        user_record = {
                            "business_name": reg_biz,
                            "email": reg_email,
                            "password_hash": hashed
                        }
                        supabase.table("business_users").insert(user_record).execute()
                        st.success("🎉 Akaunti imesajiliwa! Badili redio kwenda kwenye 'Log In' ili kuingia.")
                    except Exception as e:
                        st.error(f"Imeshindwa kusajili: {e}")
                else:
                    st.warning("Tafadhali jaza fomu yote.")
        
        # Funga Ma-Div yote ya Split interface
        st.markdown('</div></div>', unsafe_allow_html=True)
        
    st.stop()

# =====================================================================
# 4. DASHBOARD YA BIASHARA (IKIFUNGOLEWA BAADA YA LOGIN)
# =====================================================================
biz_name_input = st.session_state["business_name"]

if logo_b64:
    st.sidebar.markdown(f'''
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_b64}" style="width: 35px; height: auto;" />
            <span style="font-weight: 800; font-size: 18px; color: #111111; font-family: 'Syne';">SADALLAH</span>
        </div>
    ''', unsafe_allow_html=True)

st.sidebar.title(f"🏢 {biz_name_input}")
st.sidebar.write("Umeingia salama mtandaoni.")
if st.sidebar.button("📴 Tokea Kwenye Mfumo (Logout)"):
    st.session_state["logged_in"] = False
    st.session_state["business_name"] = ""
    st.rerun()

st.title("🚀 Gemini Enterprise Engine (GEE)")
st.subheader(f"Workspace Rasmi: {biz_name_input}")
st.markdown("---")

# --- SEHEMU YA KUINGIZA DATA ---
st.write("### 🗣️ Rekodi au Andika Muamala kwa Kiswahili/English")
col_text, col_voice = st.columns([2, 1])

with col_text:
    user_input = st.text_input(label="Andika muamala wako hapa...", placeholder="Mfano: Leo nimeuza hereni pea 3 kwa elfu 15", key="text_msg")

with col_voice:
    st.write("Au Rekodi Sauti yako hapa:")
    audio_record = mic_recorder(
        start_prompt="🔴 Anza Kurekodi Sauti",
        stop_prompt="⏹️ Stop & Tuma",
        key='recorder'
    )

final_text_prompt = ""
audio_bytes = None

if user_input:
    final_text_prompt = user_input
elif audio_record:
    audio_bytes = audio_record['bytes']
    st.audio(audio_bytes, format='audio/wav')

if st.button("Chambua na Uhifadhi") or (audio_record is not None and audio_bytes is not None):
    if final_text_prompt or audio_bytes:
        with st.spinner("Gemini inachambua na kupanga muamala wako..."):
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                headers = {'Content-Type': 'application/json'}
                params = {'key': GEMINI_TOKEN}
                
                system_instruction = (
                    "You are a strict financial data extractor. Analyze the input text or audio transaction in Swahili or English. "
                    "Identify if it is 'income' or 'expense', extract the exact numeric amount, and give a short English description. "
                    "You must output ONLY valid raw JSON with keys: 'type', 'amount', 'description'."
                )

                generation_config = {"response_mime_type": "application/json"}

                if final_text_prompt:
                    payload = {
                        "contents": [{"parts": [{"text": f"{system_instruction}\n\nTransaction text: {final_text_prompt}"}]}],
                        "generationConfig": generation_config
                    }
                elif audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": system_instruction},
                                {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}
                            ]
                        }],
                        "generationConfig": generation_config
                    }

                response = requests.post(url, headers=headers, json=payload, params=params)
                response_json = response.json()
                
                if 'candidates' in response_json and response_json['candidates']:
                    ai_text = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    extracted_data = json.loads(ai_text)
                    
                    db_record = {
                        "type": extracted_data.get("type", "income"),
                        "amount": float(extracted_data.get("amount", 0)),
                        "description": extracted_data.get("description", "Transaction"),
                        "raw_ai_prompt": final_text_prompt if final_text_prompt else "[Sauti ya Kiswahili Ilichakatwa]",
                        "business_name": biz_name_input
                    }
                    
                    supabase.table("transactions").insert(db_record).execute()
                    st.success(f"🎉 Muamala wa {biz_name_input} umetafsiriwa na kuhifadhiwa!")
                    st.rerun()
                elif 'error' in response_json and response_json['error']['code'] == 429:
                    st.error("⏳ Mfumo una matumizi makubwa kwa sasa (Daily Free Quota Exceeded). Tafadhali subiri kidogo au weka API Key nyingine ili kuendelea.")
                else:
                    st.error(f"Gemini API Error Response: {response_json}")
                
            except Exception as e:
                st.error(f"Kuna kitu kimefeli wakati wa kuchakata muamala: {e}")
    else:
        st.warning("Tafadhali andika maelezo au rekodi sauti kwanza.")

st.markdown("---")

# --- SEHEMU YA DASHBOARD & GRAPH ---
st.write("### 📊 Mwenendo wa Biashara Yako")

data = []
try:
    res = supabase.table("transactions").select("*").eq("business_name", biz_name_input).order("created_at", desc=True).execute()
    data = res.data
except Exception as e:
    st.error(f"Imeshindwa kuvuta data kutoka Supabase: {e}")

if data:
    df = pd.DataFrame(data)
    total_income = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    net_profit = total_income - total_expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumla ya Mapato (Income)", f"TZS {total_income:,.2f}")
    col2.metric("Jumla ya Matumizi (Expense)", f"TZS {total_expense:,.2f}")
    col3.metric("Faida/Hasara (Net Profit)", f"TZS {net_profit:,.2f}", delta=float(net_profit))
    
    fig = px.bar(df, x="created_at", y="amount", color="type", 
                 title=f"Mchanganuo wa Miamala ya {biz_name_input}",
                 labels={"amount": "Kiasi (TZS)", "created_at": "Tarehe"},
                 color_discrete_map={"income": "#2ecc71", "expense": "#e74c3c"})
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df[["created_at", "type", "amount", "description", "raw_ai_prompt"]], use_container_width=True)
    
    # --- AI BUSINESS ADVISOR ---
    st.markdown("---")
    st.write("### 🤖 AI Business Advisor")
    
    if st.button("Changanua Biashara na Upe Ushauri"):
        with st.spinner("Gemini inasoma miamala yako na kuandaa ushauri..."):
            try:
                history_str = df[["type", "amount", "description"]].to_string(index=False)
                
                advisor_prompt = (
                    f"You are the Lead Financial AI Advisor for a business named '{biz_name_input}'. Analyze their transaction history:\n\n"
                    f"{history_str}\n\n"
                    f"Financial Summary:\n"
                    f"- Total Income: TZS {total_income}\n"
                    f"- Total Expense: TZS {total_expense}\n"
                    f"- Net Profit: TZS {net_profit}\n\n"
                    f"Provide a brief, highly actionable strategic advice in Swahili for the business owner. "
                    f"Address them specifically by their business name '{biz_name_input}'. "
                    f"Highlight where they are losing money or doing well, and give 2 clear steps to increase profit next month. "
                    f"Keep the tone encouraging, professional, and friendly."
                )
                
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                payload = {"contents": [{"parts": [{"text": advisor_prompt}]}]}
                
                advisor_response = requests.post(url, headers=headers, json=payload, params=params)
                advisor_json = advisor_response.json()
                
                if 'candidates' in advisor_json and advisor_json['candidates']:
                    advisor_text = advisor_json['candidates'][0]['content']['parts'][0]['text']
                    st.success(f"🎯 Ushauri Rasmi kutoka kwa Gemini Advisor kwenda kwa {biz_name_input}:")
                    st.write(advisor_text)
                else:
                    st.error(f"Advisor Response Error: {advisor_json}")
                
            except Exception as e:
                st.error(f"Imeshindwa kuzalisha ushauri wa AI: {e}")

    # --- MFUMO WA KUZALISHA RIPOTI YA PDF KWA AJILI YA BENKI ---
    st.markdown("---")
    st.write("### 📄 Ripoti Rasmi ya Kifedha (PDF)")
    
    if st.button("Tengeneza Ripoti ya PDF"):
        with st.spinner("Tunatengeneza faili la PDF..."):
            try:
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                story = []
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1a365d'), spaceAfter=10)
                subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#4a5568'), spaceAfter=20)
                heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2b6cb0'), spaceBefore=15, spaceAfter=10)
                normal_style = styles['Normal']
                
                story.append(Paragraph(f"GEMINI ENTERPRISE ENGINE (GEE)", title_style))
                story.append(Paragraph(f"Sadallah Software | Official Financial Statement", subtitle_style))
                story.append(Spacer(1, 10))
                
                story.append(Paragraph("<b>TAARIFA ZA WORKSPACE</b>", heading_style))
                biz_info = f"<b>Jina la Biashara:</b> {biz_name_input}<br/><b>Tarehe ya Ripoti:</b> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}<br/><b>Hali ya Uhakiki:</b> Certified by Gemini AI Advisor<br/>"
                story.append(Paragraph(biz_info, normal_style))
                story.append(Spacer(1, 15))
                
                summary_table_data = [
                    [Paragraph("<b>Kipengele</b>", normal_style), Paragraph("<b>Kiasi (TZS)</b>", normal_style)],
                    ["Jumla ya Mapato (Total Income)", f"{total_income:,.2f}"],
                    ["Jumla ya Matumizi (Total Expense)", f"{total_expense:,.2f}"],
                    ["Faida Safi (Net Profit)", f"{net_profit:,.2f}"]
                ]
                t_summary = Table(summary_table_data, colWidths=[250, 200])
                t_summary.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (1,0), colors.HexColor('#2b6cb0')), ('TEXTCOLOR', (0,0), (1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f7fafc')), ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0'))
                ]))
                story.append(t_summary)
                
                doc.build(story)
                pdf_data = pdf_buffer.getvalue()
                
                st.download_button(label="📥 Pakua Ripoti Yako ya PDF Hapa", data=pdf_data, file_name=f"Ripoti_ya_Fedha_{biz_name_input}.pdf", mime="application/pdf")
                st.success("🎉 PDF ipo tayari!")
            except Exception as e:
                st.error(f"Imeshindwa kutengeneza PDF: {e}")
else:
    st.info(f"Biashara ya **{biz_name_input}** bado haina miamala iliyorekodiwa.")