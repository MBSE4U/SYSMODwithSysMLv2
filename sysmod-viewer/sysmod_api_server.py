#
#   Simple Flask server for the SYSMOD Methodology
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

from flask import Flask, send_from_directory, request, jsonify, Response
import requests
from anytree import NodeMixin, RenderTree
import sys
import os
import io
import json
import csv
import traceback
import importlib
from typing import Optional
from functools import wraps

import sysmod_api_helpers 
import mbse4u_sysmlv2_api_helpers as mbse4u_sysmlv2
from enum import Enum

class SysmodContextKinds(Enum):
    BROWNFIELD = 'SYSMOD::Project::brownfieldSystemContext'
    SYSTEMIDEA = 'SYSMOD::Project::systemIdeaContext'
    SYSTEM = 'SYSMOD::Project::requirementSystemContext'
    FUNCTIONAL = 'SYSMOD::Project::functionalSystemContext'
    LOGICAL = 'SYSMOD::Project::logicalSystemContext'
    PRODUCT = 'SYSMOD::Project::productSystemContext'

# OpenAI Configuration
# These keys should ideally be loaded from environment variables or a secure configuration management system,
# not hardcoded or passed directly in every request for security reasons.
# For demonstration purposes, they might be set here or expected in the request body of specific API calls.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "") # Example: Load from environment variable
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID", "") # Example: Load from environment variable

app = Flask(__name__, static_folder='html')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Optional: Pretty print JSON
app.config['JSONIFY_MIMETYPE'] = 'application/json'

# Global SYSMOD Cache
# Value: Dict[sysmod_element, element_data]
SYSMOD_CACHE = {}

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static files (including images)
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

################################################################################################################
#
# Decorator to handle errors in routes
#
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError

# ... imports ...

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ReadTimeout:
            print(f"ReadTimeout in {func.__name__}")
            return jsonify({"error": "The server took too long to respond (Read Timeout). Please try again later or check your network connection."}), 504
        except ConnectTimeout:
            print(f"ConnectTimeout in {func.__name__}")
            return jsonify({"error": "Could not connect to the server (Connection Timeout). Please check the Server URL and your network."}), 504
        except ConnectionError:
            print(f"ConnectionError in {func.__name__}")
            return jsonify({"error": "Network error occurred. Failed to connect to the server."}), 503
        except requests.HTTPError as e:
            print(f"HTTP Error in {func.__name__}: {e}")
            return jsonify({"error": f"HTTP error: {str(e)}"}), 500
        except Exception as e:
            traceback.print_exc()
            print(f"Error in {func.__name__}: {e}")
            return jsonify({"error": str(e)}), 500
    return wrapper

################################################################################################################
#
# API Endpoints
#

#
# Cache Warmup
#
@app.route('/api/cache/warmup', methods=['POST'])
@handle_errors
def api_cache_warmup():
    input_data = request.json
    print(f"/api/cache/warmup called with data: {input_data}")
    
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    page_size = input_data.get('page_size', 256)
    
    if not all([server_url, project_id, commit_id]):
        raise ValueError("Required parameters missing.")
        
    count = mbse4u_sysmlv2.load_model_cache(server_url, project_id, commit_id, page_size)
    return jsonify({"status": "success", "cached_elements": count})

#
# Retrieve List of Projects on a given Server
#
@app.route('/api/projects', methods=['POST'])
@handle_errors
def api_projects():
    input_data = request.json
    print(f"/api/projects called with data: {input_data}")
    server_url = input_data.get('server_url')
    if not server_url:
        return jsonify({"error": "server_url is required"}), 400
        
    page_size = input_data.get('page_size', 256)

    # Call the utility function
    projects = mbse4u_sysmlv2.get_projects(server_url, page_size)
    print(f"{len(projects)} projects found.")
    return jsonify(projects)

#
# Retrieve List of Commits for a given ProjectID
#
@app.route('/api/commits', methods=['POST'])
@handle_errors
def api_commits():
    input_data = request.json
    print(f"/api/commits called with data: {input_data}")

    # Extract input values
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id', "").split(' ')[0]  # Safely split and handle edge cases

    # Fetch commits using the utility function
    commits = mbse4u_sysmlv2.get_commits(server_url, project_id)
    return jsonify(commits)

#
# Get SYSMOD Projects
#
@app.route('/api/sysmod_projects', methods=['POST'])
@handle_errors
def api_sysmod_projects():
    input_data = request.json
    print(f"/api/sysmod_projects called with data: {input_data}")

    # Required inputs
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')

    if not server_url or not project_id or not commit_id:
        raise ValueError("Server_url, project_id, and commit_id are required.")

    simplified_projects = sysmod_api_helpers.get_sysmod_projects(server_url, project_id, commit_id)
            
    print(f"Returning {len(simplified_projects)} simplified projects.")
    return jsonify(simplified_projects)

#
# Get Project Details (Name + Documentation)
#
@app.route('/api/sysmod_project', methods=['POST'])
@handle_errors
def api_sysmod_project():
    input_data = request.json
    print(f"\n/api/sysmod_project called with data: {input_data}")

    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('element_id')

    if 'PROJECT_ID' in SYSMOD_CACHE and SYSMOD_CACHE['PROJECT_ID'] == sysmod_project_id:
        if 'PROJECT' in SYSMOD_CACHE:
            print("Returning cached project") 
            return jsonify(SYSMOD_CACHE['PROJECT'])
    else:
        SYSMOD_CACHE.clear()

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    response_data = sysmod_api_helpers.get_sysmod_project(server_url, project_id, commit_id, sysmod_project_id)
    print(f"Returning sysmod project: {response_data}")
    SYSMOD_CACHE['PROJECT_ID'] = sysmod_project_id
    SYSMOD_CACHE['PROJECT'] = response_data
    return jsonify(response_data)


#
# Get Generic Element by ID
#
@app.route('/api/element', methods=['POST'])
@handle_errors
def api_element():
    input_data = request.json
    print(f"/api/element called with data: {input_data}")

    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    element_id = input_data.get('element_id')

    if not all([server_url, project_id, commit_id, element_id]):
        raise ValueError("server_url, project_id, commit_id, and element_id are required.")

    query_url = f"{server_url}/projects/{project_id}/commits/{commit_id}"
    element = mbse4u_sysmlv2.get_element_fromAPI(query_url, element_id)
    
    # Enrich with documentation if not present as a property or object
    if element and ('documentation' not in element):
        doc_text = mbse4u_sysmlv2.get_element_documentation(server_url, project_id, commit_id, element_id)
        if doc_text:
            element['documentation'] = doc_text
    
    return jsonify(element)

#
# Get Problem Statement
#
@app.route('/api/problem-statement', methods=['POST'])
@handle_errors
def api_problem_statement():
    input_data = request.json
    print(f"\n/api/problem-statement called with data: {input_data}")

    if 'PROBLEMSTATEMENT' in SYSMOD_CACHE:
        print("Returning cached problem statement") 
        return jsonify(SYSMOD_CACHE['PROBLEMSTATEMENT'])

    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id') # This is the project element ID

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    problem_stmt = sysmod_api_helpers.get_problem_statement(server_url, project_id, commit_id, sysmod_project_id)
    if problem_stmt:
        print(f"Returning problem statement: {problem_stmt}")   
        SYSMOD_CACHE['PROBLEMSTATEMENT'] = problem_stmt
        return jsonify(problem_stmt)
    else:
        return jsonify({"error": "Problem statement not found"}), 404

#
# Save Problem Statement
#
@app.route('/api/problem-statement/save', methods=['POST'])
@handle_errors
def api_save_problem_statement():
    input_data = request.json
    print(f"/api/problem-statement/save called with data: {input_data}")

    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')
    new_text = input_data.get('text')

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    # Prepare for saving logic (Stub)
    print(f"Would save new problem statement: '{new_text}' to project {sysmod_project_id}")
    problem_stmt = sysmod_api_helpers.get_problem_statement(server_url, project_id, commit_id, sysmod_project_id)
    print(f"Current problem statement: '{problem_stmt}'")
    new_commit_id = mbse4u_sysmlv2.update_model_element(server_url, project_id, commit_id, problem_stmt.get('id'), "body", new_text)
    print(f"New commit ID: {new_commit_id}")
    return jsonify({"status": "success", "message": "Problem statement saved (simulation).", "commit_id": new_commit_id})

#
# Get System Idea
#
@app.route('/api/system-idea', methods=['POST'])
@handle_errors
def api_system_idea():
    input_data = request.json
    print(f"/api/system-idea called with data: {input_data}")

    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    sys_idea_doc = sysmod_api_helpers.get_system_idea(server_url, project_id, commit_id, sysmod_project_id)
    
    return jsonify(sys_idea_doc)

#
# Get Brownfield Context
#
@app.route('/api/sysmod-context', methods=['POST'])
@handle_errors
def api_context():
    input_data = request.json
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')
    context_type = input_data.get('context_type')

    print(f"\n/api/sysmod-context called with data: {input_data}")

    if context_type in SYSMOD_CACHE:
        print("Returning cached context") 
        return jsonify(SYSMOD_CACHE[context_type])

    if not context_type in SysmodContextKinds._member_map_:
        print(f"Unknown context type: {context_type}")
        return jsonify({"error": f"Unknown context type: {context_type}"}), 400

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("Required parameters missing.")

    context = sysmod_api_helpers.get_context(server_url, project_id, commit_id, sysmod_project_id, SysmodContextKinds[context_type].value)
    SYSMOD_CACHE[context_type] = context
    return jsonify(context)

#
# Get Requirements
#
@app.route('/api/sysmod-requirements', methods=['POST'])
@handle_errors
def api_requirements():
    input_data = request.json
    print(f"/api/sysmod-requirements called with data: {input_data}")
    
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')
    
    if not all([server_url, project_id, commit_id, sysmod_project_id]):
         raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    requirements = sysmod_api_helpers.get_sysmod_requirements(server_url, project_id, commit_id, sysmod_project_id)
    
    return jsonify(requirements)

#
# Get Use Cases
#
@app.route('/api/sysmod-usecases', methods=['POST'])
@handle_errors
def api_usecases():
    input_data = request.json
    print(f"/api/sysmod-usecases called with data: {input_data}")
    
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')
    
    if not all([server_url, project_id, commit_id, sysmod_project_id]):
         raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    usecases = sysmod_api_helpers.get_sysmod_usecases(server_url, project_id, commit_id, sysmod_project_id)
    
    return jsonify(usecases)

#
# Get Stakeholders
#
@app.route('/api/stakeholders', methods=['POST'])
@handle_errors
def api_stakeholders():
    input_data = request.json
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("Required parameters missing.")

    #if 'STAKEHOLDERS' in SYSMOD_CACHE:
    #    return jsonify(SYSMOD_CACHE['STAKEHOLDERS'])

    stakeholders = sysmod_api_helpers.get_stakeholders(server_url, project_id, commit_id, sysmod_project_id)
    if stakeholders:
        SYSMOD_CACHE['STAKEHOLDERS'] = stakeholders
        print(f"Stakeholders: {stakeholders}")  
        return jsonify(stakeholders)
    else:
        return None

#
# Get Feature Bindings
#
@app.route('/api/feature-bindings', methods=['POST'])
@handle_errors
def api_feature_bindings():
    input_data = request.json
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')

    if not all([server_url, project_id, commit_id]):
        raise ValueError("Required parameters missing.")

    bindings = sysmod_api_helpers.get_feature_bindings(server_url, project_id, commit_id)
    return jsonify(bindings)

#
# Toggle Feature Binding (Create/Delete)
#
@app.route('/api/feature-bindings/toggle', methods=['POST'])
@handle_errors
def api_feature_bindings_toggle():
    input_data = request.json
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    client_id = input_data.get('client_id')
    supplier_id = input_data.get('supplier_id')
    binding_id = input_data.get('binding_id')
    
    if binding_id:
        # Delete using the provided ID
        success = sysmod_api_helpers.delete_feature_binding(server_url, project_id, commit_id, binding_id)
        return jsonify({"action": "deleted", "success": success})
    else:
        # Create
        new_id = sysmod_api_helpers.create_feature_binding(server_url, project_id, commit_id, client_id, supplier_id)
        return jsonify({"action": "created", "id": new_id, "success": True if new_id else False})

@app.route('/api/feature-tree-uvl', methods=['POST'])
@handle_errors
def api_feature_tree_uvl():
    data = request.json
    server_url = data.get('server_url')
    project_id = data.get('project_id')
    commit_id = data.get('commit_id')
    sysmod_project_id = data.get('sysmod_project_id')
    
    print(f"/api/feature-tree_uvl called with data: {data}")

    if 'FEATURETREEUVL' in SYSMOD_CACHE:
        return jsonify(SYSMOD_CACHE['FEATURETREEUVL'])
    
    if not all([server_url, project_id, commit_id, sysmod_project_id]):
         return jsonify({"error": "Missing parameters"}), 400

    result = sysmod_api_helpers.get_feature_tree_uvl(server_url, project_id, commit_id, sysmod_project_id)
    SYSMOD_CACHE['FEATURETREEUVL'] = result
    if result:
        return jsonify(result)
    else:
        return None

@app.route('/api/feature-tree-sysml', methods=['POST'])
def api_feature_tree_sysml():
    data = request.json
    print(f"/api/feature-tree-sysml called with data: {data}")

    if 'FEATURETREESYSML' in SYSMOD_CACHE:
        return jsonify(SYSMOD_CACHE['FEATURETREESYSML'])

    # Dummy Matrix Data
    # Columns: Feature Name, Config 1, Config 2, ...
    headers = ["Feature", "Standard", "Premium", "Sport"]
    
    matrix_rows = [
        {"name": "Vehicle", "values": ["Selected", "Selected", "Selected"]},
        {"name": "Engine", "values": ["Selected", "Selected", "Selected"]},
        {"name": "Electric", "values": ["Unselected", "Selected", "Unselected"]},
        {"name": "Gasoline", "values": ["Selected", "Unselected", "Selected"]},
        {"name": "Infotainment", "values": ["Unselected", "Selected", "Selected"]}
    ]

    # Dummy Tree Code (Mermaid) for visualization
    # Ideally this matches the matrix structure
    graph_code = """graph TD
    Vehicle --> Engine
    Vehicle --> Infotainment
    Engine --> Electric
    Engine --> Gasoline
    style Electric fill:#bbf,stroke:#333,stroke-width:2px
    style Gasoline stroke-dasharray: 5 5
    """
    result = {
        "matrix": {
            "headers": headers,
            "rows": matrix_rows
        },
        "graph_code": graph_code
    }
    SYSMOD_CACHE['FEATURETREESYSML'] = result

    if result:
        return jsonify(result)
    else:
        return None

@app.route('/api/quality-checks', methods=['POST'])
def api_quality_checks():
    data = request.json
    print(f"\n/api/quality-checks called with data: {data}")
    
    server_url = data.get('server_url')
    project_id = data.get('project_id')
    commit_id = data.get('commit_id')
    sysmod_project_id = data.get('sysmod_project_id')
    activated_views = data.get('activated_views', [])
    
    print(f"Context: {project_id} / {commit_id} / {sysmod_project_id}")
    print(f"Active views for quality check: {activated_views}")
    
    quality_checks = []
    
    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        quality_checks.append({
            "id": "VIEWER-000",
            "title": "Missing Parameters",
            "description": "One of the parameters is missing: server_url, project_id, commit_id, sysmod_project_id",
            "status": "failed"
        })
        return jsonify(quality_checks)

    if 'problem_statement' in activated_views:
        problem_stmt = None
        if 'PROBLEMSTATEMENT' in SYSMOD_CACHE:
            problem_stmt = SYSMOD_CACHE['PROBLEMSTATEMENT']
        else:
            problem_stmt = sysmod_api_helpers.get_problem_statement(server_url, project_id, commit_id, sysmod_project_id)   
            SYSMOD_CACHE['PROBLEMSTATEMENT'] = problem_stmt

        if not problem_stmt:
            quality_checks.append({
                "id": "SYSMOD-001",
                "title": "Missing Problem Statement",
                "description": "The model does not contain a problem statement.",
                "status": "failed"
        })
        else:
            quality_checks.append({
                "id": "SYSMOD-001",
                "title": "Problem Statement",
                "description": "The model contains a problem statement.",
                "status": "successful"
        })
    
    if 'system_idea' in activated_views:
        sys_idea_doc = sysmod_api_helpers.get_system_idea(server_url, project_id, commit_id, sysmod_project_id)
        if not sys_idea_doc:
            quality_checks.append({
                "id": "SYSMOD-002",
                "title": "Missing System Idea",
                "description": "The model does not contain a system idea.",
                "status": "failed"
        })
        else:
            quality_checks.append({
                "id": "SYSMOD-002",
                "title": "System Idea",
                "description": "The model contains a system idea.",
                "status": "successful"
        })
       
    return jsonify(quality_checks)

#
# SYSMOD Status
#
@app.route('/api/sysmod-atlas', methods=['POST'])
@handle_errors
def api_sysmod_atlas():
    input_data = request.json
    print(f"/api/sysmod-atlas called with data: {input_data}")
    
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')
    loadAll = input_data.get('loadAll')
    
    if not all([server_url, project_id, commit_id, sysmod_project_id]):
         return jsonify({"error": "Missing parameters"}), 400

    print(f"Getting SYSMOD atlas for project {sysmod_project_id}")
    query_url = mbse4u_sysmlv2.get_commit_url(server_url, project_id, commit_id)
    
    atlas = {
        "FEATURE": False,
        "BROWNFIELD": False,
        "STAKEHOLDERS": False,
        "PROBLEMSTATEMENT": False,
        "SYSTEMIDEA": False,
        "SYSTEM": False,
        "USECASES": False,
        "REQUIREMENTS": False,
        "FUNCTIONAL": False,
        "LOGICAL": False,
        "PRODUCT": False
    }

    # 1. FEATURE (Feature Tree)
    if 'FEATURETREEUVL' in SYSMOD_CACHE:
        atlas["FEATURE"] = True 
    elif loadAll:
        feature_tree_uvl = sysmod_api_helpers.get_feature_tree_uvl(server_url, project_id, commit_id, sysmod_project_id)
        if feature_tree_uvl:
            atlas["FEATURE"] = True
            SYSMOD_CACHE['FEATURETREEUVL'] = feature_tree_uvl

    # 2. Check Context Kinds
    
    # Mapping from Enum Name to Frontend Grid ID Suffix
    kind_to_grid_map = {
        'BROWNFIELD': 'BFAC',
        'SYSTEMIDEA': 'SIC',
        'SYSTEM': 'SC',
        'FUNCTIONAL': 'FUC',
        'LOGICAL': 'LAC',
        'PRODUCT': 'PAC'
    }

    for kind in SysmodContextKinds:
        # Determine the key used in the Atlas dictionary (must match frontend IDs)
        atlas_key = kind_to_grid_map.get(kind.name, kind.name)
        
        # Check Cache using the Enum Name (as stored in api_context)
        cache_key = kind.name
        
        if cache_key in SYSMOD_CACHE:
            atlas[atlas_key] = True
        elif loadAll:
            try:
                # We pass the Enum Value (qualified name) to get_context
                ctx_data = sysmod_api_helpers.get_context(server_url, project_id, commit_id, sysmod_project_id, kind.value)
                if ctx_data:
                    atlas[atlas_key] = True
                    SYSMOD_CACHE[cache_key] = ctx_data
            except Exception as e:
                print(f"Error loading {kind.name}: {e}")
        else:
            # Fallback Light Check (Original Layout)
            def check_specialization(qualified_name):
                return mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, qualified_name)
                
            if not atlas.get(atlas_key):
                if check_specialization(kind.value):
                    atlas[atlas_key] = True

    # 3. STAKEHOLDERS
    if 'STAKEHOLDERS' in SYSMOD_CACHE:
        atlas["STAKE"] = True
    elif loadAll:
        stakeholders = sysmod_api_helpers.get_stakeholders(server_url, project_id, commit_id, sysmod_project_id)
        if stakeholders:
            atlas["STAKE"] = True
            SYSMOD_CACHE['STAKEHOLDERS'] = stakeholders
    else:
        # Light Check
        if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, part_usages, 'projectStakeholders'):
            atlas["STAKE"] = True
        else:
            for p in part_usages:
                children = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, p['@id'], 'PartUsage')
                if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, children, 'projectStakeholders'):
                    atlas["STAKE"] = True
                    break

    # 4. PROBLEM STATEMENT
    if 'PROBLEMSTATEMENT' in SYSMOD_CACHE:
        atlas["PS"] = True
    elif loadAll:
        ps = sysmod_api_helpers.get_problem_statement(server_url, project_id, commit_id, sysmod_project_id)
        if ps:
            atlas["PS"] = True
            SYSMOD_CACHE['PROBLEMSTATEMENT'] = ps
    else:
        # Light Check
        concern_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'ConcernUsage')
        if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, concern_usages, 'problemStatement'):
             atlas["PS"] = True
        else:
             all_req_usages = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'RequirementUsage')
             if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, all_req_usages, 'problemStatement'):
                 atlas["PS"] = True

    # 5. USE CASES
    if 'USECASES' in SYSMOD_CACHE:
        atlas["UC"] = True
    elif loadAll:
        ucs = sysmod_api_helpers.get_sysmod_usecases(server_url, project_id, commit_id, sysmod_project_id)
        if ucs:
            atlas["UC"] = True
            SYSMOD_CACHE['USECASES'] = ucs
    else:
        # Light Check
        uc_usages = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'UseCaseUsage')
        if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, uc_usages, 'useCase'):
             atlas["UC"] = True
        else:
             all_ucs = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'UseCaseUsage')
             if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, all_ucs, 'useCase'):
                  atlas["UC"] = True
            
    # 6. REQUIREMENTS
    if 'REQUIREMENTS' in SYSMOD_CACHE:
        atlas["RE"] = True
    elif loadAll:
        reqs = sysmod_api_helpers.get_sysmod_requirements(server_url, project_id, commit_id, sysmod_project_id)
        if reqs:
            atlas["RE"] = True
            SYSMOD_CACHE['REQUIREMENTS'] = reqs
    else:
        # Light Check
        req_usages_generic = mbse4u_sysmlv2.get_contained_elements(server_url, project_id, commit_id, sysmod_project_id, 'RequirementUsage')
        if req_usages_generic:
             atlas["RE"] = True
        else:
            all_reqs = mbse4u_sysmlv2.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'RequirementUsage')
            if mbse4u_sysmlv2.find_elements_specializing(server_url, project_id, commit_id, all_reqs, 'requirement'):
                atlas["RE"] = True
            
    return jsonify(atlas)

#
# AI Suggestion Endpoint
#
@app.route('/api/ai-suggestion_problem_statement', methods=['POST'])
@handle_errors 
def api_ai_suggestion_problem_statement():
    input_data = request.json
    print(f"/api/ai-suggestion_problem_statement called with data: {input_data}")
    
    text = input_data.get('text', '')
    
    api_key = input_data.get('api_key')
    org_id = input_data.get('org_id')
    
    if not api_key:
         return jsonify({"suggestion": "Error: OpenAI API Key not provided. Please set it in the 'AI Configuration' settings."}), 400

    try:
        from openai import OpenAI
        # Use provided keys
        client = OpenAI(
            api_key=api_key,
            organization=org_id if org_id else None
        )
    except ImportError:
        return jsonify({"suggestion": "Error: OpenAI library not installed. Please install it with 'pip install openai'."}), 500
    except Exception as e:
         return jsonify({"suggestion": f"Error initializing OpenAI client: {str(e)}"}), 500

    prompt = f"""
Please rewrite the following Problem Statement to make it clearer, more concise, and sharply focused on the problem itself rather than the solution.
The rewritten statement must:
- Begin with the phrase "How can we…"
- Be short and impactful, suitable as an elevator pitch that can be explained in 30 seconds or less
- Preserve all original content and meaning
- You may rephrase or restructure the text for clarity
- Do not remove any information
- Avoid introducing solutions, technologies, or implementation details    

    Draft Problem Statement:
    "{text}"
    
    Revised Problem Statement:
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant for Model-Based Systems Engineering experts using the SYSMOD methodology."},
                {"role": "user", "content": prompt}
            ]
        )
        suggestion = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        suggestion = f"Error calling AI service: {str(e)}"
    
    return jsonify({"suggestion": suggestion})

if __name__ == '__main__':
    app.run(debug=True)
