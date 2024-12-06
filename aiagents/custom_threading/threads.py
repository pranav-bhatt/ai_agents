import sys
import threading
import ctypes
import time
import traceback

class ThreadWithTrace(threading.Thread):
    """
    An enhanced thread class that provides more reliable termination mechanisms.
    
    Key Improvements:
    - Multiple termination strategies
    - Exception handling
    - Resource cleanup
    - Timeout support
    """
    
    def __init__(self, *args, timeout=None, **kwargs):
        """
        Initialize the thread with additional termination and monitoring capabilities.
        
        :param timeout: Optional timeout in seconds to forcibly stop the thread
        :param args: Positional arguments for thread initialization
        :param kwargs: Keyword arguments for thread initialization
        """
        super().__init__(*args, **kwargs)
        
        # Termination flags and controls
        self._is_running = threading.Event()
        self._terminate_flag = threading.Event()
        self._timeout = timeout
        
        # Store the original thread function
        self._original_target = self._target
        
        # Wrapper to manage thread lifecycle
        def wrapped_target(*args, **kwargs):
            self._is_running.set()
            try:
                if self._original_target:
                    self._original_target(*args, **kwargs)
            except Exception as e:
                print(f"Thread {self.name} encountered an error: {e}")
                traceback.print_exc()
            finally:
                self._is_running.clear()
        
        # Replace target with wrapped version
        self._target = wrapped_target

    def stop(self, timeout=None):
        """
        Gracefully stop the thread with optional timeout.
        
        :param timeout: Maximum time to wait for thread termination
        :return: True if thread stopped, False if timeout occurred
        """
        # Signal thread to terminate
        self._terminate_flag.set()
        
        # Wait for thread to finish or timeout
        if timeout is None:
            timeout = self._timeout
        
        try:
            if timeout:
                self.join(timeout)
                return not self.is_alive()
            else:
                self.join()
                return True
        except Exception as e:
            print(f"Error stopping thread: {e}")
            return False

    def force_stop(self):
        """
        Forcibly terminate the thread using low-level thread termination.
        Use with extreme caution as this can lead to resource leaks.
        """
        thread_id = self.ident
        print(f"The thread Id is {thread_id}")
        if not thread_id:
            return False

        try:
            # Use ctypes to inject an exception into the thread
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread_id), 
                ctypes.py_object(SystemExit)
            )
            print('Figuring out the thread type')
            if res > 1:
                # Cleanup if multiple exceptions were injected
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(thread_id), None
                )
                print('Caught an exception')
                return False
            print("No exception: Hence true")
            return True
        except Exception as e:
            print(f"Force stop failed: {e}")
            return False

    def is_running(self):
        """
        Check if the thread is currently running.
        
        :return: True if thread is active, False otherwise
        """
        return self._is_running.is_set()

    def should_terminate(self):
        """
        Check if the thread has been signaled to terminate.
        
        :return: True if termination is requested, False otherwise
        """
        return self._terminate_flag.is_set()
