from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import os

from src.helper import download_embedding
from src.prompt import system_prompt

from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_core.prompts import ChatPromptTemplate

# ----------------------------------
# Load Environment Variables
# ----------------------------------

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")

# ----------------------------------
# Flask App
# ----------------------------------

app = Flask(__name__)

# ----------------------------------
# Embeddings
# ----------------------------------

embeddings = download_embedding()

# ----------------------------------
# Pinecone Vector Store
# ----------------------------------

docsearch = PineconeVectorStore.from_existing_index(
    index_name="medintel-chatbot",
    embedding=embeddings
)

retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# ----------------------------------
# LLM
# ----------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)

# ----------------------------------
# Prompt
# ----------------------------------

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}")
    ]
)

# ----------------------------------
# RAG Chain
# ----------------------------------

question_answer_chain = create_stuff_documents_chain(
    llm,
    prompt
)

rag_chain = create_retrieval_chain(
    retriever,
    question_answer_chain
)

# ----------------------------------
# Routes
# ----------------------------------

@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/get", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        user_input = data["message"]

        response = rag_chain.invoke(
            {"input": user_input}
        )

        return jsonify(
            {
                "answer": response["answer"]
            }
        )

    except Exception as e:

        return jsonify(
            {
                "answer": f"Error: {str(e)}"
            }
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
    )