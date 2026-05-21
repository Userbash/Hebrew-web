import os
import httpx
import asyncio
from dotenv import load_dotenv

async def test():
    load_dotenv()
    api_key = os.getenv('DEEPSEEK_API_KEY')
    print(f"Key starts with: {api_key[:10]}...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                'https://api.deepseek.com/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': 'hi'}], 'stream': False},
                timeout=10.0
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
