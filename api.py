from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import parser
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load schema and prompt once at startup
SCHEMA_FILE = "api_schema.json"
if not os.path.exists(SCHEMA_FILE):
    raise RuntimeError(f"Schema file {SCHEMA_FILE} not found")

schema = parser.load_schema(SCHEMA_FILE)
system_prompt = parser.construct_prompt(schema)

class ParseRequest(BaseModel):
    description: str

@app.post("/parse")
async def parse_product(request: ParseRequest):
    if not request.description:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    
    print(f"Parsing description: {request.description[:50]}...")
    try:
        result = parser.parse_description(request.description, system_prompt, schema)
        if not result:
             raise HTTPException(status_code=500, detail="Failed to parse description")
        
        # Try to fetch an image
        if "product_name" in result:
                try:
                    from ddgs import DDGS
                    # Retry logic for rate limits
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            with DDGS() as ddgs:
                                keywords = result["product_name"]
                                # Search for images
                                images = list(ddgs.images(keywords, max_results=1))
                                if images:
                                    result["image_url"] = images[0]["image"]
                                    break
                        except Exception as inner_e:
                            print(f"Image search attempt {attempt+1} failed: {inner_e}")
                            if attempt < max_retries - 1:
                                import time
                                time.sleep(2) # Wait before retrying
                            else:
                                raise inner_e

                except Exception as e:
                    print(f"Image search failed after retries: {e}")

        return result
    except Exception as e:
        print(f"Error parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema():
    return schema

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
