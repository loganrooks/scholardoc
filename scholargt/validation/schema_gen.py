"""JSON Schema generation from ScholarGT Pydantic models.

Generates a JSON Schema document that validates both PageGT and DocumentGT files.
Uses pydantic.json_schema.models_json_schema() to produce a schema with all
model definitions, then enriches with metadata (title, version, $schema).

The generated schema is written to scholargt/generated/schema.json for use
by external validation tools (IDEs, CI pipelines, jsonschema CLI).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from scholargt.config.models import GTProfile
from scholargt.schema.document import DocumentGT
from scholargt.schema.page import PageGT
from scholargt.schema.version import SCHEMA_VERSION

# Default output path for the generated schema file
DEFAULT_SCHEMA_PATH = Path(__file__).parent.parent / "generated" / "schema.json"


def generate_schema() -> dict:
    """Generate JSON Schema from ScholarGT Pydantic models.

    Produces a schema covering PageGT, DocumentGT, and GTProfile models
    using Pydantic's 'validation' mode for maximum compatibility.

    Returns:
        A dict representing the full JSON Schema document with $defs
        containing all referenced model definitions.
    """
    _, schema = models_json_schema(
        [
            (PageGT, "validation"),
            (DocumentGT, "validation"),
            (GTProfile, "validation"),
        ],
        title="ScholarGT Schema",
    )

    # Add JSON Schema draft version and ScholarGT version
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["version"] = SCHEMA_VERSION

    return schema


def write_schema(output_path: Path | None = None) -> Path:
    """Generate and write JSON Schema to a file.

    Args:
        output_path: Where to write the schema. Defaults to
            scholargt/generated/schema.json.

    Returns:
        The path the schema was written to.
    """
    path = output_path or DEFAULT_SCHEMA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    schema = generate_schema()
    path.write_text(json.dumps(schema, indent=2) + "\n")

    return path
