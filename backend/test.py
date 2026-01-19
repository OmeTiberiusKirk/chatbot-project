import multiprocessing
import time
import os
import random

# Function that workers in the pool will execute


def worker_task(task_queue):
    """Processes items from the queue until a sentinel value (e.g., None) is found."""
    # A pool worker can access the shared queue via the argument
    try:
        item = task_queue.get()
        # Simulate some work
        time.sleep(random.randint(1, 3))
        result = f"Process {os.getpid()} finished task: {item}"
        return result
    except Exception as e:
        return f"Error processing task: {e}"


if __name__ == '__main__':
    # 1. Create a Manager to host shared objects
    with multiprocessing.Manager() as manager:
        # Create a shared queue via the Manager
        shared_queue = manager.Queue()

        # 2. Add tasks to the queue
        tasks = range(5)
        for task in tasks:
            shared_queue.put(task)

        # 3. Create a Pool
        # Note: We don't pass the queue directly to the Pool constructor in this approach;
        # instead, we pass it as an argument to the target function for each async task.
        with multiprocessing.Pool(processes=3) as pool:
            # Submit tasks to the pool, passing the shared queue to each call
            # apply_async is used to get results back individually
            results = [pool.apply_async(
                worker_task, args=(shared_queue,)) for _ in tasks]

            # 4. Collect results from the async tasks
            for async_result in results:
                # .get() blocks until the task is done
                print(async_result.get())

        print("All tasks finished and pool closed.")
