import asyncio
from api.config_manager import config_manager

async def list_agents():
    agents = await config_manager.get_all_agents()
    print([a.name for a in agents])

if __name__ == "__main__":
    asyncio.run(list_agents())
