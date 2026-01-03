# Blender API 4.5 Data Processor

This project is a tool that parses Blender Python API 4.5 documentation and ingests it into a vector database (ChromaDB) to be used in systems such as RAG (Retrieval-Augmented Generation).

## Features

1.  Document Selection (`select_docs.py`): Selects only the core API-related documents from the vast Blender documentation.
2.  Document Parsing (`parse_docs.py`): Parses HTML documents to extract structured data such as classes, functions, parameters, and descriptions into JSONL format.
3.  VectorDB Ingestion (`ingest_to_vectordb.py`): Embeds the extracted data and stores it in ChromaDB.
4.  Search Test (`test_query.py`): Executes natural language queries against the stored data to verify search results.

## Prerequisites

- Python: 3.12 or higher
- uv: Python package and project management tool (Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- OpenAI API Key: Required for using text embedding models (e.g., `text-embedding-3-small`).

## Installation

1.  Clone the Repository:
    ```bash
    git clone https://github.com/your-username/BlenderAPI_DataProcessor.git
    cd BlenderAPI_DataProcessor
    ```

2.  Install Dependencies:
    Create a virtual environment and install packages using `uv`.
    ```bash
    uv sync
    ```

3.  Set Environment Variables:
    Create a `.env` file in the root directory and enter your OpenAI API key.
    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    ```

## Usage

### 1. Prepare Blender Documentation
You need to download the official Blender Python API Reference (HTML version).
- Download and extract the documentation.
- Rename the extracted folder to `blender_python_reference_4_5` and place it in the project root.
- (Note: This folder is ignored by `.gitignore`.)

### 2. Select Documents
Copy only the necessary API documents from the full documentation to the `selected_blender_docs` folder.
```bash
uv run select_docs.py
```

### 3. Parse Documents
Parse the selected HTML documents to generate the `parsed_blender_api.jsonl` file.
```bash
uv run parse_docs.py
```

### 4. VectorDB Ingestion
Read the parsed JSONL data and store it as vectors in ChromaDB.
```bash
uv run ingest_to_vectordb.py
```
Upon completion, the `chroma_db` folder will be created.

### 5. Search Test
Query the constructed database to verify that search is working correctly.
```bash
uv run test_query.py
```

## File Structure

- `blender_python_reference_4_5/`: (User provided) Original HTML documentation
- `selected_blender_docs/`: Selected HTML documents
- `parsed_blender_api.jsonl`: Parsed result data
- `chroma_db/`: Generated Chroma Vector Database
- `select_docs.py`: Document selection script
- `parse_docs.py`: HTML parser
- `ingest_to_vectordb.py`: DB ingestion script
- `test_query.py`: Search test script

## License
MIT License
