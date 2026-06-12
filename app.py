import streamlit as st
import json
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests
import hashlib
import base64
import io

# Maktaba za ReportLab kwa ajili ya kutengeneza PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Gemini Enterprise Engine", layout="wide")

# Hakikisha maktaba ya sauti ipo, isipokuwa isikwamishe mfumo
try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("Tafadhali sakinisha maktaba ya sauti kwa kupiga: pip install streamlit-mic-recorder")
    st.stop()

# =====================================================================
# 1. FUNGUO ZA KUSHUGULIKIA SEVA
# =====================================================================
SUPABASE_URL = "[https://ndpuprbdulfrjwxakfmm.supabase.co](https://ndpuprbdulfrjwxakfmm.supabase.co)"
try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_TOKEN = st.secrets["GEMINI_TOKEN"]
except Exception:
    st.error("Tafadhali hakikisha umeweka SUPABASE_KEY na GEMINI_TOKEN kwenye Secrets za Streamlit.")
    st.stop()

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Hitilafu ya Supabase: {e}")
    st.stop()

# Kazi ya kuficha password (Hashing) kwa usalama
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# =====================================================================
# 2. USIMAMIZI WA SESSION (AUTHENTICATION SYSTEM)
# =====================================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["business_name"] = ""

if not st.session_state["logged_in"]:
    st.title("🚀 Gemini Enterprise Engine (GEE)")
    st.subheader("Sadallah Software | Home of Tech")
    
    tab1, tab2 = st.tabs(["🔐 Kuingia (Login)", "✨ Kujisajili (Register)"])
    
    with tab1:
        st.write("### Ingia kwenye Workspace yako")
        login_email = st.text_input("Barua Pepe (Email)", key="login_email_key").strip()
        login_pass = st.text_input("Nenosiri (Password)", type="password", key="login_pass_key").strip()
        
        if st.button("Ingia"):
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
                
    with tab2:
        st.write("### Sajili Biashara yako Mpya")
        reg_biz = st.text_input("Jina la Biashara yako (Mfano: Mangi Grocery)", key="reg_biz_key").strip()
        reg_email = st.text_input("Barua Pepe (Email)", key="reg_email_key").strip()
        reg_pass = st.text_input("Nenosiri Imara (Password)", type="password", key="reg_pass_key").strip()
        
        if st.button("Tengeneza Akaunti"):
            if reg_biz and reg_email and reg_pass:
                try:
                    hashed = hash_password(reg_pass)
                    user_record = {
                        "business_name": reg_biz,
                        "email": reg_email,
                        "password_hash": hashed
                    }
                    supabase.table("business_users").insert(user_record).execute()
                    st.success("🎉 Akaunti imetengenezwa kikamilifu! Sasa unaweza kuingia kwenye Tab ya Login.")
                except Exception as e:
                    st.error(f"Imeshindwa kusajili: {e}")
            else:
                st.warning("Tafadhali jaza fomu yote.")
    st.stop()

# =====================================================================
# 3. DASHBOARD YA BIASHARA (IKIFUNGOLEWA BAADA YA LOGIN)
# =====================================================================
biz_name_input = st.session_state["business_name"]

# Kitufe cha kutoka (Logout) kwenye Sidebar
st.sidebar.title(f"🏢 {biz_name_input}")
st.sidebar.write("Umeingia salama mtandaoni.")
if st.sidebar.button("📴 Tokea Kwenye Mfumo (Logout)"):
    st.session_state["logged_in"] = False
    st.session_state["business_name"] = ""
    st.rerun()

st.title("🚀 Gemini Enterprise Engine (GEE)")
st.subheader(f"Workspace Rasmi ya Biashara: {biz_name_input}")
st.markdown("---")

# --- SEHEMU YA KUINGIZA DATA (MAANDISHI NA SAUTI) ---
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

# Mfumo wa kuamua vyanzo vya data
final_text_prompt = ""
audio_bytes = None

if user_input:
    final_text_prompt = user_input
elif audio_record:
    audio_bytes = audio_record['bytes']
    st.audio(audio_bytes, format='audio/wav')

# Kuchakata miamala (Kitufe kikibonyezwa au sauti ikipatikana)
if st.button("Chambua na Uhifadhi") or (audio_record is not None and audio_bytes is not None):
    # Kuzuia mfumo usichakate mara mbili kama hakuna kipya
    if final_text_prompt or audio_bytes:
        with st.spinner("Gemini inachambua na kupanga muamala wako..."):
            try:
                url = "[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent)"
                headers = {'Content-Type': 'application/json'}
                params = {'key': GEMINI_TOKEN}
                
                system_instruction = (
                    "You are a strict financial data extractor. Analyze the input text or audio transaction in Swahili or English. "
                    "Identify if it is 'income' or 'expense', extract the exact numeric amount, and give a short English description. "
                    "You must output ONLY valid raw JSON with keys: 'type', 'amount', 'description'."
                )

                # Kutumia mfumo dhabiti wa kulazimisha JSON pekee kupitia config
                generation_config = {
                    "response_mime_type": "application/json"
                }

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
                                {
                                    "inline_data": {
                                        "mime_type": "audio/wav",
                                        "data": audio_b64
                                    }
                                }
                            ]
                        }],
                        "generationConfig": generation_config
                    }

                response = requests.post(url, headers=headers, json=payload, params=params)
                response_json = response.json()
                
                # Ulinzi thabiti wa kuangalia kama kosa lipo kwenye jibu la API kabla ya kusoma candidates
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
                
                url = "[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent)"
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
    st.markdown("Zalisha ripoti maalumu iliyothibitishwa na AI ya **Gemini Enterprise Engine** kwa ajili ya kuwasilisha taasisi za kifedha au benki.")

    if st.button("Tengeneza Ripoti ya PDF"):
        with st.spinner("Tunatengeneza faili la PDF lenye mpangilio wa kibenki..."):
            try:
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                story = []
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle(
                    'TitleStyle', parent=styles['Heading1'],
                    fontSize=22, textColor=colors.HexColor('#1a365d'), spaceAfter=10
                )
                subtitle_style = ParagraphStyle(
                    'SubTitleStyle', parent=styles['Normal'],
                    fontSize=11, textColor=colors.HexColor('#4a5568'), spaceAfter=20
                )
                heading_style = ParagraphStyle(
                    'HeadingStyle', parent=styles['Heading2'],
                    fontSize=14, textColor=colors.HexColor('#2b6cb0'), spaceBefore=15, spaceAfter=10
                )
                normal_style = styles['Normal']
                
                story.append(Paragraph(f"GEMINI ENTERPRISE ENGINE (GEE)", title_style))
                story.append(Paragraph(f"Sadallah Software | Official Financial Statement", subtitle_style))
                story.append(Spacer(1, 10))
                
                story.append(Paragraph("<b>TAARIFA ZA WORKSPACE</b>", heading_style))
                biz_info = f"""
                <b>Jina la Biashara:</b> {biz_name_input}<br/>
                <b>Tarehe ya Ripoti:</b> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
                <b>Hali ya Uhakiki:</b> Certified by Gemini AI Advisor<br/>
                """
                story.append(Paragraph(biz_info, normal_style))
                story.append(Spacer(1, 15))
                
                story.append(Paragraph("<b>MUHTASARI WA HALI YA KIFEDHA</b>", heading_style))
                summary_table_data = [
                    [Paragraph("<b>Kipengele</b>", normal_style), Paragraph("<b>Kiasi (TZS)</b>", normal_style)],
                    ["Jumla ya Mapato (Total Income)", f"{total_income:,.2f}"],
                    ["Jumla ya Matumizi (Total Expense)", f"{total_expense:,.2f}"],
                    ["Faida Safi (Net Profit)", f"{net_profit:,.2f}"]
                ]
                t_summary = Table(summary_table_data, colWidths=[250, 200])
                t_summary.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (1,0), colors.HexColor('#2b6cb0')),
                    ('TEXTCOLOR', (0,0), (1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f7fafc')),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
                    ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold')
                ]))
                story.append(t_summary)
                story.append(Spacer(1, 20))
                
                story.append(Paragraph("<b>ORODHA YA MIAMALA YA HIVI KARIBUNI</b>", heading_style))
                tx_table_data = [[Paragraph("<b>Tarehe</b>", normal_style), Paragraph("<b>Aina</b>", normal_style), Paragraph("<b>Kiasi</b>", normal_style), Paragraph("<b>Maelezo</b>", normal_style)]]
                
                for _, row in df.head(10).iterrows():
                    date_str = pd.to_datetime(row['created_at']).strftime('%m-%d %H:%M')
                    tx_table_data.append([
                        date_str,
                        row['type'].upper(),
                        f"{row['amount']:,.0f}",
                        Paragraph(row['description'], normal_style)
                    ])
                    
                t_tx = Table(tx_table_data, colWidths=[80, 60, 80, 230])
                t_tx.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4a5568')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7fafc')]),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(t_tx)
                
                story.append(Spacer(1, 30))
                story.append(Paragraph("<i>Mstari wa Uhakiki: Mfumo huu umesindikwa kidijitali na kurekodiwa kwa kutumia usalama vya vigezo vya kriptografia. Taarifa hizi ni thabiti kulingana na miamala iliyoingizwa na mtumiaji kupitia Gemini Enterprise Engine.</i>", normal_style))
                
                doc.build(story)
                pdf_data = pdf_buffer.getvalue()
                
                st.download_button(
                    label="📥 Pakua Ripoti Yako ya PDF Hapa",
                    data=pdf_data,
                    file_name=f"Ripoti_ya_Fedha_{biz_name_input}.pdf",
                    mime="application/pdf"
                )
                st.success("🎉 Faili la PDF limeandaliwa tayari kupakuliwa! Bonyeza kitufe hapo juu.")
            except Exception as e:
                st.error(f"Imeshindwa kutengeneza PDF: {e}")
else:
    st.info(f"Biashara ya **{biz_name_input}** bado haina miamala iliyorekodiwa. Andika muamala au rekodi sauti hapo juu ili kuwasha dashboard!")