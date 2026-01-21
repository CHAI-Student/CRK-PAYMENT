import asyncio
import logging
import sys

from datetime import datetime

from api.manager import serve_api
from payment import Communication


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

async def run_cat_server(comm: Communication):
    try:
        server = await asyncio.start_server(comm.run, "0.0.0.0", 5000)
        print("Server running on port 5000...")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")

async def run_api_server(comm: Communication):
    await serve_api(comm, host="127.0.0.1", port=8001, log_level="info")

async def main():
    comm = Communication()
    await asyncio.gather(
        run_cat_server(comm),
        run_api_server(comm),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main(), debug=True)
    except KeyboardInterrupt:
        print("\nExiting...")