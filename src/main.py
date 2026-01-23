"""Payment gateway application with TCP and REST API."""

import asyncio
import logging
import os
import signal
import sys

from action.manager import Action
from api.manager import serve_api
from payment import Communication

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logging.getLogger('aiosqlite').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Global state for graceful shutdown
_shutdown_event: asyncio.Event | None = None
_tasks: set = set()


async def run_cat_server(comm: Communication) -> None:
    """Run the TCP server for CAT device communication."""
    try:
        server = await asyncio.start_server(comm.run, "0.0.0.0", 5000)
        logger.info("CAT server listening on 0.0.0.0:5000")
        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        logger.info("CAT server cancelled")
    except Exception as e:
        logger.error(f"CAT server error: {e}")
        raise


async def run_action_manager(comm: Communication) -> None:
    """Run the action manager for processing device events."""
    try:
        action_manager = Action(comm)
        await action_manager.run()
    except asyncio.CancelledError:
        logger.info("Action manager cancelled")
    except Exception as e:
        logger.error(f"Action manager error: {e}")
        raise


async def run_api_server(
    comm: Communication,
) -> None:
    """Run the FastAPI REST server."""
    try:
        host = os.getenv("API_HOST", "127.0.0.1")
        port = int(os.getenv("API_PORT", "8001"))
        
        await serve_api(
            comm=comm,
            host=host,
            port=port,
            log_level="info",
        )
    except asyncio.CancelledError:
        logger.info("API server cancelled")
    except Exception as e:
        logger.error(f"API server error: {e}")
        raise


async def graceful_shutdown(timeout_seconds: float = 30.0) -> None:
    """
    Gracefully shutdown all services.
    
    Cancels all tasks and waits for them to finish within timeout.
    """
    global _shutdown_event
    
    logger.info("Starting graceful shutdown...")
    
    if _shutdown_event:
        _shutdown_event.set()
    
    # Cancel all tasks
    logger.info(f"Cancelling {len(_tasks)} tasks")
    for task in _tasks:
        if not task.done():
            task.cancel()
    
    # Wait for all tasks to complete with timeout
    try:
        await asyncio.wait_for(
            asyncio.gather(*_tasks, return_exceptions=True),
            timeout=timeout_seconds,
        )
        logger.info("All tasks completed")
    except asyncio.TimeoutError:
        logger.warning(
            f"Shutdown timeout after {timeout_seconds}s, force-killing remaining tasks"
        )
        for task in _tasks:
            if not task.done():
                task.cancel()


def handle_shutdown_signal(signum: int, frame) -> None:
    """Handle SIGTERM and SIGINT signals."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown")
    
    # Create a task to handle shutdown
    if asyncio.get_event_loop().is_running():
        asyncio.create_task(graceful_shutdown())


async def main() -> None:
    """Main application entry point."""
    global _shutdown_event, _tasks
    
    logger.info("Starting Payment Gateway Application")
    
    # Initialize shutdown event
    _shutdown_event = asyncio.Event()
    
    # Setup signal handlers for graceful shutdown
    # for sig in (signal.SIGTERM, signal.SIGINT):
    #     asyncio.get_event_loop().add_signal_handler(
    #         sig,
    #         handle_shutdown_signal,
    #         sig,
    #         None,
    #     )
    
    # Create services
    comm = Communication()
    
    # Create and track tasks
    try:
        cat_task = asyncio.create_task(run_cat_server(comm))
        _tasks.add(cat_task)
        cat_task.add_done_callback(_tasks.discard)
        
        action_task = asyncio.create_task(run_action_manager(comm))
        _tasks.add(action_task)
        action_task.add_done_callback(_tasks.discard)
        
        api_task = asyncio.create_task(
            run_api_server(comm)
        )
        _tasks.add(api_task)
        api_task.add_done_callback(_tasks.discard)
        
        logger.info("All services started")
        
        # Wait for any task to fail
        await asyncio.gather(cat_task, action_task, api_task)
        
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await graceful_shutdown(1.0)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main(), debug=False)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
