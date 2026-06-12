import streamlit as st
import json
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests

st.set_page_config(page_title="Gemini Enterprise Engine", layout="wide")

# =====================================================================
# 1. FUNGUO ZAKO RASMI
# =====================================================================
SUPABASE_URL = "https://ndpuprbdulfrjwxakfmm.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


# Ufunguo wako wa AQ wa Google AI Studio
GEMINI_TOKEN = st.secrets["GEMINI_TOKEN"]

# Kuanzisha Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Hitilafu ya kuanzisha Supabase: {e}")

st.title("🚀 Gemini Enterprise Engine (GEE)")
st.subheader("Sadallah Software | Home of Tech")

# --- SEHEMU YA KUINGIZA DATA ---
st.write("### 🗣️ Rekodi Muamala kwa Lugha ya Kawaida (Kiswahili/English)")
user_input = st.text_input(label="Andika muamala wako hapa...", placeholder="Mfano: Leo nimeuza website kwa laki tano na nusu")

if st.button("Chambua na Uhifadhi"):
    if user_input:
        with st.spinner("Gemini inachambua na kuhifadhi muamala wako..."):
            try:
                prompt = (
                    f"Extract financial transaction data from this text: '{user_input}'. "
                    "Identify if it is 'income' or 'expense', the exact numeric amount, and a short English description. "
                    "Return ONLY a valid JSON object exactly like this, no markdown, no backticks: "
                    "{{\n  \"type\": \"income\",\n  \"amount\": 550000,\n  \"description\": \"Website sale\"\n}}"
                )
                
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                headers = {'Content-Type': 'application/json'}
                params = {'key': GEMINI_TOKEN}
                
                response = requests.post(url, headers=headers, json=payload, params=params)
                response_json = response.json()
                
                ai_text = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                extracted_data = json.loads(ai_text)
                
                db_record = {
                    "type": extracted_data["type"],
                    "amount": float(extracted_data["amount"]),
                    "description": extracted_data["description"],
                    "raw_ai_prompt": user_input
                }
                
                supabase.table("transactions").insert(db_record).execute()
                st.success("🎉 Muamala umetafsiriwa na kuhifadhiwa kikamilifu!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Kuna kitu kimefeli wakati wa kuchakata: {e}")
    else:
        st.warning("Tafadhali andika maelezo kwanza.")

st.markdown("---")

# --- SEHEMU YA DASHBOARD & GRAPH ---
st.write("### 📊 Mwenendo wa Biashara Yako")

data = []
try:
    res = supabase.table("transactions").select("*").order("created_at", desc=True).execute()
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
                 title="Mchanganuo wa Miamala kwa Muda",
                 labels={"amount": "Kiasi (TZS)", "created_at": "Tarehe"},
                 color_discrete_map={"income": "#2ecc71", "expense": "#e74c3c"})
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df[["created_at", "type", "amount", "description", "raw_ai_prompt"]], use_container_width=True)
    
    # =====================================================================
    # AWAMU YA 2: AI BUSINESS ADVISOR (MTAMBO MPYA)
    # =====================================================================
    st.markdown("---")
    st.write("### 🤖 AI Business Advisor")
    st.info("Bofya kitufe cha chini ili kuruhusu Gemini ichanganue data zako zote na ikupe ushauri wa kijasusi.")
    
    if st.button("Changanua Biashara na Upe Ushauri"):
        with st.spinner("Gemini inasoma miamala yako yote na kuandaa ushauri..."):
            try:
                # Tunatengeneza muhtasari wa data kwenda kwa Gemini
                history_str = df[["type", "amount", "description"]].to_string(index=False)
                
                advisor_prompt = (
                    f"You are the Lead Financial AI Advisor for Sadallah Software. Analyze this business transaction history:\n\n"
                    f"{history_str}\n\n"
                    f"Financial Summary:\n"
                    f"- Total Income: TZS {total_income}\n"
                    f"- Total Expense: TZS {total_expense}\n"
                    f"- Net Profit: TZS {net_profit}\n\n"
                    f"Provide a brief, highly actionable strategic advice in Swahili for the business owner. "
                    f"Highlight where they are losing money or doing well, and give 2 clear steps to increase profit next month. "
                    f"Keep the tone encouraging, professional, and friendly."
                )
                
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                payload = {"contents": [{"parts": [{"text": advisor_prompt}]}]}
                headers = {'Content-Type': 'application/json'}
                params = {'key': GEMINI_TOKEN}
                
                advisor_response = requests.post(url, headers=headers, json=payload, params=params)
                advisor_json = advisor_response.json()
                
                advisor_text = advisor_json['candidates'][0]['content']['parts'][0]['text']
                
                # Kuonyesha ushauri kwenye kadi safi ya kijani
                st.success("🎯 Ushauri Rasmi kutoka kwa Gemini Advisor:")
                st.write(advisor_text)
                
            except Exception as e:
                st.error(f"Imeshindwa kuzalisha ushauri wa AI: {e}")
else:
    st.info("Bado hakuna miamala iliyorekodiwa ili kutoa ushauri.")