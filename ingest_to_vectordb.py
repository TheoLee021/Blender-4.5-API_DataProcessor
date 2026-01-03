import json
import os
from typing import Iterator, Dict, Any
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()  # Load environment variables from .env file

# Configuration
JSONL_FILE = "parsed_blender_api.jsonl"
CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "blender_api"
BATCH_SIZE = 1000

def create_rich_text(entry: Dict[str, Any]) -> str:
    """
    Constructs a comprehensive Markdown string for embedding.
    Markdown structure helps LLMs understand the context better.
    """
    # 1. Header & Identity
    parts = [
        f"# API Reference: {entry.get('id', 'N/A')}",
        f"- Type: {entry.get('type', 'N/A')}",
        f"- Name: {entry.get('name', 'N/A')}",
    ]
    
    # 2. Description
    if entry.get('description'):
        parts.append(f"\n## Description\n{entry['description']}")

    # 3. Signature (Code Block)
    if entry.get('signature'):
        parts.append(f"\n## Signature\n```python\n{entry['signature']}\n```")
    
    # 4. Parameters
    if entry.get('parameters'):
        params = entry['parameters']
        parts.append("\n## Parameters")
        if isinstance(params, list):
            for p in params:
                parts.append(f"- {p}")
        else:
            parts.append(f"- {params}")

    # 5. Return Type
    if entry.get('return_type'):
        parts.append(f"\n## Return Type\n- {entry['return_type']}")
        
    # 6. Code Examples (High Priority for RAG)
    if entry.get('code_examples'):
        examples = entry['code_examples']
        parts.append("\n## Example Code")
        if isinstance(examples, list):
            for ex in examples:
                parts.append(f"```python\n{ex}\n```")
        else:
            parts.append(f"```python\n{examples}\n```")
        
    return "\n".join(parts)

def document_generator(file_path: str) -> Iterator[Document]:
    """
    [Memory Optimization]
    Yields documents one by one using a generator.
    Never loads the entire dataset into memory at once.
    """
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            
            try:
                entry = json.loads(line)
                
                # Create Metadata
                # Improved module extraction logic
                api_id = str(entry.get("id", ""))
                module_name = "unknown"
                if api_id:
                    parts_split = api_id.split(".")
                    # Extract 'bpy.ops' or 'bmesh.ops' instead of just 'bpy'
                    if len(parts_split) >= 2:
                        module_name = f"{parts_split[0]}.{parts_split[1]}"
                    else:
                        module_name = parts_split[0]

                metadata = {
                    "id": api_id,
                    "type": str(entry.get("type", "")),
                    "name": str(entry.get("name", "")),
                    "module": module_name,
                    "url": str(entry.get("url", "")), # Parsed URL with anchor
                    "has_code": bool(entry.get("code_examples")),
                }
                
                # Create Page Content
                page_content = create_rich_text(entry)
                
                yield Document(page_content=page_content, metadata=metadata)
                
            except json.JSONDecodeError as e:
                print(f"Error parsing line {i+1}: {e}")

def main():
    # Check for API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    # Initialize Embeddings
    print("Initializing OpenAI Embeddings...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Initialize VectorDB (Persistent Client)
    print(f"Initializing ChromaDB at {CHROMA_DB_DIR}...")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    # Ingest in Batches (Stream Processing)
    batch = []
    total_count = 0
    
    print(f"Starting stream ingestion...")
    
    for doc in document_generator(JSONL_FILE):
        batch.append(doc)
        
        # When batch is full, push to DB and clear memory
        if len(batch) >= BATCH_SIZE:
            try:
                vectorstore.add_documents(documents=batch)
                total_count += len(batch)
                print(f"Ingested {total_count} documents...")
            except Exception as e:
                print(f"Error ingesting batch at count {total_count}: {e}")
            finally:
                batch = [] # Critical: Clear memory

    # Ingest remaining documents
    if batch:
        try:
            vectorstore.add_documents(documents=batch)
            total_count += len(batch)
            print(f"Ingested remaining {len(batch)} documents.")
        except Exception as e:
            print(f"Error ingesting final batch: {e}")

    print(f"Ingestion complete. Total documents: {total_count}")

if __name__ == "__main__":
    main()
