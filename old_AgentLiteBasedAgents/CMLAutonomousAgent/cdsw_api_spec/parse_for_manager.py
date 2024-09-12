import json
import jsonref


def remove_unecessary_keys(dictionary, useless_keys):
    """
    since the original swagger contains a ton of unnecessary metadata occupying
    valuable character count, we remove those extra fields
    """
    if isinstance(dictionary, dict):
        for key, value in list(dictionary.items()):
            if key in useless_keys:
                del dictionary[key]
            else:
                remove_unecessary_keys(value, useless_keys)
    elif isinstance(dictionary, list):
        for item in dictionary:
            remove_unecessary_keys(item, useless_keys)


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


def swaggerParser():
    # import urllib.request

    # CDSW_ENDPOINT = ""
    # urllib.request.urlretrieve(
    #     f"{CDSW_ENDPOINT}/api/v2/swagger.json", "original_swagger.json"
    # )
    swagger = jsonref.load(
        open("original_swagger.json"), lazy_load=False, proxies=False, merge_props=True
    )
    # remove unnecessary ref definitions
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
    remove_unecessary_keys(swagger, useless_keys)

    buckets = bucketer(swagger)
    metadata = {}

    # we need a metadata file that will allow for direct mapping of paths to relevant json file
    for bucket_name, paths in buckets.items():
        # set the initial data for manager metadata along with where the files are being stored
        for path in paths:
            metadata[path] = {}
            metadata[path]["methods"] = {}
            metadata[path]["file"] = f"{bucket_name}.json"

            for method in paths[path]:
                metadata[path]["methods"][method] = paths[path][method]["summary"]

        # populate the individual json files with api information
        json.dump(
            paths,
            open(f"agent_categorised_json/{bucket_name}.json", "w"),
            separators=(",", ":"),
        )

    # create the manager metadata
    json.dump(metadata, open("manager_metadata.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    swaggerParser()
