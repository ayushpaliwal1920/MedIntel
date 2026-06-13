import json

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import os

from src.helper import download_embedding
from src.prompt import system_prompt

from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder 

from langchain_classic.memory import ConversationBufferMemory

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

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

# ----------------------------------
# Prompt
# ----------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

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

if not os.path.exists("chat_history.json"):
    with open("chat_history.json", "w") as f:
        json.dump([], f)

with open("chat_history.json", "r") as f:
    try:
        chats = json.load(f)
    except:
        chats = []

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/new-chat", methods=["POST"])
def new_chat():

    with open("chat_history.json", "r") as f:
        chats = json.load(f)

    new_id = len(chats) + 1

    chats.append({
        "id": new_id,
        "title": "New Chat",
        "messages": []
    })

    with open("chat_history.json", "w") as f:
        json.dump(chats, f, indent=4)

    memory.clear()

    return jsonify({
        "chat_id": new_id
    })


@app.route("/get", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        user_input = data["message"]

        chat_history = memory.load_memory_variables({})
        
        response = rag_chain.invoke({
            "input": user_input,
            "chat_history": chat_history["chat_history"]
        })

        answer = response["answer"]

        memory.save_context(
            {"input": user_input},
            {"answer": answer}
        )

        # Load old chats
        with open("chat_history.json", "r") as f:
            chats = json.load(f)

        # Create first chat if file is empty
        if len(chats) == 0:
            chats.append({
                "id": 1,
                "title": user_input[:30],
                "messages": []
            })

        # Latest conversation
        chat = chats[-1]

        # Save user message
        chat["messages"].append({
            "role": "user",
            "content": user_input
        })

        # Save AI answer
        chat["messages"].append({
            "role": "assistant",
            "content": answer
        })

        # Write back to file
        with open("chat_history.json", "w") as f:
            json.dump(chats, f, indent=4)

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        return jsonify({
            "answer": f"Error: {str(e)}"
        })
    



@app.route("/history", methods=["GET"])
def history():

    with open("chat_history.json", "r") as f:
        chats = json.load(f)

    return jsonify(chats)


@app.route("/conversation/<int:chat_id>")
def get_conversation(chat_id):

    with open("chat_history.json", "r") as f:
        chats = json.load(f)

    for chat in chats:
        if chat["id"] == chat_id:
            return jsonify(chat)

    return jsonify({"error":"Not found"})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
    )