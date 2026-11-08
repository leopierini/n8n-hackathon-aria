import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
import uvicorn
import datetime

# Initialize FastAPI app
app = FastAPI(title="ARIA Local Backend Mock")

# Add CORS middleware to allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Client (Will fall back to mock responses if no real key is provided)
api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_to_prevent_startup_crash")
client = AsyncOpenAI(api_key=api_key)

# Define request model for chat
class ChatMessage(BaseModel):
    message: str

# In-memory "knowledge base" to simulate RAG
MOCK_KNOWLEDGE_BASE = [
    "Brevetto EP2024-183421 (Esmaltes Ejemplo S.L., 14 feb 2024): Finitura opaca a bassa riflettanza per gres porcellanato con precursore di zirconio a 1180°C.",
    "Normativa EN 14411:2023 (EUR-Lex): Modifica parametri di assorbimento acqua per piastrelle BIa. Include nuove specifiche per formati fino a 320x160 cm.",
    "Paper JECS Vol. 44 (8 gen 2024): Studio sulla stabilizzazione della zirconia con ossidi di terre rare per formulazioni sotto 1100°C.",
    "Report Cersaie 2024 (Qualicer Proceedings): Analisi dei trend estetici. La finitura silk supera il mat puro nelle preferenze dei buyer europei."
]

@app.post("/api/chat")
async def chat_endpoint(request: ChatMessage):
    """
    Mock endpoint for the chat interface.
    Uses OpenAI to generate a response based on the user's message and a mocked knowledge base.
    """
    user_message = request.message
    
    # Check if OpenAI API key is configured
    if not os.environ.get("OPENAI_API_KEY"):
        # Fallback to a hardcoded response if no key is present to keep the UI working
        return JSONResponse(content={
            "response": "Al momento la mia intelligenza artificiale non è configurata (chiave API mancante). Tuttavia, basandomi sul mio database, posso confermare che il brevetto EP2024-183421 riguarda finiture opache.",
            "sources": [{"name": "Knowledge base locale", "type": "Database"}],
            "timestamp": datetime.datetime.now().strftime("%H:%M")
        })

    try:
        # Construct the context from the mocked knowledge base
        context = "\n".join([f"- {item}" for item in MOCK_KNOWLEDGE_BASE])
        
        system_prompt = f"""
        Sei ARIA (Autonomous Research Intelligence Assistant), un assistente proattivo per la ricerca e sviluppo nel settore ceramico.
        Rispondi alle domande in italiano in modo professionale, conciso e pertinente.
        Se pertinente, usa questo contesto per formulare la tua risposta:
        {context}
        """

        response = await client.chat.completions.create(
            model="gpt-4o",  # or gpt-3.5-turbo if you prefer
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.3
        )

        reply_text = response.choices[0].message.content
        
        # In a real app, you would extract actual sources used by the LLM
        mock_sources = [{"name": "Ricerca AI", "type": "Sintesi"}]

        return JSONResponse(content={
            "response": reply_text,
            "sources": mock_sources,
            "timestamp": datetime.datetime.now().strftime("%H:%M")
        })

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return JSONResponse(content={
            "response": "Ho riscontrato un errore di connessione ai miei sistemi cognitivi. Riprova più tardi.",
            "sources": [],
            "timestamp": datetime.datetime.now().strftime("%H:%M")
        }, status_code=500)

@app.post("/api/upload")
async def upload_endpoint(file: UploadFile = File(...)):
    """
    Mock endpoint for document uploads.
    """
    print(f"Received file: {file.filename}")
    
    # In a real scenario, you would process the file (e.g., extract text, create embeddings)
    # Here we just mock a successful processing
    
    return JSONResponse(content={
        "status": "success",
        "message": f"Documento '{file.filename}' ricevuto ed elaborato con successo.",
        "filename": file.filename,
        "size": "Mock size"
    })

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
