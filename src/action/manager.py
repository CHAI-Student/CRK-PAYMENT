import asyncio

from payment.manager import Communication

class ActionTask:
    def __init__(self, comm: Communication):
        self.comm = comm
        self.task: asyncio.Task | None = None