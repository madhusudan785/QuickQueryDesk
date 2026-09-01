import asyncio
from app.rag.engine import retrieve_relevant_articles

async def main():
    sources = await retrieve_relevant_articles("VPN not connecting from home", top_k=3)
    print(f"Got {len(sources)} sources:")
    for s in sources:
        print(f"  - {s['title']} (score: {s['relevance_score']}, type: {type(s['relevance_score'])})")

asyncio.run(main())
