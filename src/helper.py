from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings



# Extract Data :

def load_pdf_files(data):
    loader = DirectoryLoader(data , glob ="*.pdf" , loader_cls=PyPDFLoader)
 
    documents = loader.load()
    return documents


def filter_to_minimal_docs(documents: List[Document]) -> List[Document]:
    """
    Given a list of Document objects, return a new list of Document
    objects containing only 'source' in metadata and the original
    page_content.
    """

    minimal_docs: List[Document] = []

    for doc in documents:
        src = doc.metadata.get("source")

        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src}
            )
        )

    return minimal_docs


# Chunking : 

def text_split(minimal_docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50,
        length_function = len
    )
    text_chunks = text_splitter.split_documents(minimal_docs)
    return text_chunks


# Embeddings :

def download_embedding():
    model_name = "BAAI/bge-large-en-v1.5"

    embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
   )    

    return embeddings


