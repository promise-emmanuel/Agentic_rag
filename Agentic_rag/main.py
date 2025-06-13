from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
import asyncio
import os, uvicorn
from dotenv import load_dotenv, find_dotenv
from typing import Union

from fastapi import FastAPI, HTTPException

# Load environment variables
_ = load_dotenv(find_dotenv())

app = FastAPI()

# Create a RAG tool using LlamaIndex
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

@app.post("/query")
async def query_llama_index(query: str): #-> Union[str, dict]:
    """
    Endpoint to query the LlamaIndex vector store.
    """
    try:
        response = query_engine.query(query)
        return {"response": str(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":    
    uvicorn.run(app, host="0.0.0.0", port=8000) #reload=True)
