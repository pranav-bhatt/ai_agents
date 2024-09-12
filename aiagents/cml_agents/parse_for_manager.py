import os
import json
import jsonref


def remove_unnecessary_keys(dictionary, useless_keys):
    """
    since the original swagger contains a ton of unnecessary metadata occupying
    valuable character count, we remove those extra fields
    """
    if isinstance(dictionary, dict):
        for key, value in list(dictionary.items()):
            if key in useless_keys:
                del dictionary[key]
            else:
                remove_unnecessary_keys(value, useless_keys)
    elif isinstance(dictionary, list):
        for item in dictionary:
            remove_unnecessary_keys(item, useless_keys)


def bucketer(swagger, threshold=2):
    """
    The following code buckets the paths in the swagger specification by path segment
    in order to have small json files that can be easily consumed
    """
    buckets = {}
    for path, methods in swagger["paths"].items():
        path_parts = path.split("/")
        path_parts = [
            s.split(":", 1)[0].lstrip("{").rstrip("}")
            + (":" + s.split(":", 1)[1] if ":" in s else "")
            for s in path_parts
        ]

        bucket_name = (
            "_".join(path_parts[3 : 3 + threshold])
            if len(path_parts) > 3
            else path_parts[3]
        )
        while bucket_name in buckets and len(buckets[bucket_name]) >= threshold:
            threshold += 1
            bucket_name = (
                "_".join(path_parts[3 : 3 + threshold])
                if len(path_parts) > 3
                else path_parts[3]
            )

        if bucket_name not in buckets:
            buckets[bucket_name] = {}

        buckets[bucket_name][path] = methods
    return buckets


def swagger_parser(
    swagger_file_name: str,
    swagger_file_root: str,
    generated_folder_root: str,
):
    swagger_file_location = os.path.join(swagger_file_root, swagger_file_name)
    bucket_folder_name = swagger_file_name.split(".json")[0]

    swagger = jsonref.load(
        open(swagger_file_location), lazy_load=False, proxies=False, merge_props=True
    )
    # remove unnecessary ref definitions
    if "definitions" in swagger:
        del swagger["definitions"]

    useless_keys = [
        "type",
        "in",
        "readOnly",
        "format",
        "responses",
        "operationId",
        "tags",
    ]
    remove_unnecessary_keys(swagger, useless_keys)

    buckets = bucketer(swagger)
    metadata = {}

    os.makedirs(
        os.path.join(generated_folder_root, bucket_folder_name),
        exist_ok=True,
    )

    # we need a metadata file that will allow for direct mapping of paths to relevant json file
    for bucket_name, paths in buckets.items():
        # set the initial data for manager metadata along with where the files are being stored
        for path in paths:
            metadata[path] = {}
            metadata[path]["methods"] = {}
            metadata[path][
                "file"
            ] = f"{generated_folder_root}/{bucket_folder_name}/{bucket_name}.json"

            for method in paths[path]:
                metadata[path]["methods"][method] = paths[path][method]["summary"]

        # populate the individual json files with api information
        json.dump(
            paths,
            open(
                os.path.join(
                    generated_folder_root,
                    bucket_folder_name,
                    f"{bucket_name}.json",
                ),
                "w",
            ),
            separators=(",", ":"),
        )

    # create the manager metadata
    json.dump(
        metadata,
        open(
            os.path.join(
                generated_folder_root,
                f"{bucket_folder_name}_metadata.json",
            ),
            "w",
        ),
        separators=(",", ":"),
    )
