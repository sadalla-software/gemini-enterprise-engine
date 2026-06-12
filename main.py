import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Gemini Enterprise Engine")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Client ya Google 2026 SDK
ai_client = genai.Client()

class UserPrompt(BaseModel):
    user_id: str
    prompt_text: str

@app.post("/api/process-transaction")
async def process_transaction(data: UserPrompt):
    try:
        system_instruction = (
            "You are a financial data extractor for African SMEs. "
            "Analyze the input and extract transaction type ('income' or 'expense'), "
            "the exact numeric amount, and a short summary in English. "
            "Return STRICTLY a valid JSON object with keys: 'type', 'amount', 'description'."
        )
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=data.prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            ),
        )
        
        extracted_data = json.loads(response.text.strip())
        
        db_record = {
            "user_id": data.user_id,
            "type": extracted_data["type"],
            "amount": float(extracted_data["amount"]),
            "description": extracted_data["description"],
            "raw_ai_prompt": data.prompt_text
        }
        
        result = supabase.table("transactions").insert(db_record).execute()
        return {"status": "success", "extracted_data": extracted_data, "database_record": result.data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Tunatumia localhost kulazimisha Windows kuelewa mawasiliano ya ndani moja kwa moja
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)