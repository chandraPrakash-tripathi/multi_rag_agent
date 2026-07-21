import os
import serpapi
from dotenv import load_dotenv

# This finds your .env file and loads its variables into Python's os environment
load_dotenv()

# Now os.getenv will successfully find the key
client = serpapi.Client(api_key=os.getenv("SERPAPI_KEY"))

# Run the search
results = client.search(
    {"engine": "google", "q": "Python programming tutorials", "num": 5}
)

# Parse the JSON response
for i, result in enumerate(results.get("organic_results", []), 1):
    title = result.get("title")
    link = result.get("link")
    print(f"{i}. {title}\n   {link}\n")
