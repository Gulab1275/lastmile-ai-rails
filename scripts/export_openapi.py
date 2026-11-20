"""
Exports OpenAPI JSON specification from the FastAPI app.
Enables Gulab to generate the Next.js TypeScript SDK client immediately without waiting for a deployed backend.
"""
import json
import os
import sys

# Ensure repository root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.api.main import app


def export_openapi():
    os.makedirs("docs", exist_ok=True)
    schema = app.openapi()
    output_path = os.path.join("docs", "openapi.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"Exported OpenAPI spec to: {output_path}")
    print(f"Total endpoints documented: {len(schema.get('paths', {}))}")


if __name__ == "__main__":
    export_openapi()
