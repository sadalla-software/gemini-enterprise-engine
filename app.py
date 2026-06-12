import streamlit as st
import json
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests
import hashlib
import base64

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
SUPABASE_URL = "https://ndpuprbdulfrjwxakfmm.supabase.co"
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
                    st.error(f"Hitilafu: {e}")
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
                    st.error(f"Imeshindwa kusajili: Jina la biashara au Email imeshachukuliwa tayari.")
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
if st.button("Chambua na Uhifadhi") or audio_bytes is not None:
    if final_text_prompt or audio_bytes:
        with st.spinner("Gemini inachambua na kupanga muamala wako..."):
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                headers = {'Content-Type': 'application/json'}
                params = {'key': GEMINI_TOKEN}
                
                system_instruction = (
                    "You are a strict financial data extractor. Analyze the input (text or audio transaction in Swahili/English). "
                    "Identify if it is 'income' or 'expense', extract the exact numeric amount, and give a short English description. "
                    "Return ONLY a valid JSON object exactly like this, no markdown backticks, no extra text: "
                    "{\n  \"type\": \"income\",\n  \"amount\": 15000,\n  \"description\": \"Earrings sale\"\n}"
                )

                if final_text_prompt:
                    prompt = f"{system_instruction}\n\nTransaction text: '{final_text_prompt}'"
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    response = requests.post(url, headers=headers, json=payload, params=params)
                
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
                        }]
                    }
                    response = requests.post(url, headers=headers, json=payload, params=params)

                response_json = response.json()
                ai_text = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                if ai_text.startswith("```json"):
                    ai_text = ai_text.replace("
```json", "").replace("```", "").strip()
                elif ai_text.startswith("```"):
                    ai_text = ai_text.replace("
```", "").strip()
                    
                extracted_data = json.loads(ai_text)
                
                db_record = {
                    "type": extracted_data["type"],
                    "amount": float(extracted_data["amount"]),
                    "description": extracted_data["description"],
                    "raw_ai_prompt": final_text_prompt if final_text_prompt else "[Sauti ya Kiswahili Ilichakatwa]",
                    "business_name": biz_name_input
                }
                
                supabase.table("transactions").insert(db_record).execute()
                st.success(f"🎉 Muamala wa {biz_name_input} umetafsiriwa na kuhifadhiwa!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Kuna kitu kimefeli wakati wa kuchakata: {e}")
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
                headers = {'Content-Type': 'application/json'}
                params = {'key': GEMINI_TOKEN}
                
                advisor_response = requests.post(url, headers=headers, json=payload, params=params)
                advisor_json = advisor_response.json()
                
                advisor_text = advisor_json['candidates'][0]['content']['parts'][0]['text']
                
                st.success(f"🎯 Ushauri Rasmi kutoka kwa Gemini Advisor kwenda kwa {biz_name_input}:")
                st.write(advisor_text)
                
            except Exception as e:
                st.error(f"Imeshindwa kuzalisha ushauri wa AI: {e}")
else:
    st.info(f"Biashara ya **{biz_name_input}** bado haina miamala iliyorekodiwa. Andika muamala au rekodi sauti hapo juu ili kuwasha dashboard!")