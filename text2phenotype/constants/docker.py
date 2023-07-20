"""
This file holds onto constants related to Docker interaction with code.
"""

MDL_SIGTERM = 30  # Re-write of SIGTERM (15) to 30 for use in workers without
# interference from multiprocessing or subprocesses in Python
