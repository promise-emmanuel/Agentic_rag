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
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()


@app.route("/", methods=["POST", 'GET'])
def index():
    if request.method == "POST":
        query = request.form.get("query")
        response = query_engine.query(query)    
        return render_template('index.html', query=query, response=response)
    return render_template('index.html')

if __name__ =="__main__":
    port = int(os.environ.get('port', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)


