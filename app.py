import streamlit as st
import json
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests

st.set_page_config(page_title="Gemini Enterprise Engine", layout="wide")

# =====================================================================
# 1. FUNGUO ZAKO RASMI KUTOKA STREAMLIT SECRETS
# =====================================================================
SUPABASE_URL = "https://ndpuprbdulfrjwxakfmm.supabase.co"
try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_TOKEN = st.secrets["GEMINI_TOKEN"]
except Exception:
    st.error("Tafadhali hakikisha umeweka SUPABASE_KEY na GEMINI_TOKEN kwenye Secrets za Streamlit au .env")
    st.stop()

# Kuanzisha Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Hitilafu ya kuanzisha Supabase: {e}")
    st.stop()

st.title("🚀 Gemini Enterprise Engine (GEE)")
st.subheader("Sadallah Software | Home of Tech")

st.markdown("---")

# =====================================================================
# 2. MFUMO WA LOGIN / USILIMISHI WA BIASHARA (MULTI-TENANCY)
# =====================================================================
st.sidebar.write("## 🔐 Ingia Kwenye Biashara Yako")
st.sidebar.info("Kama wewe ni mteja mpya, andika jina la biashara yako na PIN mpya ili kujiandikisha moja kwa moja.")

biz_name_input = st.sidebar.text_input("Jina la Biashara", value="Sadallah Software").strip()
biz_pin_input = st.sidebar.text_input("PIN ya Siri (Namba 4)", value="1234", type="password").strip()

if not biz_name_input or not biz_pin_input:
    st.warning("🔒 Tafadhali weka Jina la Biashara na PIN kwenye sidebar ili kuona dashboard yako.")
    st.stop()

st.write(f"### 🏢 Workspace ya Biashara: **{biz_name_input}**")

# --- SEHEMU YA KUINGIZA DATA ---
st.write("### 🗣️ Rekodi Muamala kwa Lugha ya Kawaida (Kiswahili/English)")
user_input = st.text_input(label="Andika muamala wako hapa...", placeholder="Mfano: Leo nimeuza hereni pea 3 kwa elfu 15")

if st.button("Chambua na Uhifadhi"):
    if user_input:
        with st.spinner("Gemini inachambua na kuhifadhi muamala wako..."):
            try:
                prompt = (
                    f"Extract financial transaction data from this text: '{user_input}'. "
                    "Identify if it is 'income' or 'expense', the exact numeric amount, and a short English description. "
                    "Return ONLY a valid JSON object exactly like this, no markdown, no backticks: "
                    "{{\n  \"type\": \"income\",\n  \"amount\": 15000,\n  \"description\": \"Earrings sale\"\n}}"
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
                    "raw_ai_prompt": user_input,
                    "business_name": biz_name_input,
                    "business_pin": biz_pin_input
                }
                
                supabase.table("transactions").insert(db_record).execute()
                st.success(f"🎉 Muamala wa {biz_name_input} umetafsiriwa na kuhifadhiwa kikamilifu!")
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
    # Hapa tunavuta data za biashara iliyoingia tu (biz_name_input)
    res = supabase.table("transactions")\
                  .select("*")\
                  .eq("business_name", biz_name_input)\
                  .order("created_at", desc=True)\
                  .execute()
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
    st.info(f"Bofya kitufe cha chini ili kuruhusu Gemini ichanganue data za {biz_name_input} na ikupe ushauri.")
    
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
    st.info(f"Biashara ya **{biz_name_input}** bado haina miamala iliyorekodiwa. Andika muamala wa kwanza hapo juu ili kuwasha dashboard!")