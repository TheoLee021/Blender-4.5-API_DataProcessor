import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Configuration
CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "blender_api"

def main():
    # Check for API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    # Initialize Embeddings
    print("Initializing OpenAI Embeddings...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Initialize VectorDB
    print(f"Loading ChromaDB from {CHROMA_DB_DIR}...")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    # Perform Similarity Search
    query = "particle system"
    print(f"Performing similarity search for: '{query}'")
    results = vectorstore.similarity_search(query, k=1)

    if results:
        print("\n--- Most Similar Result ---")
        doc = results[0]
        print(f"Content:\n{doc.page_content}")
        print(f"\nMetadata:\n{doc.metadata}")
    else:
        print("No results found.")

if __name__ == "__main__":
    main()
