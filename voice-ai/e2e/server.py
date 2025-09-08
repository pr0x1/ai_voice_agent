import os
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Create FastAPI app
app = FastAPI()

# Get API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    print("OPENAI_API_KEY environment variable is not set!")
    raise ValueError(
        "Please set OPENAI_API_KEY environment variable"
    )

# Get current directory for serving static files
current_dir = Path(__file__).parent

# Serve static files from current directory
app.mount("/static", StaticFiles(directory=current_dir), name="static")

# Also serve index.html at root
@app.get("/")
async def serve_index():
    from fastapi.responses import FileResponse
    return FileResponse(current_dir / "index.html")

session_config = {
    "session": {
        "type": "realtime",
        "model": "gpt-realtime",
        "audio": {
            "output": {
                "voice": "marin",
            },
        },
    },
}

# An endpoint which would work with the client code above - it returns
# the contents of a REST API request to this protected endpoint
@app.get("/token")
async def get_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/realtime/client_secrets",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=session_config,
        )

        # Check if request was successful
        response.raise_for_status()

        data = response.json()
        return data

if __name__ == "__main__":
    print("Server running on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)
