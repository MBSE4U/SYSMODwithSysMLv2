#    This module provides generic utility functions for interacting with a SysMLv2-compatible REST API.
#    It includes helpers for querying projects, commits, metadata, elements, and relationships.
#
#    Copyright 2025 Tim Weilkiens
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import json
import uuid
import requests
from functools import lru_cache
from typing import List, Dict, Optional, Any, Union

# Global session object
session = requests.Session()

# Global Element Cache
# Key: query_url (matches the context of a commit)
# Value: Dict[element_id, element_data]
ELEMENT_CACHE = {}

def get_projects(server_url: str, page_size: int = 256) -> List[Dict[str, Any]]:
    """
    Fetches the list of projects from the server.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        page_size (int, optional): Number of projects to fetch per page. Defaults to 256.

    Returns:
        List[Dict[str, Any]]: A list of project dictionaries, sorted alphabetically by name.

    Raises:
        ValueError: If the server returns a non-200 status code.
    """
    projects_url = f"{server_url}/projects?page%5Bsize%5D={page_size}"
    print(f"Fetching projects from {projects_url}")
    response = session.get(projects_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to retrieve projects from {projects_url}. Status code: {response.status_code}, details: {response.text}")
    projects = response.json()
    sorted_projects = sorted(
        projects,
        key=lambda p: (p["name"] or "").lower()
    )
    return sorted_projects

def get_commits(server_url: str, project_id: str) -> List[Dict[str, Any]]:
    """
    Fetches the list of commits for a given project.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.

    Returns:
        List[Dict[str, Any]]: A list of commit dictionaries, sorted by creation date.

    Raises:
        ValueError: If arguments are missing or the server returns an error.
    """
    if not server_url or not project_id:
        raise ValueError("Both server_url and project_id are required.")

    commits_url = f"{server_url}/projects/{project_id}/commits"
    response = session.get(commits_url)

    if response.status_code != 200:
        raise ValueError(f"Failed to retrieve commits. Status code: {response.status_code}, details: {response.text}")

    commits = response.json()
    if not isinstance(commits, list):
        raise ValueError("Expected a list of commits in the response.")
    # Sort by 'createdAt' if present, otherwise by 'id'
    sorted_commits = sorted(commits, key=lambda x: x.get('createdAt', x.get('id', '')))
    return sorted_commits

def load_model_cache(server_url: str, project_id: str, commit_id: str, page_size: int = 256) -> int:
    """
    Fetches all elements for a given project and commit and stores them in the global `ELEMENT_CACHE`.

    This function attempts to load the entire model into memory to optimize subsequent lookups.
    The cache is keyed by the commit-specific URL.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        page_size (int, optional): Number of elements to fetch per page. Defaults to 256.

    Returns:
        int: The number of elements loaded into the cache.

    Raises:
        ValueError: If the server returns an error or unexpected response format.
    """
    commit_url = f"{server_url}/projects/{project_id}/commits/{commit_id}"
    elements_url = f"{commit_url}/elements?page%5Bsize%5D={page_size}"
    
    print(f"Loading cache from {elements_url}")
    response = session.get(elements_url)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to load elements for cache. Status code: {response.status_code}, details: {response.text}")
    
    elements = response.json()
    print(f"Loaded {len(elements)} elements for cache.")

    if not isinstance(elements, list):
         raise ValueError(f"Expected list of elements, got {type(elements)}")
         
    # Populate Cache
    cache_entry = {}
    for el in elements:
        if '@id' in el:
            cache_entry[el['@id']] = el
            
    ELEMENT_CACHE[commit_url] = cache_entry
    print(f"Cache loaded for {commit_url} with {len(cache_entry)} elements.")
    return len(cache_entry)

def get_metadata_ids_by_name(server_url: str, project_id: str, commit_id: str, metadata_shortnames: List[str]) -> Dict[str, str]:
    """
    Fetches the IDs of MetadataDefinition elements based on provided short names.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        metadata_shortnames (List[str]): List of short names to search for.

    Returns:
        Dict[str, str]: A mapping of short name to MetadataDefinition ID.
    """
    metadata_definitions = get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'MetadataDefinition')
    if isinstance(metadata_definitions, list):
        id_map = {}
        for shortName in metadata_shortnames:
            matched_id = None
            for item in metadata_definitions:
                print(f"Comparing item shortName: {item.get('declaredShortName')} with shortName: {shortName}")
                if item.get('declaredShortName') == shortName:
                    print(f"Found match for shortName: {shortName} with ID: {item['@id']}")
                    matched_id = item['@id']
                    id_map[shortName] = matched_id
                    break
        return id_map
    else:
        return {"error": "Unexpected response", "details": metadata_definitions}

def get_metadatausage_annotatedElement_ids(server_url: str, project_id: str, commit_id: str, metadefinition_dict: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Retrieve IDs of elements annotated with specific metadata.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        metadefinition_dict (Dict[str, str]): A mapping of metadata key (logical name) to MetadataDefinition ID.

    Returns:
        Dict[str, List[str]]: A mapping from metadata key to a list of annotated element IDs.
    """
    
    metadata_usages = get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'MetadataUsage')
    print(f"Found {len(metadata_usages)} MetadataUsages")
    results = {metadata_name: [] for metadata_name in metadefinition_dict.keys()}
    print(f"Found {len(results)} results")
    for item in metadata_usages:
        metadata = item.get('metadataDefinition')
        print(f"Found metadata: {metadata}")
        metadata_id = metadata.get('@id') if isinstance(metadata, dict) else 'Unknown'
        print(f"Found metadata_id: {metadata_id}")
        for key, metadefinition_id in metadefinition_dict.items():
            if metadata_id == metadefinition_id:
                annotated_elements = item.get("annotatedElement", [])   
                print(f"Found annotated_elements: {annotated_elements}")    
                if annotated_elements:
                    if isinstance(annotated_elements, list):
                        for annotated in annotated_elements:
                            annotated_id = annotated.get("@id")
                            print(f"Found annotated_id: {annotated_id}")
                            if annotated_id:
                                results[key].append(annotated_id)
                    elif isinstance(annotated_elements, dict):
                        annotated_id = annotated_elements.get("@id")
                        if annotated_id:
                            results[key].append(annotated_id)
                else:
                    results[key].append(item.get("@id"))
    print(f"get_metadatausage_annotatedElement_ids returns: {results}")
    return results

def get_owned_usages(server_url, project_id, commit_id, owner, feature_name):
    """
    Fetches owned usages for the owner from both Usage and Definition and adds them to the owner object.
    """

    query_url = get_commit_url(server_url, project_id, commit_id)

    print(f"get_owned_usages called with owner: {owner.get('name')}, feature_name: {feature_name}")
    if not owner:
        return

    feature_ids = [p['@id'] for p in owner.get(feature_name, [])]
    owned_usages = get_elements_fromAPI(query_url, feature_ids)
    print(f"  Found {len(owned_usages)} {feature_name} in owner")
    
    # Also fetch all inherited features
    def_ref = owner.get('definition')
    if def_ref and len(def_ref) > 0:
            def_id = def_ref[0]['@id']
            definition = get_element_fromAPI(query_url, def_id)
            print(f"  Fetching owned usages from Definition: {definition.get('name')} ({definition.get('@id')})")
            def_usages_ids = [p['@id'] for p in definition.get(feature_name, [])]
            def_usages = get_elements_fromAPI(query_url, def_usages_ids)  
            print(f"  Found {len(def_usages)} {feature_name} in Definition")
            owned_usages.extend(def_usages)
            
    return owned_usages

def get_elements_byKind_fromAPI(server_url: str, project_id: str, commit_id: str, kind: str) -> List[Dict[str, Any]]:
    """
    Fetches elements of a specific kind (e.g., 'Class', 'PartUsage').

    Results are cached via LRU cache.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        kind (str): The SysML v2 element kind.

    Returns:
        List[Dict[str, Any]]: List of matching element dictionaries.
    """
    query_url = f"{server_url}/projects/{project_id}/query-results?commitId={commit_id}"

    query_input = {
        '@type': 'Query',
        'where': {
            '@type': 'PrimitiveConstraint',
            'inverse': False,
            'operator': '=',
            'property': '@type',
            'value': [f"{kind}"]
        }
    }
    try:
        query_response = session.post(query_url, json=query_input)
        if query_response.status_code == 200:
            query_response_json = query_response.json()
            return query_response_json
        else:
            raise ValueError(f"Failed to query kinds. Status code: {query_response.status_code}, details: {query_response.text}")
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_elements_byDeclaredName_fromAPI(server_url: str, project_id: str, commit_id: str, name: str) -> List[Dict[str, Any]]:
    """
    Fetches elements by their `declaredName`.

    Also handles 'Redefinition' relationships to find elements that redefine a named element.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        name (str): The declared name to search for.

    Returns:
        List[Dict[str, Any]]: List of matching element dictionaries.
    """
    query_input = {
        '@type': 'Query',
        'where': {
            '@type': 'PrimitiveConstraint',
            'inverse': False,
            'operator': '=',
            'property': 'declaredName',
            'value': [f"{name}"]
        }
    }

    try:
        query_url = f"{server_url}/projects/{project_id}/query-results?commitId={commit_id}"
        query_response = session.post(query_url, json=query_input)
        if query_response.status_code == 200:
            query_response_json = query_response.json()
            additional_elements = []
            for element in query_response_json:
                # print(f"Found element: {element.get('declaredName', 'Unknown')} (ID: {element.get('@id', 'Unknown')})")
                elementsOfSameType = get_elements_byKind_fromAPI(server_url, project_id, commit_id, element.get('@type', ''))
                for el in elementsOfSameType:
                    # print(f"Processing element of type {el.get('@type', 'Unknown')}: {el.get('declaredName', 'Unknown')} (ID: {el.get('@id', 'Unknown')})")
                    if el.get('@id') != element.get('@id'):
                        for relationshipID in el.get('ownedRelationship', []):
                            relationship = get_element_fromAPI(server_url, project_id, commit_id, relationshipID['@id'])
                            # print(f"Found relationship: {relationship.get('@type', 'Unknown')} (ID: {relationship.get('@id', 'Unknown')})")
                            if relationship.get('@type') == "Redefinition":
                                # print(f"Found redefinition relationship: {relationshipID}")
                                redefinedFeatureID = relationship.get('redefinedFeature').get('@id')
                                # print(f"redefinedFeatureID: {redefinedFeatureID}")
                                redefinedElement = get_element_fromAPI(server_url, project_id, commit_id, redefinedFeatureID)
                                # print(f"Redefined element declaredName: {redefinedElement.get('declaredName', 'Unknown')}")

                                # 👉 Check if the redefined element has the declaredName "value"
                                if redefinedElement.get('declaredName') == name:
                                    # print("Adding element to query_response_json because redefined elements declaredName is 'value'")
                                    additional_elements.append(el)

            query_response_json.append(additional_elements)
            return query_response_json
        else:
            raise ValueError(f"Failed to query names. Status code: {query_response.status_code}, details: {query_response.text}")
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_elements_byProperty_fromAPI(server_url: str, project_id: str, commit_id: str, property: str,value: str) -> List[Dict[str, Any]]:
    """
    Fetches elements by their `property`.

    Also handles 'Redefinition' relationships to find elements that redefine a named element.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        property (str): The property to search for.
        value (str): The value to search for.

    Returns:
        List[Dict[str, Any]]: List of matching element dictionaries.
    """
    query_input = {
        '@type': 'Query',
        'where': {
            '@type': 'PrimitiveConstraint',
            'inverse': False,
            'operator': '=',
            'property': property,
            'value': [f"{value}"]
        }
    }
    print(f"Query input: {query_input}")    
    try:
        query_url = f"{server_url}/projects/{project_id}/query-results?commitId={commit_id}"
        query_response = session.post(query_url, json=query_input)
        if query_response.status_code == 200:
            query_response_json = query_response.json()
            additional_elements = []
            for element in query_response_json:
                # print(f"Found element: {element.get(property, 'Unknown')} (ID: {element.get('@id', 'Unknown')})")
                elementsOfSameType = get_elements_byKind_fromAPI(server_url, project_id, commit_id, element.get('@type', ''))
                for el in elementsOfSameType:
                    # print(f"Processing element of type {el.get('@type', 'Unknown')}: {el.get(property, 'Unknown')} (ID: {el.get('@id', 'Unknown')})")
                    if el.get('@id') != element.get('@id'):
                        for relationshipID in el.get('ownedRelationship', []):
                            relationship = get_element_fromAPI(get_commit_url(server_url, project_id, commit_id), relationshipID['@id'])
                            # print(f"Found relationship: {relationship.get('@type', 'Unknown')} (ID: {relationship.get('@id', 'Unknown')})")
                            if relationship.get('@type') == "Redefinition":
                                # print(f"Found redefinition relationship: {relationshipID}")
                                redefinedFeatureID = relationship.get('redefinedFeature').get('@id')
                                # print(f"redefinedFeatureID: {redefinedFeatureID}")
                                redefinedElement = get_element_fromAPI(get_commit_url(server_url, project_id, commit_id), redefinedFeatureID)
                                # print(f"Redefined element declaredName: {redefinedElement.get(property  , 'Unknown')}")

                                # 👉 Check if the redefined element has the declaredName "value"
                                if redefinedElement.get(property) == value:
                                    # print("Adding element to query_response_json because redefined elements declaredName is 'value'")
                                    additional_elements.append(el)

            query_response_json.append(additional_elements)
            return query_response_json
        else:
            raise ValueError(f"Failed to query elements. Status code: {query_response.status_code}, details: {query_response.text}")
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_elements_fromAPI(query_url: str, element_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Batch fetches multiple elements by ID.

    Args:
        query_url (str): The base URL inclusive of project and commit (e.g. `.../commits/{id}`).
        element_ids (List[str]): List of element IDs to fetch.

    Returns:
        List[Dict[str, Any]]: List of element dictionaries.
    """
    elements = []
    for element_id in element_ids:
        try:
            element_json = get_element_fromAPI(query_url, element_id)
            if isinstance(element_json, list):
                elements.extend(element_json)
            else:
                elements.append(element_json)
        except Exception as e:
            print(f"Error processing element id {element_id}: {e}")
            continue  # Continue with the next ID
    return elements

@lru_cache(maxsize=2048)
def get_element_fromAPI(query_url: str, element_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single element by ID, checking the local cache first.

    Args:
        query_url (str): The base URL inclusive of project and commit (e.g. `.../commits/{id}`).
        element_id (str): The ID of the element.

    Returns:
        Optional[Dict[str, Any]]: The element dictionary, or None if failed.

    Raises:
        Exception: If the network request fails significantly.
    """
    print(f"get_element_fromAPI called: {query_url}/elements/{element_id}")  

    try:
        # Check Cache First
        if query_url in ELEMENT_CACHE:
            cached_element = ELEMENT_CACHE[query_url].get(element_id)
            if cached_element:
                # print(f"Cache HIT (cache size: {len(ELEMENT_CACHE[query_url])} ): {element_id}") 
                return cached_element
            else:
                 # Local cache exists but this specific element is missing
                 # print(f"Cache MISS (cache size: {len(ELEMENT_CACHE[query_url])}): {element_id}") 
                 pass
        else:
            # print(f"Cache MISS for context: {query_url}")
            # print(f"Available Cache Contexts: {list(ELEMENT_CACHE.keys())}")
            pass
        
        url = query_url + "/elements/" + element_id
        # print(f"API Query: {url}")
        elements_response = session.get(url)
        if elements_response.status_code == 200:
            element = elements_response.json()
            if isinstance(element, list):
                # print(f"⚠️ API returned list for element {element_id}, using first item")
                element = element[0] if element else None
            
            if element:
                if query_url not in ELEMENT_CACHE:
                    ELEMENT_CACHE[query_url] = {}
                ELEMENT_CACHE[query_url][element_id] = element
                # print(f"Cache SET (cache size: {len(ELEMENT_CACHE[query_url])} ): {element_id}")   
            return element
        
    except Exception as e:
        print(f"Error processing element id {element_id}: {e}")
        raise e

def get_contained_elements(server_url: str, project_id: str, commit_id: str, element_id: str, kind: str, elementKind: str = 'ownedElement') -> List[Dict[str, Any]]:
    """
    Returns a list of contained elements of a specific kind.

    Args:
        server_url (str): The base URL of the SysML v2 API server.
        project_id (str): The UUID of the project.
        commit_id (str): The UUID of the commit.
        element_id (str): The ID of the container element.
        kind (str): The SysML v2 type to filter for (e.g. 'Class', 'MetadataUsage').
        elementKind (str, optional): The property to search within (e.g. 'ownedElement', 'ownedFeature'). Defaults to 'ownedElement'.

    Returns:
        List[Dict[str, Any]]: List of matching child elements.
    """
    query_url = f"{server_url}/projects/{project_id}/commits/{commit_id}"
    element_data = get_element_fromAPI(query_url, element_id)
    
    if not element_data:
        print(f"Unable to fetch element with id '{element_id}' in commit '{commit_id}' of project '{project_id}'")
        return []

    owned_elements = element_data.get(elementKind, [])
    print(f"get_contained_elements: {len(owned_elements)} raw elements found in '{elementKind}'")
    matching_elements = []

    for owned_element in owned_elements:
        full_element = get_element_fromAPI(query_url, owned_element['@id'])
        if full_element and full_element.get('@type') == kind:
            matching_elements.append(full_element)

    print(f"get_contained_elements: {len(matching_elements)} matching elements found in '{elementKind}'")
    return matching_elements

def getValueFromOperatorExpressionUnit(query_url: str, opExp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Helper to extract value from an OperatorExpression.
    
    Args:
        query_url (str): Context URL.
        opExp (Dict[str, Any]): The operator expression element.

    Returns:
        Optional[Dict[str, Any]]: The value element.
    """
    # print(f"getValueFromOperatorExpressionUnit called") # with opExp: {opExp}")
    for relationship_id in opExp.get("ownedRelationship"):
        relationship = get_element_fromAPI(query_url, relationship_id["@id"])
        if relationship.get("@type") == 'ParameterMembership' and relationship.get("memberName") == "x":
            memberElement = get_element_fromAPI(query_url, relationship["memberElement"]["@id"])
            featureValue = get_element_fromAPI(query_url, memberElement["ownedRelationship"][0]["@id"])
            return get_element_fromAPI(query_url, featureValue["memberElement"]["@id"])
    return None

def find_element_by_id(aggregated_results: List[Dict[str, Any]], target_id: str) -> Optional[Dict[str, Any]]:
    """
    Searches a list of elements for a specific ID.
    
    Args:
        aggregated_results (List[Dict]): List of elements.
        target_id (str): ID to find.
        
    Returns:
        Optional[Dict]: Found element or None.
    """
    for element in aggregated_results:
        if element['@id'] == target_id:
            return element
    return None  # Return None if not found

def get_commit_url(server_url: str, project_id: str, commit_id: str) -> str:
    """Helper to construct the commit URL."""
    return f"{server_url}/projects/{project_id}/commits/{commit_id}"

def check_specialization_hierarchy(query_url: str, element: Dict[str, Any], super_element: Dict[str, Any], visited: set = None) -> bool:
    """
    Recursively checks if an element specializes (is a subclass of) an element with a specific name.

    Args:
        query_url (str): Context URL.
        element (Dict[str, Any]): The child element to check.
        super_element (Dict[str, Any]): The superclass/interface to look for.
        visited (set, optional): Set of visited IDs to prevent loops.

    Returns:
        bool: True if it specializes the target, False otherwise.
    """
    if visited is None: visited = set()
    
    el_id = element.get('@id')
    if el_id in visited: return False
    visited.add(el_id)
    
    print(f"Hierarchy Check: {element.get('name')} ({element.get('@type')}, {element.get('@id')}) :> {super_element.get('name')} ({super_element.get('@type')}, {super_element.get('@id')})")

    if element.get('@id') == super_element.get('@id'):
        print(f"Found {super_element.get('name')}")
        return True

    # Check ownedSpecialization
    print(f"Checking ownedSpecialization for {element.get('name')}: {element.get('ownedSpecialization')}")
    for rel_ref in element.get('ownedSpecialization', []):
        rel = get_element_fromAPI(query_url, rel_ref['@id'])
        if rel:
             general = rel.get('general')
             if general:
                 general_el = get_element_fromAPI(query_url, general['@id'])
                 if general_el and check_specialization_hierarchy(query_url, general_el, super_element, visited):
                     return True
    return False

def find_elements_specializing(server_url: str, project_id: str, commit_id: str, elements: List[Dict[str, Any]], super_element_name: str, element_kind: str = None) -> List[Dict[str, Any]]:
    """
    Filters a list of elements to find those that specialize a specific element.

    Args:
        query_url (str): Context URL.
        elements (List[Dict]): List of candidate elements.
        super_element_name (str): Name of the supertype.
        element_kind (str, optional): Filter by SysML element kind first.

    Returns:
        List[Dict]: List of matching elements.
    """
    print(f"find_elements_specializing called with {len(elements)} elements, {super_element_name}, {element_kind}")
    super_element = None    
    super_elements = get_elements_byProperty_fromAPI(server_url, project_id, commit_id, 'qualifiedName', super_element_name)
    if super_elements:
        super_element = super_elements[0]
    else:
        return []   
    print(f"Found super element: {super_element.get('name')} ({super_element.get('@id')})")  
    found_elements = []
    for el in elements:
        if element_kind and el.get('@type') != element_kind:
            continue
        if check_specialization_hierarchy(get_commit_url(server_url, project_id, commit_id), el, super_element):
            print(f"Check {el.get('@id')} != {super_element.get('@id')}")
            if el.get('@id') != super_element.get('@id'):
                found_elements.append(el)
    return found_elements

def get_recursive_owned_elements(server_url: str, project_id: str, commit_id: str, start_element_id: str, kind: str, max_depth: int = 5, current_depth: int = 0) -> List[Dict[str, Any]]:
    """
    Recursively fetches owned elements of a specific kind down to a maximum depth.

    Args:
        server_url (str): API Base URL.
        project_id (str): Project ID.
        commit_id (str): Commit ID.
        start_element_id (str): Root element ID.
        kind (str): Target element kind.
        max_depth (int, optional): Maximum recursion level. Defaults to 5.
        current_depth (int, optional): Current recursion level.

    Returns:
        List[Dict]: List of found elements.
    """
    if current_depth > max_depth:
        return []
    
    elements = get_contained_elements(server_url, project_id, commit_id, start_element_id, kind)
    all_elements = elements[:]
    
    if current_depth < max_depth:
        # Generic recursion logic
        # For now, let's just look at children of 'ownedElement'.
        raw_children = get_contained_elements(server_url, project_id, commit_id, start_element_id, 'Element') # Generic
        for child in raw_children:
            if child.get('@type') in ['Package', 'PartUsage', 'ItemUsage']:
                all_elements.extend(get_recursive_owned_elements(server_url, project_id, commit_id, child['@id'], kind, max_depth, current_depth + 1))
                
    return all_elements

def get_element_definition(server_url: str, project_id: str, commit_id: str, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Retrieves the definition element for a given usage element.

    Args:
        server_url (str): API Base URL.
        project_id (str): Project ID.
        commit_id (str): Commit ID.
        element (Dict): The usage element.

    Returns:
        Optional[Dict]: The definition element, or None.
    """
    definition_refs = element.get('definition')
    if definition_refs:
        definition = get_element_fromAPI(get_commit_url(server_url, project_id, commit_id), definition_refs[0]['@id'])
        if definition:
            return definition
    return None

def get_element_documentation(server_url: str, project_id: str, commit_id: str, element_id: str) -> Optional[str]:
    """
    Retrieves the documentation for a given element.

    Args:
        server_url (str): API Base URL.
        project_id (str): Project ID.
        commit_id (str): Commit ID.
        element_id (str): Element ID.

    Returns:
        Optional[str]: The documentation text, or None if not found.
    """
    print(f"get_element_documentation called with element_id: {element_id}")
    element = get_element_fromAPI(get_commit_url(server_url, project_id, commit_id), element_id)
    if element:
        element_doc_refs = element.get('documentation') 
        if element_doc_refs:
            bodies = []
            for ref in element_doc_refs:
                doc = get_element_fromAPI(get_commit_url(server_url, project_id, commit_id), ref['@id'])
                if doc and doc.get('body'):
                    bodies.append(doc.get('body'))
            return bodies
    return []

def get_feature_value(server_url: str, project_id: str, commit_id: str, owner: Dict[str, Any], feature_name: str, feature_kind: str = 'AttributeUsage') -> Union[str, int, float, None]:
    """
    Extracts the value of a specific feature (attribute) from an element.

    Args:
        server_url (str): API Base URL.
        project_id (str): Project ID.
        commit_id (str): Commit ID.
        owner (Dict): The element containing the feature.
        feature_name (str): The name of the feature to retrieve.
        feature_kind (str, optional): The kind of feature to look for. Defaults to 'AttributeUsage'.

    Returns:
        Union[str, int, float, None]: The value of the feature, or "Unknown"/None if not found.
    """
    print(f"get_feature_value called with owner: {owner.get('@id')} and feature_name: {feature_name} and feature_kind: {feature_kind}")

    query_url = get_commit_url(server_url, project_id, commit_id)

    feature = get_feature(server_url, project_id, commit_id, owner, feature_name, feature_kind)
    if not feature:
        return None

    return get_attribute_value_from_usage(query_url, feature)

def get_feature(server_url: str, project_id: str, commit_id: str, owner: Dict[str, Any], feature_name: str, feature_kind: str = 'AttributeUsage') -> Union[str, int, float, None]:
    print(f"get_feature called with owner: {owner.get('@id')} and feature_name: {feature_name} and feature_kind: {feature_kind}")

    query_url = get_commit_url(server_url, project_id, commit_id)

    feature_kind_mapping = {
        'AttributeUsage': 'ownedFeature',
        'PartUsage': 'ownedPart',
        'ItemUsage': 'ownedItem',   
        'PortUsage': 'ownedPort',
        'ReferenceUsage': 'ownedReference',
    }

    feature_ids = [p['@id'] for p in owner.get(feature_kind_mapping.get(feature_kind), [])]
    print(f"  Found {len(feature_ids)} {feature_kind_mapping.get(feature_kind)} in owner")    
    owned_usages = get_elements_fromAPI(query_url, feature_ids)
    for usage in owned_usages:
        if feature_kind == usage.get('@type'):  
            if usage.get('name') == feature_name:
                print(f"  Found {feature_name} in owner")
                return usage
    
    # Also fetch all inherited features
    inherited_features_ids = owner.get('inheritedFeature')
    print(f"  Found {len(inherited_features_ids)} inherited features")
    for inherited_feature_id in inherited_features_ids:
        inherited_feature = get_element_fromAPI(query_url, inherited_feature_id.get('@id'))
        if feature_kind == inherited_feature.get('@type'):
            print(f"  Found {feature_kind}: Compare {feature_name} with {inherited_feature.get('name')}")
            if inherited_feature.get('name') == feature_name:
                print(f"  Found {feature_name} in inherited features")
                return inherited_feature
    
    print(f"  NOT found {feature_name} in owner")
    return None


def get_attribute_value_from_usage(query_url: str, attr_usage: Dict[str, Any]) -> Union[str, int, float, None]:
    """
    Helper to extract value from an AttributeUsage element.

    Args:
        query_url (str): Context URL.
        attr_usage (Dict): The attribute usage element.

    Returns:
        Union[str, int, float, None]: The extracted value.
    """

    print(f"get_attribute_value_from_usage called with {attr_usage.get('@id')}")

    # Dig for the value expression
    print(f"#relationships: {len(attr_usage.get('ownedRelationship', []))}")
    for rel_ref in attr_usage.get('ownedRelationship', []):
        rel = get_element_fromAPI(query_url, rel_ref['@id'])
        print(f"Found relationship: {rel.get('@id')}: {rel.get('@type')}")
        if rel and rel.get('@type') == 'FeatureValue':
            # The value is a 'memberElement' or 'value'
            # Check schema. FeatureValue has 'value' property which is an Expression.
            print(f"Found FeatureValue: val = {rel.get('value')}")
            value_id = rel.get('value')
            if value_id:
                print(f"Found value_id: {value_id.get('@id')}")
                value = get_element_fromAPI(query_url, value_id.get('@id'))
                if value.get('@type') == 'FeatureChainExpression':                         
                    value = get_element_fromAPI(query_url, value.get('targetFeature').get('@id'))   
                if value:
                    print(f"Found value: {value.get('@id')}, type {value.get('@type')}")   
                    # Check if LiteralInteger, LiteralString, etc.
                    if 'value' in value: 
                        print(f"Return value: {value['value']}")
                        return value['value']
                    # Enum value reference?
                    if value.get('@type') == 'FeatureReferenceExpression':
                        # Reference to an Enum literal?
                         enumeration = get_element_fromAPI(query_url, value.get('referent').get('@id'))
                         if enumeration:
                            print(f"Found Enumeration via FeatureReferenceExpression: {enumeration.get('declaredName')}")
                            return enumeration.get('declaredName')
                    if value.get('@type') == 'EnumerationUsage':
                        print(f"Found EnumerationUsage: {value.get('name')}")
                        return value.get('name')

    print(f"NOT found value")    
    return None

def update_model_element(server_url, project_id, commit_id, element_id, feature_name, feature_value):
    """
    Updates a model element with a new feature value.
    """
    
    commit_body = {
    "@type": "Commit",
    "change": [
        {
        "@type": "DataVersion",
        "payload": {
            "@type": "Documentation",
            feature_name: feature_value,
            "identifier":element_id
        },
        "identity": {
            "@id": element_id
        }
        }
    ],
    "previousCommit": {
        "@id": commit_id
        }
    }
    print(f"commit_body: {commit_body}")
    
    commit_post_url = f"{server_url}/projects/{project_id}/commits" 

    commit_post_response = requests.post(commit_post_url, 
                                      headers={"Content-Type": "application/json"}, 
                                      data=json.dumps(commit_body))

    new_commit_id = ""

    if commit_post_response.status_code == 200:
        commit_response_json = commit_post_response.json()
        print(commit_response_json)
        new_commit_id = commit_response_json['@id']
    else:
        print(f"Problem in updating model element in project {project_id}")
        print(commit_post_response)

    return new_commit_id 