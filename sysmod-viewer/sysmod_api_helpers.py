#    This module provides specific SYSMOD utility functions.
#    It inherits generic SysMLv2 helpers from mbse4u_sysmlv2_api_helpers.
#
#    Copyright 2025 Tim Weilkiens, Paul Herbst, Dimitri Petrik
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

import sys
import os

import mbse4u_sysmlv2_api_helpers as mbse4u_sysmlv2

def get_sysmod_projects(server_url, project_id, commit_id):
    """
    Retrieves list of projects annotated with @project metadata.
    """

    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    metadata_definition_ids = mbse4u_sysmlv2.get_metadata_ids_by_name(server_url, project_id, commit_id, ['project'])
    print(f"Found {len(metadata_definition_ids)} metadata definition IDs.")
    project_ids = []
    if metadata_definition_ids:
        metadata_usages = mbse4u_sysmlv2.get_metadatausage_annotatedElement_ids(server_url, project_id, commit_id, metadata_definition_ids)
        print(f"Found {len(metadata_usages)} metadata usages.")
        project_ids = metadata_usages.get('project', [])
        print(f"Found {len(project_ids)} project IDs")
    if not project_ids:
        occurrence_definitions = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'OccurrenceDefinition')
        print(f"Found {len(occurrence_definitions)} OccurrenceDefinitions")
        project_ids = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, occurrence_definitions, 'SYSMOD::Project')               
        print(f"Found {len(project_ids)} project IDs")
    
    simplified_projects = []
    
    for item in project_ids:
        # Fetch the actual element to get its name if it's an ID, otherwise use the element directly
        if isinstance(item, dict):
            el = item
        else:
            el = mbse4u_sysmlv2.get_element_fromAPI(query_url, item)
            
        if el:
            simplified_projects.append({'name': el.get('declaredName'), '@id': el.get('@id')})

    return simplified_projects


def get_sysmod_project(server_url, project_id, commit_id, element_id):
    """
    Retrieves the project documentation element.
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    # Get Element
    element = mbse4u_sysmlv2.get_element_fromAPI(query_url, element_id)
    if not element:
        raise ValueError(f"Element {element_id} not found.")

    # Get Documentation via Helper
    doc_text = mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, element_id)
    
    response_data = {}
    response_data['name'] = element.get('declaredName')
    if doc_text:
        response_data['documentation'] = doc_text
        
    return response_data

def get_problem_statement(server_url, project_id, commit_id, element_id):
    """
    Retrieves the problem statement documentation element.
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)

    # 1. Get RequirementUsages
    concern_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, element_id, 'ConcernUsage')
    print(f"Found {len(concern_usages)} ConcernUsages")
    req_usages = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'RequirementUsage')
    print(f"Found {len(req_usages)} RequirementUsages")

    # 2. Find one specializing 'problemStatement'
    problem_reqs = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, concern_usages, 'SYSMOD::Project::problemStatement')
    if not problem_reqs:
        problem_reqs = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, req_usages, 'SYSMOD::Project::problemStatement')
    
    if problem_reqs:
        # 3. Get Documentation
        doc_text = mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, problem_reqs[0]['@id'])
        if doc_text: 
            return {'id': problem_reqs[0]['@id'], 'body': doc_text}
        
    return None

def save_problem_statement(server_url, project_id, commit_id, problem_statement_id, body):
    """
    Saves the problem statement documentation element.
    """
    return mbse4u_sysmlv2.update_model_element(server_url, project_id, commit_id, problem_statement_id, "body", body)

def get_system_idea(server_url, project_id, commit_id, element_id):
    """
    Retrieves the system idea documentation.
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    # 1. Find PartUsage specialized from 'systemIdeaContext'
    part_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, element_id, 'SYSMOD::Project::PartUsage')
    context_parts = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'SYSMOD::Project::systemIdeaContext')
    if len(context_parts) > 1:
        print(f"Warning: Multiple elements specializing 'systemIdeaContext' found. Using the first one.")
    context_part = context_parts[0] if context_parts else None
    
    if context_part:
        # 2. Find 'systemOfInterest' usage inside context
        sub_parts = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, context_part['@id'], 'SYSMOD::Project::PartUsage')
        # Here we look for name 'systemOfInterest' directly, or specialization?
        # User requirement was: "owns another part usage with name systemOfInterest"
        # So name match is sufficient.
        
        system_of_interest = next((p for p in sub_parts if p.get('name') == 'systemOfInterest'), None)
        
        # If not found by name, try specialization just in case?
        if not system_of_interest:
             found_elements = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, sub_parts, 'SYSMOD::Project::systemOfInterest')
             system_of_interest = found_elements[0] if found_elements else None

        if system_of_interest:
             # 3. Get Documentation
             doc_text = mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, system_of_interest['@id'])
             if doc_text:
                 return {'body': doc_text}
             else:
                print(f"Try to find Documentation via Definition: {system_of_interest.get('definition')[0]['@id']}")
                definition = mbse4u_sysmlv2.get_element_fromAPI(query_url, system_of_interest.get('definition')[0]['@id'])
                if definition:
                    doc_text_def = mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, definition['@id'])
                    if doc_text_def:
                        return {'body': doc_text_def}             

    return None



def get_context(server_url, project_id, commit_id, sysmod_project_id, context_type):
    """
    Retrieves the context information.
    Returns { context, system, actors }
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    sysmod_project = mbse4u_sysmlv2.get_element_fromAPI(query_url, sysmod_project_id)
    print(f"ownedPart: {sysmod_project.get('ownedPart')}")
    part_usages_ids = [p['@id'] for p in sysmod_project.get('ownedPart', [])]
    part_usages = mbse4u_sysmlv2.get_elements_fromAPI(query_url, part_usages_ids)
    found_contexts = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, context_type, 'PartUsage')
    context_part = found_contexts[0] if found_contexts else None
    
    if not context_part:
        return None
        
    print(f"Found Context: {context_part.get('name')} ({context_part.get('@id')})")

    system = get_context_system(server_url, project_id, commit_id, context_part)
    actors = get_context_actors(server_url, project_id, commit_id, context_part)
    return {
        "context": context_part,
        "system": system,
        "actors": actors
    }


def get_context_system(server_url, project_id, commit_id, context_part):
    """
    Retrieves the system of interest from the context.
    Returns system of interest part usage
    """
    print(f"get_context_system called with context_id: {server_url}/projects/{project_id}/commits/{commit_id}/elements/{context_part['@id']}")
    context_parts = mbse4u_sysmlv2.get_owned_usages(server_url, project_id, commit_id, context_part, 'ownedPart')
    print(f"Found {len(context_parts)} parts in context")
    system_of_interest = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, context_parts, 'SYSMOD::SystemContext::systemOfInterest')
    system_of_interest = system_of_interest[0] if system_of_interest else None
    system_id = ""
    if system_of_interest:
        system_id = system_of_interest['@id']
    else:
        return None 
    system = mbse4u_sysmlv2.get_element_fromAPI(mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id), system_id)
    system['parts'] = mbse4u_sysmlv2.get_owned_usages(server_url, project_id, commit_id, system, 'ownedPart')    
    return system


def get_context_actors(server_url, project_id, commit_id, context_part):
    """
    Retrieves the actors from the context.
    Returns actors part usages
    """
    print(f"get_context_actors called with context_id: {server_url}/{project_id}/{commit_id}/{context_part['@id']}")
    context_parts = mbse4u_sysmlv2.get_owned_usages(server_url, project_id, commit_id, context_part, 'ownedPart')
    print(f"Found {len(context_parts)} parts in context")
    actors = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, context_parts, 'SYSMOD::SystemContext::actors')
   
    return actors


def get_stakeholders(server_url, project_id, commit_id, sysmod_project_id):
    """
    Retrieves all stakeholders and their attributes.
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    # Let's get 'PartUsage' from root.
    # root_parts = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'PartUsage')
    # project_stakeholders = mbse4u_sysmlv2.get_elements_byProperty_fromAPI(server_url, project_id, commit_id, 'qualifiedName', 'SYSMOD::Project::projectStakeholders')
    # project_stakeholders = project_stakeholders[0] if project_stakeholders else None
    
    sysmod_project = mbse4u_sysmlv2.get_element_fromAPI(query_url, sysmod_project_id)
    sysmod_project_partusages = mbse4u_sysmlv2.get_owned_usages(server_url, project_id, commit_id, sysmod_project, 'ownedPart')
    stakeholder_part_usages = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, sysmod_project_partusages, 'SYSMOD::Project::projectStakeholders', 'PartUsage')
    print(f"\n\nstakeholder_features: {len(stakeholder_part_usages)}\n\n")
    return None
    stakeholders = []
    
    candidates = []
    # Check root parts and their children (1 level down)
    for p in root_parts:
        candidates.append(p)
        children = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, p['@id'], 'PartUsage')
        candidates.extend(children)

    for p in candidates:
        if mbse4u_sysmlv2.check_specialization_hierarchy(query_url, p, project_stakeholders, "SYSMOD::Project::projectStakeholders"):
            print(f"Found Stakeholder: {p.get('name')} {p.get('@id')}")
                
            # Extract attributes
            # We need helper to extract specific attrs: risk, effort, priority, contact, categories
            attributes = {
                'name': p.get('name'),
                'description': mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, p.get('@id')), # Generic Helper
                'contact': mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, p, 'contact') or "",
                'risk': mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, p, 'risk') or "unknown",
                'effort': mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, p, 'effort') or "unknown",
                'categories': mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, p, 'categories') or []
            }
            stakeholders.append(attributes)
            
    return stakeholders

def get_feature_bindings_container(server_url, project_id, commit_id):
    """
    Retrieves container for dependency relationships annotated with @FB.
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    # 1. Find ID of MetadataDefinition "featureBindings"
    fb_metadata_id_map = mbse4u_sysmlv2.get_metadata_ids_by_name(server_url, project_id, commit_id, ['featureBindings'])
    print(f"# elements found: {len(fb_metadata_id_map)}: {fb_metadata_id_map}")
    fb_id = fb_metadata_id_map.get('featureBindings')
    
    if not fb_id:
        print("MetadataDefinition 'featureBindings' not found.")
        return []

    # 2. Find elements annotated with @FB
    annotated_ids_map = mbse4u_sysmlv2.get_metadatausage_annotatedElement_ids(server_url, project_id, commit_id, {'featureBindings': fb_id})
    annotated_ids = annotated_ids_map.get('featureBindings', [])
    
    if not annotated_ids:
        print("No elements annotated with @featureBindings found.")
        return [] 
        
    return annotated_ids

def get_feature_bindings(server_url, project_id, commit_id):
    """
    Retrieves dependency relationships annotated with @FB.
    """
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    # 1. Find ID of MetadataDefinition "FB"
    fb_metadata_id_map = mbse4u_sysmlv2.get_metadata_ids_by_name(server_url, project_id, commit_id, ['FB'])
    print(f"# elements found: {len(fb_metadata_id_map)}: {fb_metadata_id_map}")
    fb_id = fb_metadata_id_map.get('FB')
    
    if not fb_id:
        print("MetadataDefinition 'FB' not found.")
        return []

    # 2. Find elements annotated with @FB
    annotated_ids_map = mbse4u_sysmlv2.get_metadatausage_annotatedElement_ids(server_url, project_id, commit_id, {'FB': fb_id})
    annotated_ids = annotated_ids_map.get('FB', [])
    
    if not annotated_ids:
        print("No elements annotated with @FB found.")
        return []

    bindings = []
    
    # 3. Process each annotated element
    for element_id in annotated_ids:
        element = mbse4u_sysmlv2.get_element_fromAPI(query_url, element_id)
        if not element: continue
        
        # Owner should be a dependency
        owner = element.get('owner')
        if not owner: continue
        feature_binding = mbse4u_sysmlv2.get_element_fromAPI(query_url, owner['@id'])
        if not feature_binding: continue

        entry = {
            'id': feature_binding.get('@id'),
            'type': feature_binding.get('@type'),
            'client': '',
            'supplier': ''
        }
        
        if feature_binding.get('client'):
             client_ref = feature_binding.get('client')[0]
             client_el = mbse4u_sysmlv2.get_element_fromAPI(query_url, client_ref['@id'])
             if client_el: 
                 entry['client'] = {'name': client_el.get('name') or client_el.get('declaredName') or "Unknown", 'id': client_el.get('@id')}

        if feature_binding.get('supplier'):
             supplier_ref = feature_binding.get('supplier')[0]
             supplier_el = mbse4u_sysmlv2.get_element_fromAPI(query_url, supplier_ref['@id'])
             if supplier_el: 
                 entry['supplier'] = {'name': supplier_el.get('name') or supplier_el.get('declaredName') or "Unknown", 'id': supplier_el.get('@id')}

        bindings.append(entry)
        
    return bindings

def create_feature_binding(server_url, project_id, commit_id, client_id, supplier_id):
    """
    Creates a new Dependency from client_id to supplier_id and annotates it with @FB.
    """
    print(f"Creating Feature Binding between {client_id} and {supplier_id}")
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    feature_bindings_containers = get_feature_bindings_container(server_url, project_id, commit_id)
    if not feature_bindings_containers:
        print("Error: Feature Bindings Container not found.")
        return None
    feature_bindings_container_id = feature_bindings_containers[0]
    print(f"Feature Bindings Container ID: {feature_bindings_container_id}")
    
    # Implementation pending valid WRITE access pattern.
    return None



def get_feature_tree_uvl(server_url, project_id, commit_id, sysmod_project_id):
    """
    Retrieves the textual representation of the Feature Tree.
    """
    # 1. Find Usage of 'FeatureModel'
    # We look for a usage that specializes 'FeatureModel'? Or is it a package?
    # Based on previous context, we look for MetadataUsage of 'featureTree' (annotated element)
    
    print("Getting UVL feature tree")   
    id_map = mbse4u_sysmlv2.get_metadata_ids_by_name(server_url, project_id, commit_id, ['featureTree'])
    ft_id = id_map.get('featureTree')
    
    if not ft_id:
        return {"error": "Metadata 'featureTree' not found"}
        
    usage_map = mbse4u_sysmlv2.get_metadatausage_annotatedElement_ids(server_url, project_id, commit_id, {'featureTree': ft_id})
    annotated_ids = usage_map.get('featureTree', [])
    
    if not annotated_ids:
        return {"error": "No elements annotated with @featureTree found"}
        
    # Assuming first one is the separate textual representation
    # The annotated element is likely the Feature Model Package or Usage.
    # We need to find the "TextualRepresentation" inside it?
    
    annotated_id = annotated_ids[0]
    
    # Get contained TextualRepresentation
    text_reps = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, annotated_id, 'TextualRepresentation')
    print(f"get_contained_elements: {len(text_reps)} matching elements found in 'TextualRepresentation': {text_reps[0].get('body', '')}")
    if text_reps:
        # Return the body (UVL code)
        return {"uvl_code": text_reps[0].get('body', '')}
    
    return {"uvl_code": "// No textual representation found."}

def get_sysmod_status(server_url, project_id, commit_id, sysmod_project_id):
    """
    Checks for the existence of various SYSMOD artifacts to populate the status grid.
    Returns a dictionary with status (bool) for each artifact.
    """
    print(f"Checking SYSMOD status for project {sysmod_project_id}")
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    status = {
        "FEATURE": False,
        "BFAC": False,
        "STAKE": False,
        "PS": False,
        "SIC": False,
        "SC": False,
        "UC": False,
        "RE": False,
        "FUC": False,
        "LAC": False,
        "PAC": False
    }

    # 1. FEATURE (Feature Tree)
    # Check for metadata usage 'featureTree'
    ft_ids = mbse4u_sysmlv2.get_metadata_ids_by_name(server_url, project_id, commit_id, ['featureTree'])
    if ft_ids.get('featureTree'):
        usages = mbse4u_sysmlv2.get_metadatausage_annotatedElement_ids(server_url, project_id, commit_id, {'featureTree': ft_ids['featureTree']})
        if usages.get('featureTree'):
            status["FEATURE"] = True

    # Get all PartUsages in the sysmod project to optimize context checks
    part_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'PartUsage')
    
    # 2. BFAC (Brownfield Context)
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'brownfieldSystemContext'):
        status["BFAC"] = True

    # 3. STAKE (Stakeholders)
    # Check if 'projectStakeholders' is specialized
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'projectStakeholders'):
        status["STAKE"] = True
    else:
        # Fallback: check one level deeper as get_stakeholders does
        for p in part_usages:
            children = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, p['@id'], 'PartUsage')
            if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, children, 'projectStakeholders'):
                status["STAKE"] = True
                break

    # 4. PS (Problem Statement)
    concern_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'ConcernUsage')
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, concern_usages, 'problemStatement'):
        status["PS"] = True
    else:
        # Fallback: Check global RequirementUsage
        all_req_usages = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'RequirementUsage')
        if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, all_req_usages, 'problemStatement'):
            status["PS"] = True

    # 5. SIC (System Idea)
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'systemIdeaContext'):
        status["SIC"] = True

    # 6. SC (System Context)
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'systemContext'):
        status["SC"] = True

    # 7. UC (Use Cases)
    uc_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'UseCaseUsage')
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, uc_usages, 'useCase'):
        status["UC"] = True
    if not status["UC"]:
        all_ucs = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'UseCaseUsage')
        if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, all_ucs, 'useCase'):
             status["UC"] = True

    # 8. RE (Requirements)
    req_usages_generic = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'RequirementUsage')
    if req_usages_generic:
        status["RE"] = True
    if not status["RE"]:
         all_reqs = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'RequirementUsage')
         if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, all_reqs, 'requirement'):
             status["RE"] = True

    # 9. FUC (Functional Architecture Context)
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'functionalArchitectureContext'):
        status["FUC"] = True

    # 10. LAC (Logical Architecture Context)
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'logicalArchitectureContext'):
        status["LAC"] = True

    # 11. PAC (Physical Architecture Context / Product Context)
    if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'physicalArchitectureContext'):
         status["PAC"] = True
    elif mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'productContext'):
         status["PAC"] = True

    return status

def get_sysmod_requirements(server_url, project_id, commit_id, sysmod_project_id):
    """
    Retrieves requirements from the model (currently dummy data).
    """

    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)

    # 1. Get RequirementUsages
    sysmod_project = mbse4u_sysmlv2.get_element_fromAPI(query_url, sysmod_project_id)
    req_usages = []
    if sysmod_project:
        req_usages_ids = [p['@id'] for p in sysmod_project.get('ownedRequirement', [])]
        req_usages = mbse4u_sysmlv2.get_elements_fromAPI(query_url, req_usages_ids)
    else:
        req_usages = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'RequirementUsage')
    print(f"Found {len(req_usages)} RequirementUsages")

    # 2. Find one specializing 'problemStatement'
    requirement_specifications = mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, req_usages, 'SYSMOD::Project::systemRequirementSpecification')
    print(f"Found {len(requirement_specifications)} RequirementSpecifications")

    owned_requirements = [] 
    if requirement_specifications:
        # 3. Get owned requirements
        owned_requirements = mbse4u_sysmlv2.get_owned_usages(server_url, project_id, commit_id, requirement_specifications[0], 'ownedFeature')
        print(f"Found {len(owned_requirements)} owned requirements")

    sysmod_requirements = []
    if owned_requirements:
        for req in owned_requirements:
            req_doc = mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, req['@id'])
            if req_doc:
                sysmod_requirements.append({
                    "identifier": req.get('shortName'),
                    "name": req.get('declaredName'),
                    "uri": req.get('@id'),
                    "text": req_doc,
                    "motivation": mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, req, 'motivation') or "",
                    "priority": mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, req, 'priority') or "",
                    "obligation": mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, req, 'obligation') or "",
                    "stability": mbse4u_sysmlv2.get_feature_value(server_url, project_id, commit_id, req, 'stability') or ""
                })
    
    return sysmod_requirements  

def get_sysmod_usecases(server_url, project_id, commit_id, sysmod_project_id    ):
    """
    Retrieves use cases from the model (currently dummy data).
    """

    requirement_system_context = get_context(server_url, project_id, commit_id, sysmod_project_id, 'SYSMOD::Project::requirementSystemContext')
    if requirement_system_context:
        print(f"Found requirementSystemContext: {server_url}/projects/{project_id}/commits/{commit_id}/elements/{requirement_system_context['@id']}")
        
    # Dummy Data for Use Case

    dummy_usecases = [
        {
            "name": "Register New User",
            "description": "A new user registers to the system via web interface.",
            "actors": ["User", "System Admin"]
        },
        {
            "name": "Process Payment",
            "description": "The system processes a credit card payment securely.",
            "actors": ["User", "Payment Gateway"]
        },
        {
            "name": "Generate Report",
            "description": "Admin generates a monthly sales report.",
            "actors": ["System Admin"]
        },
        {
            "name": "Manage Inventory",
            "description": "Staff updates stock levels for products.",
            "actors": ["Warehouse Staff", "System"]
        }
    ]
    return dummy_usecases
