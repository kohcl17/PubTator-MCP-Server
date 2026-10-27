import requests
import json
import time
from typing import List, Dict, Optional, Union, Generator, Any
import xml.etree.ElementTree as ET
from pubtator_global_variables import *

class PubTator3API:
    BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
    ANNOTATE_URL = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful"
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.request_delay = 0.34  # Comply with the 3 requests/second limit
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_request_time = 0
    
    def _rate_limited_request(self, method, *args, **kwargs):
        """Request method with rate limiting and retry mechanism"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        
        kwargs['timeout'] = self.timeout
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, *args, **kwargs)
                self._last_request_time = time.time()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(min(2 ** attempt, 10))  # Exponential backoff strategy
    
    # ------------------------- Core Functionality -------------------------
    def export_publications(
        self,
        ids: List[str],
        id_type: str = "pmid",
        format: str = "biocjson",
        full_text: bool = False,
        extract_text: bool = False
    ) -> Union[Dict, str]:
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
        if not ids:
            raise ValueError("IDs list cannot be empty")
        
        if id_type not in PUB_ID_FORMATS:
            raise ValueError("id_type must be 'pmid' or 'pmcid'")
        if format not in AVAILABLE_FORMATS:
            raise ValueError("format must be one of: pubtator, biocxml, biocjson")
        
        try:
            if id_type == "pmcid":
                url = f"{self.BASE_URL}/publications/pmc_export/{format}"
            else:
                url = f"{self.BASE_URL}/publications/export/{format}"
            
            params = {f"{id_type}s": ",".join(ids)}
            if full_text and format != "pubtator":
                params["full"] = "true"
            
            response = self._rate_limited_request("GET", url, params=params)
            response.raise_for_status()
            
            if format == "biocjson":
                result = response.json()
                if isinstance(result, list):
                    result = {"PubTator3": result}  # standardize to the key extract_publication_text expects
            else:
                result = response.text

            if extract_text:
                return self.extract_publication_text(result, format=format)
            return result
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to export publications: {str(e)}")
    
    def find_entity_id(
        self,
        query: str,
        concept: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        locates the valid entity ids
        ---
        arguments
        ---
            query: str | free text input
            concept: str or None | one of gene, chemical, drugs, disease, variant, species, cell_line
            limit: int or None | number of IDs to return
        ---
        returns
        ---
            JSON of entity IDs
        """
        url = f"{self.BASE_URL}/entity/autocomplete/"
        params = {"query": query}
        
        if concept:
            if concept not in ENTITIES:
                raise ValueError("Invalid concept type")
            params["concept"] = concept
        if limit:
            params["limit"] = limit
        
        response = self._rate_limited_request("GET", url, params=params)
        response.raise_for_status()
        return response.json()
    
    def find_related_entities(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        target_entity_type: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> Dict:
        """
       finds related entities
        ---
        arguments
        ---
            entity_id: str | from find_entity_id
            relation_type: str or None | one of associate, cause, compare, cotreat, drug_interact, inhibit, interact, negative_correlate, positive_correlate, prevent, stimulate, treat
            target_entity_type: str or None | one of gene, chemical, disease, variant
            max_results: int or None | maximum number of results to return
        ---
        returns
        ---
            related entities in JSON
        """
        url = f"{self.BASE_URL}/relations"
        # Ensures entity_id has @ so it's valid
        if not entity_id.startswith("@"):
            raise ValueError("Invalid entity ID format, should start with '@', e.g., '@CHEMICAL_remdesivir' or '@DISEASE_Neoplasms'")
        params = {"e1": entity_id}
        
        if relation_type:
            if relation_type not in RELATION and relation_type != "ANY":
                raise ValueError("Invalid relation type")
            params["type"] = relation_type
        if target_entity_type:
            if target_entity_type not in ENTITY_TYPES:
                raise ValueError("Invalid target entity type")
            params["e2"] = target_entity_type
        if max_results:
            params["limit"] = max_results
        
        response = self._rate_limited_request("GET", url, params=params)
        response.raise_for_status()
        return response.json()
    
    
    
    # ------------------------- Enhanced Search Functionality -------------------------
    def search(
        self,
        query: str,
        page: int = 1,
        max_pages: Optional[int] = None
    ) -> Generator[Dict, None, None]:
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
        current_page = page
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while max_pages is None or current_page <= max_pages:
            try:
                url = f"{self.BASE_URL}/search/"
                params = {"text": query, "page": current_page}
                
                response = self._rate_limited_request("GET", url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("results"):
                    break
                    
                consecutive_errors = 0 
                yield data
                current_page += 1
                
            except requests.exceptions.RequestException as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    raise Exception(f"Search terminated after {max_consecutive_errors} consecutive request failures")
                time.sleep(min(2 ** consecutive_errors, 10))
                continue
            
            except json.JSONDecodeError:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    raise Exception(f"Search terminated after {max_consecutive_errors} consecutive response parsing failures")
                time.sleep(min(2 ** consecutive_errors, 10))
                continue
    
    def search_relations(
        self,
        entity1: str,
        relation_type: str = "ANY",
        entity2: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        specific entity relationship search
        ---
        arguments
        ---
            entity1: first entity ID (from find_entity_id)
            relation_type: str | one of ANY or associate, cause, compare, cotreat, drug_interact, inhibit, interact, negative_correlate, positive_correlate, prevent, stimulate, treat
            entity2: str or None | second entity type from gene, chemical, disease, or variant
            max_pages: int or None | maximum number of pages to return
        
        ---
        returns
        ---
            GeneratorDict of results
        """
        if entity2 is None:
            query = f"relations:{relation_type}|{entity1}"
        else:
            query = f"relations:{relation_type}|{entity1}|{entity2}"
            
        yield from self.search(query, max_pages=max_pages)
    
    def extract_pmids_from_results(self, results: Dict) -> List[str]:
        """
        Extract the PMIDs obtained from the results
        ---
        arguments
        ---
            results: dict | search results
        
        ---    
        returns
        ---
            list of PMIDs
        """
        return [str(result["pmid"]) for result in results.get("results", []) if "pmid" in result]
    
    def batch_export_from_search(
        self,
        query: str,
        format: str = "biocjson",
        max_pages: Optional[int] = 3,
        full_text: bool = False,
        extract_text: bool = False,
        batch_size: int = 100
    ) -> Generator[Union[Dict, str], None, None]:
        """Search for and batch-export literature, supports batch processing and error retries
        
        ---
        arguments
        ---
            query: str | search query
            format: str | one of pubtator, biocxml, biocjson, defauly biocjson
            max_pages: int | maximum number of pages to return
            full_text: bool | return full text
            extract_text: bool | return only the text from the publications
            batch_size: int | Number of PMIDs per batch
        ---    
        returns
        ---
            GeneratorDict of literature search results
        """
        try:
            all_pmids = []
            for page_result in self.search(query, max_pages=max_pages):
                page_pmids = self.extract_pmids_from_results(page_result)
                all_pmids.extend(page_pmids)
                
                # Process in batches to avoid excessively long URLs and high memory usage
                while len(all_pmids) >= batch_size:
                    batch = all_pmids[:batch_size]
                    try:
                        batch = [str(pmid) for pmid in batch]
                        result = self.export_publications(
                            batch,
                            "pmid",
                            format,
                            full_text,
                            extract_text
                        )
                        yield result
                        all_pmids = all_pmids[batch_size:]
                    except requests.exceptions.RequestException as e:
                        # Handles exception in batch processing
                        print(f"Batch export failed (batch size:{len(batch)}): {str(e)}")
                        # Retry with a smaller batch size
                        if batch_size > 10:
                            batch_size = batch_size // 2
                            continue
                        raise
            
            # handles remaining PMIDs
            if all_pmids:
                try:
                    all_pmids = [str(pmid) for pmid in all_pmids]
                    result = self.export_publications(
                        all_pmids,
                        "pmid",
                        format,
                        full_text,
                        extract_text
                    )
                    yield result
                except requests.exceptions.RequestException as e:
                    print(f"Handling remaining failed PMID retrievals (count:{len(all_pmids)}): {str(e)}")
                    raise
                    
        except Exception as e:
            raise Exception(f"An error occurred during the batch export process: {str(e)}")
        
    # Handle parsing of publications to summarise efficiently in local LLMs
    def extract_publication_text(
        self,
        publications: Union[Dict[str, Any], str],
        format: str = 'biocjson'
        ) -> Dict[str, str]:
        '''
        Handle parsing of publications to summarise efficiently in local LLMs
        ---
        arguments
        ---
        publications: Dict or str | results from export_publications
        format: str | result format from publications, one of pubtator, biocxml, biocjson (default: biocjson)
        
        ---
        returns
        ---
        JSON/Dict of text results
        '''
        json_parsed = {}
        if format == 'biocjson':
            results = publications['PubTator3']
            for i in results: # Each pmid
                pmid = i['id'] 
                text = [n['text'] for n in i['passages']]
                text_joined = "\n".join(text)
                json_parsed[pmid] = text_joined
        
        elif format == 'biocxml':
            root = ET.fromstring(publications)
            for document in root.findall('document'):
                pmid = document.findtext('id')
                texts = [passage.findtext('text') or "" for passage in document.findall('passage')]
                json_parsed[pmid] = "\n".join(texts)
                
        elif format == 'pubtator':
            current_pmid = None
            texts = []
            for line in publications.strip().split("\n"):
                if not line.strip():
                    if current_pmid is not None:
                        json_parsed[current_pmid] = "\n".join(texts)
                    current_pmid, texts = None, []
                    continue
                parts = line.split("|", 2)
                if len(parts) == 3 and parts[1] in ("t", "a"):
                    pmid, _, text = parts
                    if pmid != current_pmid:
                        if current_pmid is not None:
                            json_parsed[current_pmid] = "\n".join(texts)
                        current_pmid, texts = pmid, []
                    texts.append(text)
                # tab-separated annotation rows don't match pmid|t|.. or pmid|a|.. — skipped
            if current_pmid is not None:
                json_parsed[current_pmid] = "\n".join(texts)
        else:
            raise ValueError("format must be one of: biocjson, biocxml, pubtator")
        return json_parsed

# Test Program
if __name__ == "__main__":
    import argparse
    import logging
    from datetime import datetime
    
    # Logger configs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='PubTator3API Test Program')
    parser.add_argument('--test', choices=['all', 'export', 'entity', 'relation', 'annotate', 'search'],
                        default='all', help='Select test case to run')
    args = parser.parse_args()
    
    try:
        api = PubTator3API(max_retries=3, timeout=30)
        
        def test_export_publications():
            logger.info("Testing export publications functionality...")
            pmids = ["25359968", "25359969"]
            result = api.export_publications(pmids, format="biocjson", extract_text=True)
            logger.info(f"Successfully exported {len(pmids)} publications")
            return result
        
        def test_find_entity_id():
            logger.info("Testing find entity ID functionality...")
            query = "diabetes"
            result = api.find_entity_id(query, concept="disease", limit=5)
            logger.info(f"Successfully found entity: {query}")
            return result
        
        def test_find_related_entities():
            logger.info("Testing find related entities functionality...")
            entity_id = "@DISEASE_Diabetes_Mellitus"  # Use correct entity ID format
            result = api.find_related_entities(
                entity_id,
                relation_type="treat",
                target_entity_type="chemical"
            )
            logger.info(f"Successfully found entities related to {entity_id}")
            return result
        
        
        
        def test_search():
            logger.info("Testing search functionality...")
            query = "diabetes treatment"
            results = []
            for page_result in api.search(query, max_pages=2):
                results.append(page_result)
            logger.info(f"Successfully searched: {query}")
            return results
        
        # Tests to execute
        test_funcs = {
            'export': test_export_publications,
            'entity': test_find_entity_id,
            'relation': test_find_related_entities,
            'search': test_search
        }
        
        if args.test == 'all':
            for name, func in test_funcs.items():
                # Execute all test cases
                try:
                    logger.info(f"\nExecuting test: {name}")
                    result = func()
                    logger.info(f"Test successful: {name}\n")
                except Exception as e:
                    logger.error(f"Test failed {name}: {str(e)}\n")
        else:
            try:
                result = test_funcs[args.test]()
                logger.info(f"Test successful: {args.test}")
            except Exception as e:
                logger.error(f"Test failed {args.test}: {str(e)}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Network request error: {e}")
    except ValueError as e:
        logger.error(f"Parameter error: {e}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")
    finally:
        api.session.close()
