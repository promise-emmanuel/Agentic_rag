# import os, json
# import boto3
# from botocore.exceptions import ClientError

# # Ensure the environment variables are set from AWS Secrets Manager
# # This function fetches the secret and exports it as environment variables
# # It should be called once at the start of the application
# # This is useful for serverless environments like AWS Lambda or when running in a container
# def get_secret_and_export():
#     secret_name = "Askpromise/OpenAIKey"
#     region_name = "eu-north-1"

#     # Create a Secrets Manager client
#     session = boto3.session.Session()
#     client = session.client(
#         service_name='secretsmanager',
#         region_name=region_name
#     )

#     try:
#         resp = client.get_secret_value(SecretId=secret_name)
#     except ClientError as e:
#         # Log or handle the error as needed
#         raise

#     # Parse the JSON string into a dict
#     secret_dict = json.loads(resp['SecretString'])

#     # Export each key as an environment variable
#     for key, value in secret_dict.items():
#         os.environ[key] = value

# # Invoke it once at import time
# get_secret_and_export()



# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
# from llama_index.core.agent.workflow import FunctionAgent
# from llama_index.llms.openai import OpenAI
# import asyncio
# import uvicorn
# from dotenv import load_dotenv, find_dotenv
# from typing import Union
# from flask import Flask, request, jsonify, render_template



# # Load environment variables when running locally
# # Uncomment the next line if you have a .env file with your OpenAI API key
# # _ = load_dotenv(find_dotenv())


# # Initialize Flask app
# app = Flask(__name__)

# # Lazy loading
# query_engine = None

# def initialize_query_engine():
#     global query_engine
#     if query_engine is None:
#         print("Loading documents and creating index...")
#         # Create a RAG tool using LlamaIndex
#         documents = SimpleDirectoryReader(input_files=["./data/Pmg_lds.md", "./data/handbook.md"]).load_data()
#         index = VectorStoreIndex.from_documents(documents)
#         query_engine = index.as_query_engine()


# # Landing page route (GET only)
# @app.route("/", methods=["GET"])
# def landing():
#     return render_template('index.html')


# # Chat page route (GET for chat UI, POST for chat API)
# @app.route("/chat", methods=["POST", "GET"])
# def chat():
#     if request.method == "POST":
#         # Ensure query engine is initialized
#         initialize_query_engine()
#         # Accept both form and JSON for flexibility
#         query = request.form.get("query") 
#         if not query:
#             return "No query provided", 400
#         response = query_engine.query(query)
#         return str(response)
#     return render_template('component.html')

# # uncomment to run locally
# # if __name__ =="__main__":
#     # port = int(os.environ.get('port', 3000))
#     # app.run(host='0.0.0.0', port=port, debug=True)



# # def get_secret(name: str, region: str="eu-north-1") -> dict:
# #     client = boto3.client("secretsmanager", region_name=region)
# #     try:
# #         resp = client.get_secret_value(SecretId=name)
# #         return json.loads(resp["SecretString"])
# #     except ClientError as e:
# #         # If decryption fails or no permission, this will raise
# #         raise

# # # Fetch and export into environment
# # secrets = get_secret("AskPromise/OpenAIKey")
# # os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
# # os.environ["MODEL"] = secrets["MODEL"]

