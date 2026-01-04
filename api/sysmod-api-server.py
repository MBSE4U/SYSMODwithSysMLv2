#
#   Simple Flask server for the SYSMOD Methodology
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

from flask import Flask, send_from_directory, request, jsonify, Response
import requests
from anytree import NodeMixin, RenderTree
import os
import io
import json
import csv
import traceback
import sysmod_api_helpers 
from typing import Optional
from functools import wraps

app = Flask(__name__, static_folder='sysmodWeb')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Optional: Pretty print JSON
app.config['JSONIFY_MIMETYPE'] = 'application/json'

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
def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
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
# Retrieve List of Projects on a given Server
#
@app.route('/api/projects', methods=['POST'])
@handle_errors
def api_projects():
    input_data = request.json
    print(f"/api/projects called with data: {input_data}")
    server_url = input_data['server_url']

    # Call the utility function
    projects = sysmod_api_helpers.get_projects(server_url)
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
    commits = sysmod_api_helpers.get_commits(server_url, project_id)
    return jsonify(commits)

#
# Get SYSMOD Projects
#
@app.route('/api/smProjects', methods=['POST'])
@handle_errors
def getSYSMODProjects():
    input_data = request.json
    print(f"/api/smProjects called with data: {input_data}")

    # Required inputs
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')

    if not server_url or not project_id or not commit_id:
        raise ValueError("Server_url, project_id, and commit_id are required.")
    # metadata_names = ['project']
    query_url = f"{server_url}/projects/{project_id}/query-results?commitId={commit_id}"
    # domainDefinitions = sysmod_api_helpers.get_metadata_ids_by_name(query_url, metadata_names)
    # domainAnnotatedElementsIDs = sysmod_api_helpers.get_metadatausage_annotatedElement_ids(query_url, domainDefinitions)
    # print(f"domainAnnotatedElementsIDs: {domainAnnotatedElementsIDs}")
    # query_url = f"{server_url}/projects/{project_id}/commits/{commit_id}"
    # project_elements = sysmod_api_helpers.get_elements_fromAPI(query_url, domainAnnotatedElementsIDs.get('project', []))

    occurrences = sysmod_api_helpers.get_elements_byKind_fromAPI(server_url, project_id, commit_id, 'OccurrenceDefinition')
    project_elements = sysmod_api_helpers.find_elements_specializing(query_url, occurrences, 'Project', element_kind=None)
    
    # Return simplified list with only declaredName (mapped to name) and @id
    simplified_projects = [{'name': p.get('declaredName'), '@id': p.get('@id')} for p in project_elements]
    
    return jsonify(simplified_projects)

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
    element = sysmod_api_helpers.get_element_fromAPI(query_url, element_id)
    
    return jsonify(element)

#
# Get Problem Statement
#
@app.route('/api/problem-statement', methods=['POST'])
@handle_errors
def api_problem_statement():
    input_data = request.json
    print(f"/api/problem-statement called with data: {input_data}")

    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id') # This is the project element ID

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("server_url, project_id, commit_id, and sysmod_project_id are required.")

    problem_stmt = sysmod_api_helpers.get_problem_statement(server_url, project_id, commit_id, sysmod_project_id)
    
    return jsonify(problem_stmt)

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
def api_brownfield_context():
    input_data = request.json
    server_url = input_data.get('server_url')
    project_id = input_data.get('project_id')
    commit_id = input_data.get('commit_id')
    sysmod_project_id = input_data.get('sysmod_project_id')
    context_type = input_data.get('context_type')

    print(f"/api/sysmod-context called with data: {input_data}")

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("Required parameters missing.")

    brownfield_context = sysmod_api_helpers.get_context(server_url, project_id, commit_id, sysmod_project_id, context_type)
    return jsonify(brownfield_context)

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

    stakeholders = sysmod_api_helpers.get_stakeholders(server_url, project_id, commit_id, sysmod_project_id)
    return jsonify(stakeholders)

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
    sysmod_project_id = input_data.get('sysmod_project_id')

    if not all([server_url, project_id, commit_id, sysmod_project_id]):
        raise ValueError("Required parameters missing.")

    bindings = sysmod_api_helpers.get_feature_bindings(server_url, project_id, commit_id, sysmod_project_id)
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
    
    # Check if a binding already exists
    # For efficiency we might want the caller to tell us the existing ID if known,
    # but to be safe we can check the bindings.
    # However, get_feature_bindings is expensive.
    
    # Simplified approach:
    # 1. Fetch current bindings (yes, expensive but safe for prototype)
    # 2. Look for matching client/supplier pair
    # 3. If found -> Delete
    # 4. If not found -> Create
    
    current_bindings = sysmod_api_helpers.get_feature_bindings(server_url, project_id, commit_id, None) # sysmod_project_id not strictly needed for matching
    
    existing_binding = next((b for b in current_bindings if b.get('client', {}).get('id') == client_id and b.get('supplier', {}).get('id') == supplier_id), None)
    
    if existing_binding:
        # Delete
        success = sysmod_api_helpers.delete_feature_binding(server_url, project_id, commit_id, existing_binding['id'])
        return jsonify({"action": "deleted", "success": success})
    else:
        # Create
        new_id = sysmod_api_helpers.create_feature_binding(server_url, project_id, commit_id, client_id, supplier_id)
        return jsonify({"action": "created", "id": new_id, "success": True if new_id else False})


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
    
    if not all([server_url, project_id, commit_id]):
        raise ValueError("Required parameters missing.")
        
    count = sysmod_api_helpers.load_model_cache(server_url, project_id, commit_id)
    return jsonify({"status": "success", "cached_elements": count})

if __name__ == '__main__':
    app.run(debug=True)

