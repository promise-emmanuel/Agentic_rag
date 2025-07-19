import os, json, shutil
import boto3
from botocore.exceptions import ClientError

# Ensure the environment variables are set from AWS Secrets Manager
# This function fetches the secret and exports it as environment variables
# It should be called once at the start of the application
# This is useful for serverless environments like AWS Lambda or when running in a container
def get_secret_and_export():
    secret_name = "Askpromise/OpenAIKey"
    region_name = "eu-north-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        resp = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # Log or handle the error as needed
        raise

    # Parse the JSON string into a dict
    secret_dict = json.loads(resp['SecretString'])

    # Export each key as an environment variable
    for key, value in secret_dict.items():
        os.environ[key] = value

# Invoke it once at import time
# get_secret_and_export()



# app 
import os
from dotenv import load_dotenv,  find_dotenv
from openai import OpenAI as OpenAIClient
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Document, StorageContext, load_index_from_storage

from llama_index.core.node_parser import SentenceWindowNodeParser

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.core import Settings

# adding postprocessor and reranking to build query engine
from llama_index.core.indices.postprocessor import MetadataReplacementPostProcessor
from llama_index.postprocessor.cohere_rerank import CohereRerank

from llama_index.core.postprocessor import SimilarityPostprocessor
from source_code.prompt import Prompt

from pinecone import Pinecone, ServerlessSpec
# import pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore


# uncomment to run locally
_ = load_dotenv(find_dotenv())


client = OpenAIClient()

MODEL = os.environ["MODEL"]
EMBED_MODEL = os.environ["EMBED_MODEL"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]

pc = Pinecone(api_key=PINECONE_API_KEY)



node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=3,  # number of sentences in each node
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )
    

# metadata replacement replaces the retrieved chunks.text with the metadata (sentence window).
postprocess = MetadataReplacementPostProcessor(
    target_metadata_key="window"
)


cohere_rerank = CohereRerank(
    api_key=os.environ["COHERE_API_KEY"], 
    top_n=4,
)




def load_document(Data):
    """Load a document from the specified file path."""
    documents = SimpleDirectoryReader(input_files=Data).load_data()
    
    # merge into a single large document rather than one document per page
    document = Document(text="\n\n".join([doc.text for doc in documents]))
    
    return document

def build_index(docs):
    """Build a vector store index from the provided documents.""" 

    Settings.llm = LlamaOpenAI(model=MODEL)
    Settings.embed_model = OpenAIEmbedding(model=EMBED_MODEL)
    Settings.node_parser = node_parser
    nodes = node_parser.get_nodes_from_documents([docs])

    index_name = "askpromise"
    if index_name not in pc.list_indexes():
        print("building index")
        pc.create_index(
        name=index_name,
        dimension=1536,   #openai ada-002 embedding size
        metric="euclidean",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    
    print("loading index")
    pinecone_index = pc.Index(index_name)
        
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    sentence_window_index = VectorStoreIndex(nodes, storage_context=storage_context)
    
    return sentence_window_index
    
    # if not os.path.exists(Storage_dir):
    #     os.makedirs(Storage_dir)
    
    #     #create a fresh storage context
    #     storage_context = StorageContext.from_defaults()
    
    #     # build the index from nodes
    #     sentence_window_index = VectorStoreIndex(
    #         nodes, storage_context=storage_context)

    #     # persist both the vector store and docstore so u
    #     sentence_window_index.storage_context.persist(persist_dir=Storage_dir)
    
    # return sentence_window_index
    
    
def load_index():
    """Load the index from the storage context."""     
    
    try:
        # List available indexes and verify our index exists
        available_indexes = pc.list_indexes()
        print("Available indexes:", available_indexes)
        
        index_name = "askpromise"
        if index_name not in available_indexes:
            print()
            print("I can't connect to pinecone")
            
        # Connect to existing index
        pinecone_index = pc.Index(index_name)

        # Initialize vector store with Pinecone
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        
        # Create storage context with the vector store
        # storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Load the index from vector store
        sentence_window_index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            # storage_context=storage_context
        )
        
        # print(f"Successfully loaded index '{index_name}' from Pinecone")
        # return pinecone_index
        return sentence_window_index

    except Exception as e:
        print(f"Error loading Pinecone index: {str(e)}")
        raise

def create_engine(index):
    """Create a query engine from the provided index."""
    
    sentence_window_query_engine = index.as_retriever(
        similarity_top_k=12,  # number of top results to return
        node_postprocessors=[postprocess, cohere_rerank],  # apply postprocessing and reranking
    )
    
    return sentence_window_query_engine

# function to get a response based on the retrieved context and query
def generate_response(retrieved_context, query):
    """Generate a response based on the retrieved context and query."""
    
    refined_context = []

    # First, filter the retrieved context using similaritypostprocessor
    processor = SimilarityPostprocessor(similarity_cutoff=0.40)
    filtered_context = processor.postprocess_nodes(retrieved_context)
     
    #next we want to make sure the contexts are not empty, then also retrieve the metadata and store it in a list

    if not filtered_context:
        print("No contexts found")
    else:
        # If not empty, process each context
        for context in filtered_context:
            refined_context.append(context.metadata["window"])
        
    context_length = len(refined_context)
    print("Context Length:", context_length)
    print("Contexts found:", bool(filtered_context))  # Print whether contexts were found
    print(refined_context[0])
    
    
    # Create a prompt object
    prompt = Prompt(Context=refined_context, Query=query)
    
    # Get the response message
    message = prompt.get_prompts()
    
    # Use OpenAI to get the AI response
    completion = client.chat.completions.create(model=MODEL, messages=message)
    return completion.choices[0].message.content