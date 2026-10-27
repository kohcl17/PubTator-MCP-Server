from typing import List, Dict, Optional, Any, Union
import asyncio
import logging
from mcp.server import MCPServer
from pubtator_search import PubTator3API

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
mcp = MCPServer("pubtator")

# Initialize PubTator3API client
client = PubTator3API(max_retries=3, timeout=30)


@mcp.tool()
async def search_pubtator(query: str, max_pages: Optional[int] = 3) -> List[Dict[str, Any]]:
    logging.info(f"Searching PubTator with query: {query}, max_pages: {max_pages}")
    """
    all encompassing search function
    
    ---
    arguments
    ---
        query: str | free text, entity IDs, relationships
        page: int | page number to return 
        max_pages: int or None | maximum number of pages to return
    
    ---
    returns
    ---
        GeneratorDict of results
    """
    try:
        results = await asyncio.to_thread(list, client.search(query, max_pages=max_pages))
        return results
    except Exception as e:
        logging.error(f"An error occurred while searching: {str(e)}")
        return [{"error": f"An error occurred while searching: {str(e)}"}]

@mcp.tool()
async def export_publications(ids: List[str], id_type: str = "pmid", format: str = "biocjson", full_text: bool = False, extract_text: bool = True) -> Union[Dict, str]:
    logging.info(f"Exporting publications: {ids}, id_type: {id_type}, format: {format}, full_text: {full_text}")
    """
    Export the annotation results for a set of documents
    ---
    arguments
    ---
        ids: list | PMIDs or PMCIDs
        id_type: str | one of pmid or pmcid
        format: str | one of pubtator, biocxml, or biocjson (default biocjson)
        full_text: bool | gets full text
        extract_text: bool | return only the text from the publications
    ---
    returns
    ---
        Annotation results (JSON dictionary or XML string)
    """
    try:
        result = await asyncio.to_thread(client.export_publications, ids, id_type, format, full_text, extract_text)
        return result
    except Exception as e:
        return {"error": f"An error occurred while exporting publications: {str(e)}"}

@mcp.tool()
async def find_entity_id(query: str, concept: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    logging.info(f"Finding entity ID for query: {query}, concept: {concept}, limit: {limit}")
    """
    Find entity ID using a free text query.

    Args:
        query: Query text
        concept: Optional, specify biological concept type
        limit: Optional, limit the number of returned results

    Returns:
        Dictionary containing entity IDs
    """
    try:
        result = await asyncio.to_thread(client.find_entity_id, query, concept, limit)
        return result
    except Exception as e:
        return [{"error": f"An error occurred while finding entity ID: {str(e)}"}]

@mcp.tool()
async def find_related_entities(entity_id: str, relation_type: Optional[str] = None, target_entity_type: Optional[str] = None, max_results: Optional[int] = None) -> List:
    logging.info(f"Finding related entities for: {entity_id}, relation_type: {relation_type}, target_entity_type: {target_entity_type}, max_results: {max_results}")
    """
    Find related entities.

    Args:
        entity_id: Entity ID
        relation_type: Optional, specify relation type
        target_entity_type: Optional, specify target entity type
        max_results: Optional, limit the number of returned results

    Returns:
        Dictionary containing related entities
    """
    try:
        result = await asyncio.to_thread(client.find_related_entities, entity_id, relation_type, target_entity_type, max_results)
        return result
    except Exception as e:
        return {"error": f"An error occurred while finding related entities: {str(e)}"}

@mcp.tool()
async def batch_export_from_search(query: str, format: str = "biocjson", max_pages: Optional[int] = 3, full_text: bool = False, batch_size: int = 100) -> List[Union[Dict, str]]:
    logging.info(f"Batch exporting from search: {query}, format: {format}, max_pages: {max_pages}, full_text: {full_text}, batch_size: {batch_size}")
    """
    Search and batch export publications.

    Args:
        query: Search query
        format: Export format
        max_pages: Maximum number of search pages
        full_text: Whether to export full text
        batch_size: Number of PMIDs to process in each batch

    Returns:
        List of dictionaries or strings containing exported publication data
    """
    try:
        results = await asyncio.to_thread(list, client.batch_export_from_search(query, format, max_pages, full_text, batch_size))
        return results
    except Exception as e:
        logging.error(f"An error occurred during batch export: {str(e)}")
        return [{"error": f"An error occurred during batch export: {str(e)}"}]

# To integrate into export_publications?
# @mcp.tool()
# async def extract_publication_text(publications: Dict) -> Dict[str, str]:
#     logging.info(f"Parsing text from publications...")
#     '''
#     Handle parsing of publications to summarise efficiently in local LLMs
#     ---
#     arguments
#     ---
#     publications: Dict | results from export_publications
    
#     ---
#     returns
#     ---
#     JSON/Dict of text results
#     '''
#     try:
#         result = await asyncio.to_thread(client.extract_publication_text, publications=publications)
#         return result
#     except Exception as e:
#         return {"error": f"An error occurred while extracting text from publications: {str(e)}"}

if __name__ == "__main__":
    logging.info("Starting PubTator MCP server")
    # Initialize and run the server
    mcp.run(transport='stdio')
