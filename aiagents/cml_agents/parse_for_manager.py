import os
import json
import yaml
import jsonref

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle circular references."""
    def default(self, obj):
        # Handle specific types that may cause issues
        if isinstance(obj, dict):
            return {key: self.default(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.default(element) for element in obj]
        return super().default(obj)

def read_swagger_file(swagger_file_location):
    """
    Reads a Swagger file in JSON or YAML format and returns the parsed data.
    
    :param swagger_file_location: The path to the Swagger file
    :return: Parsed Swagger data as a Python dictionary
    """
    if swagger_file_location.endswith('.json'):
        with open(swagger_file_location, 'r') as file:
            return json.load(file)
    elif swagger_file_location.endswith('.yaml') or swagger_file_location.endswith('.yml'):
        with open(swagger_file_location, 'r') as file:
            return yaml.safe_load(file)
    else:
        raise ValueError(f"Unsupported file format: {swagger_file_location}")

def split_swagger_by_paths(swagger_data):
    """Split the Swagger file into chunks based on the API paths."""
    chunks = {}
    paths = swagger_data.get('paths', {})
    
    for path, methods in paths.items():
        chunk = {
            "path": path,
            "methods": methods  # Ensure 'methods' is directly taken as a dictionary
        }
        chunks[path] = chunk
    return chunks

def sanitize_file_name(name):
    """Sanitize the file name by replacing invalid characters."""
    return name.replace('/', '_').replace('\\', '_')

def swagger_parser(swagger_file_name: str, swagger_file_root: str, generated_folder_root: str):
    """
    Processes a single Swagger file, splits it into individual files based on paths,
    and stores them in a specified directory structure.
    This version is optimized for large Swagger files.
    """
    # Define the path to the swagger file and the output folder for chunks
    swagger_file_location = os.path.join(swagger_file_root, swagger_file_name)
    bucket_folder_name = swagger_file_name.split(".json")[0]

    # Read the Swagger file using the new read function
    swagger_data = read_swagger_file(swagger_file_location)

    # Create the output directory for the Swagger file chunks
    output_dir = os.path.join(generated_folder_root, bucket_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # Initialize metadata to map paths to files
    metadata = {}

    chunks = split_swagger_by_paths(swagger_data)

    # Write each path chunk into the respective JSON file in the correct folder
    for path, chunk in chunks.items():
        sanitized_key = sanitize_file_name(path)
        chunk_file_name = os.path.join(output_dir, f"{sanitized_key}.json")
        
        with open(chunk_file_name, 'w') as file:
            json.dump(chunk, file, cls=CustomJSONEncoder, indent=2)

        # Populate the metadata for mapping paths to chunk files
        methods_metadata = {}
        for method, details in chunk["methods"].items():
            if isinstance(details, dict):  # Check if details is a dictionary
                # Attempt to get a summary, falling back to description if not available
                summary = details.get("summary") or details.get("description", "")
            else:
                summary = ""  # If details is not a dictionary, set summary to empty
            
            methods_metadata[method] = summary

        metadata[path] = {
            "methods": methods_metadata,
            "file": chunk_file_name
        }

    # Write the metadata after processing all paths
    metadata_file_path = os.path.join(generated_folder_root, f"{bucket_folder_name}_metadata.json")
    with open(metadata_file_path, 'w') as f:
        json.dump(metadata, f, cls=CustomJSONEncoder, separators=(",", ":"))
    print(f"Written metadata to: {metadata_file_path}")
