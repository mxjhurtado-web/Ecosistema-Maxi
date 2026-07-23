import asyncio
import sys
import os

# Add api directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.shared_logic import detect_language

async def main():
    res1 = await detect_language("hola?¡")
    res2 = await detect_language("hola, buenas tardes")
    print("hola?¡ ->", res1)
    print("hola, buenas tardes ->", res2)

if __name__ == "__main__":
    asyncio.run(main())
