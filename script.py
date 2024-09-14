from pyvis.network import Network
import networkx as nx
import os
import ast


# Define the root directory for the project
root_dir = "Loop-Labyrinth-Analysis"

# Function to extract imports (both modules and functions) from a file
def extract_imports(file_path):
    with open(file_path, "r") as file:
        try:
            tree = ast.parse(file.read(), filename=file_path)
        except SyntaxError:
            return [], []

    module_imports = []
    function_imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if node.names:
                for alias in node.names:
                    function_imports.append((module_name, alias.name))
    
    return module_imports, function_imports

# Walk through the directories and parse the files
def gather_imports(root_dir):
    imports_map = {}
    function_imports_map = {}
    
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py") and "__pycache__" not in subdir:
                file_path = os.path.join(subdir, file)
                file_key = os.path.relpath(file_path, root_dir).replace("\\", "/")  # Handle path separators for all OS
                module_imports, function_imports = extract_imports(file_path)
                imports_map[file_key] = module_imports
                function_imports_map[file_key] = function_imports
    
    return imports_map, function_imports_map

# Link the imports to the actual Python files
def resolve_imports(imports_map, function_imports_map):
    resolved_imports = {}
    resolved_function_imports = {}
    
    # Resolve module imports
    for file, imports in imports_map.items():
        resolved_imports[file] = []
        for imp in imports:
            # Try to map imports to actual files in the project
            for other_file in imports_map:
                if other_file.endswith(f"{imp.replace('.', '/')}.py"):  # Handle import as a path
                    resolved_imports[file].append(other_file)
    
    # Resolve function imports
    for file, functions in function_imports_map.items():
        resolved_function_imports[file] = []
        for module_name, function_name in functions:
            # Try to map functions to the files that define them
            for other_file in imports_map:
                if other_file.endswith(f"{module_name.replace('.', '/')}.py"):
                    resolved_function_imports[file].append((other_file, function_name))
    
    return resolved_imports, resolved_function_imports

# Create a graph of imports
def create_import_graph(resolved_imports, resolved_function_imports):
    graph = nx.DiGraph()  # Directed graph
    
    # Add module imports (file to file)
    for file, imported_files in resolved_imports.items():
        for imported_file in imported_files:
            graph.add_edge(file, imported_file, type='module')
    
    # Add function imports (file to file with function labels)
    for file, imported_functions in resolved_function_imports.items():
        for imported_file, function_name in imported_functions:
            graph.add_edge(file, imported_file, type='function', function=function_name)
    
    return graph

# Visualize the graph using PyVis
def visualize_graph_pyvis(graph):
    net = Network(height="750px", width="100%", directed=True)
    
    # Add nodes
    for node in graph.nodes():
        net.add_node(node, label=node, color="skyblue", title=node)
    
    # Add edges with labels for functions
    for edge in graph.edges(data=True):
        if edge[2]['type'] == 'function':
            function_name = edge[2]['function']
            net.add_edge(edge[0], edge[1], title=function_name, color='red', label=function_name)
        else:
            net.add_edge(edge[0], edge[1], color='gray')
    
    # Write the graph to an HTML file
    net.write_html("import_graph.html")  # Use write_html instead of show()


# Run the process
imports_map, function_imports_map = gather_imports(root_dir)
resolved_imports, resolved_function_imports = resolve_imports(imports_map, function_imports_map)
graph = create_import_graph(resolved_imports, resolved_function_imports)
visualize_graph_pyvis(graph)
