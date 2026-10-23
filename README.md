# NOTE
This repo was forked from [JackKuo666's repo](https://github.com/JackKuo666/PubTator-MCP-Server). This fork serves to update the core functionality, initalise global variables from another file for organisation, and replace FastMCP with MCP v2.3 as FastMCP is deprecated.

# PubTator MCP Server
🔍 A biomedical literature annotation and relationship mining server based on PubTator3, providing convenient access through the MCP interface.

PubTator MCP Server provides AI assistants with access to the PubTator3 biomedical literature annotation system through the Model Context Protocol (MCP). It allows AI models to programmatically search scientific literature, obtain annotation information, and analyze entity relationships.

## ✨ Core Features
- 🔎 Literature Annotation Export: Support exporting PubTator annotation results in multiple formats ✅
- 🚀 Entity ID Lookup: Query standard identifiers for biological concepts through free text ✅
- 📊 Relationship Mining: Discover biomedical relationships between entities ✅
- 📄 Literature Search: Support literature retrieval by keywords and entity IDs ✅
- 🧠 Batch Processing: Support batch export of annotation information from search results ✅

## 🚀 Quick Start

### Requirements

- Python 3.10+
- MCP library

### Manual Installation

1. Clone the repository:
   ```
   git clone https://github.com/JackKuo666/PubTator-MCP-Server.git
   cd PubTator-MCP-Server
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

(Mac OS)

```json
{
  "mcpServers": {
    "pubtator": {
      "command": "python",
      "args": ["-m", "pubtator-mcp-server"]
      }
  }
}
```

(Windows)

```json
{
  "mcpServers": {
    "pubtator": {
      "command": "C:\\Users\\YOUR\\PATH\\miniconda3\\envs\\mcp_server\\python.exe",
      "args": [
        "D:\\code\\YOUR\\PATH\\PubTator-MCP-Server\\pubtator_server.py"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### CLine Configuration
```json
{
  "mcpServers": {
    "pubtator": {
      "command": "bash",
      "args": [
        "-c",
        "source /home/YOUR/PATH/mcp-server-pubtator/.venv/bin/activate && python /home/YOUR/PATH/pubtator_server.py"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

To use TCP transport, modify the configuration as follows:

```json
{
  "mcpServers": {
    "pubtator": {
      "command": "bash",
      "args": [
        "-c",
        "source /home/YOUR/PATH/mcp-server-pubtator/.venv/bin/activate && python /home/YOUR/PATH/pubtator_server.py"
      ],
      "env": {
        "MCP_TRANSPORT": "tcp",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": "8888"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 🛠 API Features

PubTator MCP Server provides the following core features:

### 1. Export Publications (export_publications)

Export PubTator annotation results for specified PMID literature:
```python
result = await export_publications(
    ids=["32133824", "34170578"],
    id_type="pmid",
    format="biocjson",  # Supported: pubtator, biocxml, biocjson
    full_text=False     # Whether to include full text
)
```

### 2. Entity ID Lookup (find_entity_id)

Query standard identifiers for biological concepts through free text:
```python
result = await find_entity_id(
    query="COVID-19",
    concept="disease",  # Optional: gene, disease, chemical, species, mutation
    limit=5             # Optional: limit number of results
)
```

### 3. Relationship Query (find_related_entities)

Find other entities related to a specified entity:
```python
result = await find_related_entities(
    entity_id="@DISEASE_COVID_19",
    relation_type="treat",    # Optional: treat, cause, interact, etc.
    target_entity_type="chemical",  # Optional: gene, disease, chemical
    max_results=5       # Optional: limit number of results
)
```

### 4. Literature Search (search_pubtator)

Search the PubTator database:
```python
results = await search_pubtator(
    query="COVID-19",
    max_pages=1     # Optional: maximum number of pages to retrieve
)
```

### 5. Batch Export (batch_export_from_search)

Search and batch export literature annotations:
```python
results = await batch_export_from_search(
    query="COVID-19",
    format="biocjson",
    max_pages=1,
    full_text=False,
    batch_size=5
)
```

Note: The actual function calls may vary depending on your implementation. These examples are based on our recent tests and may need to be adjusted to match your exact API.

## ⚠️ Usage Limitations

- API request rate limit: maximum 3 requests per second
- When batch exporting, use a reasonable batch_size to avoid request timeout
- For relationship queries, entity IDs must start with "@", e.g., "@DISEASE_COVID-19"

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for research purposes only. Please comply with PubTator's terms of service and use this tool responsibly.
