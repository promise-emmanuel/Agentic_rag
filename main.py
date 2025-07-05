from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
import asyncio
import os, uvicorn
from dotenv import load_dotenv, find_dotenv
from typing import Union


from flask import Flask, request, jsonify, render_template
# from fastapi import FastAPI, HTTPException

# Load environment variables
_ = load_dotenv(find_dotenv())

# app = FastAPI()
app = Flask(__name__)


# Create a RAG tool using LlamaIndex
documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()





# Landing page route (GET only)
@app.route("/", methods=["GET"])
def landing():
    return render_template('index.html')

# Chat page route (GET for chat UI, POST for chat API)
@app.route("/chat", methods=["POST", "GET"])
def chat():
    if request.method == "POST":
        # Accept both form and JSON for flexibility
        query = request.form.get("query") 
        if not query:
            return "No query provided", 400
        response = query_engine.query(query)
        return str(response)
    return render_template('component.html')

if __name__ =="__main__":
    port = int(os.environ.get('port', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)


