# Python asyncio Primer

## The event loop
asyncio runs a single-threaded event loop. Coroutines defined with `async def` are scheduled on the loop, and `await` yields control back to it while waiting for I/O. This is cooperative multitasking: a coroutine that never awaits blocks everything else.

## Async generators
An async generator is an `async def` function that uses `yield`. Consumers iterate it with `async for`. This is the idiomatic way to stream data, such as tokens from an LLM, without buffering the whole response.

## Running blocking code
CPU-bound or blocking calls should be moved off the loop using `asyncio.to_thread()` or a process pool. Calling `time.sleep()` inside a coroutine freezes the loop; use `await asyncio.sleep()` instead.

## Type hints
Type hints are not enforced at runtime by Python itself. Tools like mypy check them statically, while Pydantic uses them to validate data at runtime.

## Packaging
The `uv` tool manages virtual environments, dependencies and lockfiles. `uv add` updates `pyproject.toml` and `uv.lock`, and `uv run` executes commands inside the project environment.
