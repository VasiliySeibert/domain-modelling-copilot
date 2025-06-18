from openai import OpenAI
import json

def setup():
    api_key = input("Enter your OpenAI API key: ")
    client = OpenAI(api_key=api_key)
    return client

def prompt(scenario, client):
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": "You are an expert in extracting structured information from natural language text. \nGiven a text description, extract attributes, associations, generalizations, aggregations, and compositions.\n\n### Output Format:\n{\n  'attributes': [(Entity, Attribute)],\n  'associations': [(Entity1, Kard1, Kard2, Entity2, Relationship)],\n  'generalizations': [(Superclass, Subclass)],\n  'aggregations': [(Whole, Kard1, Part, Kard2)],\n  'compositions': [(Whole, Kard1, Part, Kard2)]\n}\n\n### Example 1:\n\n**Input Text:**\nThe manufacturer, CameraCorp, produces action cameras and supplies them to retailers. \nShipments are dispatched from the inventory and contain action cameras. \nCustomers like SarahAdventurer and ExtremeSportsClub receive shipments.\n\n**Expected Output:**\n{\n  'attributes': [('Manufacturer', 'name')],\n  'associations': [('Inventory', '1', '0..*', 'Shipment', 'dispatches'),\n                   ('Shipment', '1', '1', 'DistributionCenter', 'sent from'),\n                   ('DistributionCenter', '1', '0..*', 'Shipment', 'receives'),\n                   ('Shipment', '1', '1..*', 'ActionCamera', 'contains'),\n                   ('Customer', '1', '0..*', 'Shipment', 'receives')],\n  'generalizations': [('Customer', 'SarahAdventurer'),\n                      ('Customer', 'ExtremeSportsClub')],\n  'aggregations': [('Inventory', '1', 'ActionCamera', '*')],\n  'compositions': []\n}\n\n### Example 2:\n\n**Input Text:**\nThe supplier, GadgetMarket, provides components to manufacturers. \nManufacturers assemble action cameras using these components.\n\n**Expected Output:**\n{\n  'attributes': [('Supplier', 'name')],\n  'associations': [('Supplier', '0..*', '0..*', 'Component', 'provides'),\n                   ('Component', '0..*', '0..*', 'Manufacturer', 'supplied to'),\n                   ('Manufacturer', '1', '0..*', 'ActionCamera', 'assembles')],\n  'generalizations': [('Supplier', 'GadgetMarket')],\n  'aggregations': [('ActionCamera', '1', 'Component', '*')],\n  'compositions': []\n}\n\n\n"
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "In our action camera store, we specialize in cameras designed for adventurers and professionals seeking rugged and versatile solutions to capture their journeys. The inclusion of different models like ActionCamPro and AdventureCamX caters to a comprehensive range of activities and environments. These cameras come equipped with various high-quality components such as lenses, batteries, and mounts, which are critical to perform under extreme conditions.\r\n\r\nLenses are fundamental to our cameras; they handle different lighting and focus to deliver clear, high-quality images and videos. Batteries are essential for ensuring that our cameras can operate for extended periods, especially in remote locations where charging facilities might be sparse. Mounts, including ChestMounts and HelmetMounts, provide our customers with hands-free operation allowing them to concentrate on their activities while capturing moments seamlessly from different perspectives.\r\n\r\nEach action camera model and component is uniquely identified by names, descriptions, and IDs, which are essential for inventory management and simplifying the customer experience. Understanding these details helps in automating tasks such as stock check, categorization, and even recommendations based on the previous purchase history or customer preferences.\r\n\r\nIncluding these entities in the model is crucial not only for operational efficiency but also for emphasizing the customizability and adaptability of our products to various user needs. This detailed structuring ensures we can provide precise and quick services and product suggestions, enhancing overall customer satisfaction and streamlining their purchasing process."
            }
        ]
        },
        {
        "role": "assistant",
        "content": [
            {
            "type": "text",
            "text": "{\n  \"attributes\": [\n    {\n      \"entity\": \"ActionCamera\",\n      \"property\": \"name\"\n    },\n    {\n      \"entity\": \"ActionCamera\",\n      \"property\": \"description\"\n    },\n    {\n      \"entity\": \"ActionCamera\",\n      \"property\": \"ID\"\n    },\n    {\n      \"entity\": \"Component\",\n      \"property\": \"name\"\n    },\n    {\n      \"entity\": \"Component\",\n      \"property\": \"description\"\n    },\n    {\n      \"entity\": \"Component\",\n      \"property\": \"ID\"\n    }\n  ],\n  \"associations\": [\n    {\n      \"source\": \"Lenses\",\n      \"sourceMultiplicity\": \"1..*\",\n      \"targetMultiplicity\": \"1\",\n      \"target\": \"ActionCamera\",\n      \"relationship\": \"equipped with\"\n    },\n    {\n      \"source\": \"Batteries\",\n      \"sourceMultiplicity\": \"1..*\",\n      \"targetMultiplicity\": \"1\",\n      \"target\": \"ActionCamera\",\n      \"relationship\": \"equipped with\"\n    },\n    {\n      \"source\": \"Mounts\",\n      \"sourceMultiplicity\": \"1..*\",\n      \"targetMultiplicity\": \"1\",\n      \"target\": \"ActionCamera\",\n      \"relationship\": \"equipped with\"\n    }\n  ],\n  \"generalizations\": [\n    {\n      \"superclass\": \"ActionCamera\",\n      \"subclass\": \"ActionCamPro\"\n    },\n    {\n      \"superclass\": \"ActionCamera\",\n      \"subclass\": \"AdventureCamX\"\n    },\n    {\n      \"superclass\": \"Mount\",\n      \"subclass\": \"ChestMount\"\n    },\n    {\n      \"superclass\": \"Mount\",\n      \"subclass\": \"HelmetMount\"\n    }\n  ],\n  \"aggregations\": [\n    {\n      \"parent\": \"ActionCamera\",\n      \"parentMultiplicity\": \"1\",\n      \"child\": \"Component\",\n      \"childMultiplicity\": \"*\"\n    }\n  ],\n  \"compositions\": []\n}"
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": scenario}
        ]
        }
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
        "name": "camera_store_schema",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
            "attributes": {
                "type": "array",
                "description": "List of attributes for the entities.",
                "items": {
                "type": "object",
                "properties": {
                    "entity": {
                    "type": "string",
                    "description": "The name of the entity."
                    },
                    "property": {
                    "type": "string",
                    "description": "The property of the entity."
                    }
                },
                "required": [
                    "entity",
                    "property"
                ],
                "additionalProperties": False
                }
            },
            "associations": {
                "type": "array",
                "description": "List of associations between entities.",
                "items": {
                "type": "object",
                "properties": {
                    "source": {
                    "type": "string",
                    "description": "Source entity."
                    },
                    "sourceMultiplicity": {
                    "type": "string",
                    "description": "Multiplicity for the source entity."
                    },
                    "targetMultiplicity": {
                    "type": "string",
                    "description": "Multiplicity for the target entity."
                    },
                    "target": {
                    "type": "string",
                    "description": "Target entity."
                    },
                    "relationship": {
                    "type": "string",
                    "description": "Relationship type."
                    }
                },
                "required": [
                    "source",
                    "sourceMultiplicity",
                    "targetMultiplicity",
                    "target",
                    "relationship"
                ],
                "additionalProperties": False
                }
            },
            "generalizations": {
                "type": "array",
                "description": "List of generalizations of entities.",
                "items": {
                "type": "object",
                "properties": {
                    "superclass": {
                    "type": "string",
                    "description": "Superclass entity."
                    },
                    "subclass": {
                    "type": "string",
                    "description": "Subclass entity."
                    }
                },
                "required": [
                    "superclass",
                    "subclass"
                ],
                "additionalProperties": False
                }
            },
            "aggregations": {
                "type": "array",
                "description": "List of aggregations of entities.",
                "items": {
                "type": "object",
                "properties": {
                    "parent": {
                    "type": "string",
                    "description": "Parent entity."
                    },
                    "parentMultiplicity": {
                    "type": "string",
                    "description": "Multiplicity for the parent entity."
                    },
                    "child": {
                    "type": "string",
                    "description": "Child entity."
                    },
                    "childMultiplicity": {
                    "type": "string",
                    "description": "Multiplicity for the child entity."
                    }
                },
                "required": [
                    "parent",
                    "parentMultiplicity",
                    "child",
                    "childMultiplicity"
                ],
                "additionalProperties": False
                }
            },
            "compositions": {
                "type": "array",
                "description": "List of compositions of entities.",
                "items": {
                "type": "object",
                "properties": {
                    "parent": {
                    "type": "string",
                    "description": "Parent entity."
                    },
                    "child": {
                    "type": "string",
                    "description": "Child entity."
                    }
                },
                "required": [
                    "parent",
                    "child"
                ],
                "additionalProperties": False
                }
            }
            },
            "required": [
            "attributes",
            "associations",
            "generalizations",
            "aggregations",
            "compositions"
            ],
            "additionalProperties": False
        }
        }
    },
    temperature=1,
    max_completion_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    return response


def process_response(response):
    _response = response.choices[0].message.content
    data = json.loads(_response)
    return data

def convert_to_plantuml(data, response):
    try:
        uml_lines = ["@startuml", "left to right direction"]

        # Process Associations (Relationships)
        for assoc in data.get("associations", []):
            source = assoc["source"]
            target = assoc["target"]
            source_multiplicity = assoc["sourceMultiplicity"]
            target_multiplicity = assoc["targetMultiplicity"]
            relationship = assoc["relationship"]
            uml_lines.append(f'{source} "{source_multiplicity}" -- "{target_multiplicity}" {target} : {relationship}')

        # Process Generalizations (Inheritance)
        for gen in data.get("generalizations", []):
            superclass = gen["superclass"]
            subclass = gen["subclass"]
            uml_lines.append(f"{superclass} <|-- {subclass}")

        # Process Aggregations (Whole-Part)
        for agg in data.get("aggregations", []):
            parent = agg["parent"]
            child = agg["child"]
            parent_multiplicity = agg["parentMultiplicity"]
            child_multiplicity = agg["childMultiplicity"]
            uml_lines.append(f'{parent} "{parent_multiplicity}" o-- "{child_multiplicity}" {child}')

        # Process Compositions (Whole-Part, Strong Ownership)
        for comp in data.get("compositions", []):
            parent = comp["parent"]
            child = comp["child"]
            uml_lines.append(f'{parent} *-- {child}')

        # Process Attributes (Class Properties)
        attribute_dict = {}
        for attr in data.get("attributes", []):
            entity = attr["entity"]
            property_name = attr["property"]
            if entity not in attribute_dict:
                attribute_dict[entity] = []
            attribute_dict[entity].append(property_name)

        # Correctly format attributes under their respective entities
        for entity, attributes in attribute_dict.items():
            uml_lines.append("\n".join(f"{entity} : {attr}" for attr in attributes))

        uml_lines.append("@enduml")

        return "\n".join(uml_lines)
    except Exception as e:
        print(f"Error in converting to PlantUML: {e}")
        print(data)
        print(response)

import unicodedata

def remove_diacritics(text):
    """
    Remove diacritical marks from the input text, converting characters like 'é' to 'e'.
    
    Args:
        text (str): The input string to process.
    
    Returns:
        str: The string with diacritical marks removed.
    """
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def merge_tokens(segment):
    """
    Merge consecutive tokens into a single entity name (e.g., "Tech Savvy" becomes "TechSavvy"),
    except for quoted strings or UML relationship tokens. Remove hyphens, periods, commas, plus signs,
    and diacritical marks from entity name tokens.
    
    Args:
        segment (str): A segment of a PlantUML line to process.
    
    Returns:
        str: The processed segment with entity names merged and cleaned.
    """
    tokens = segment.split()
    special_tokens = {"--", "<|--", "o--", "*--"}
    merged_tokens = []
    buffer = []
    
    for token in tokens:
        if token.startswith('"') and token.endswith('"'):
            # Preserve quoted strings (e.g., cardinalities like "0..*")
            if buffer:
                merged_tokens.append(''.join(buffer))
                buffer = []
            merged_tokens.append(token)
        elif token in special_tokens:
            # Preserve special UML tokens (e.g., "--", "<|--", "*--")
            if buffer:
                merged_tokens.append(''.join(buffer))
                buffer = []
            merged_tokens.append(token)
        else:
            # Clean entity name token: remove hyphens, periods, commas, plus signs, and diacritics
            clean_token = remove_diacritics(token.replace('-', '').replace('.', '').replace(',', '').replace('+', ''))
            buffer.append(clean_token)
    if buffer:
        merged_tokens.append(''.join(buffer))
    return ' '.join(merged_tokens)

def post_process(text):
    """
    Process PlantUML text line by line:
    - For attribute lines (with ':' but no relationship operators), merge the entity name
      and simplify the attribute to the first word, replacing 'e-mail' with 'EMail'.
    - For relationship/inheritance lines, process the entity names and preserve labels.
    
    Args:
        text (str): The raw PlantUML text.
    
    Returns:
        str: The processed PlantUML text.
    """
    lines = text.splitlines()
    processed_lines = []
    relationship_ops = ["--", "<|--", "o--", "*--"]
    
    for line in lines:
        if (
            line.strip() == "" 
            or line.strip().startswith("@startuml") 
            or line.strip().startswith("@enduml")
            or line.strip() == "left to right direction"
        ):
            processed_lines.append(line)
            continue
        
        if ':' in line and not any(op in line for op in relationship_ops):
            left, right = line.split(":", 1)
            left_processed = merge_tokens(left)
            words = right.strip().split()
            if words:
                attr = words[0]
                if attr == "e-mail":
                    attr = "EMail"
            else:
                attr = ""
            processed_lines.append(left_processed + " : " + attr)
        else:
            if ':' in line:
                before, after = line.split(":", 1)
                before_processed = merge_tokens(before)
                processed_lines.append(before_processed + " : " + after.strip())
            else:
                processed_lines.append(merge_tokens(line))
                
    return "\n".join(processed_lines)

def gpt_v2_interface(scenario, client):
    response = prompt(scenario, client)
    data = process_response(response)
    plant_uml = convert_to_plantuml(data, response)
    plant_uml = post_process(plant_uml)
    return plant_uml
