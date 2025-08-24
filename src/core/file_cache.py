"""
File Cache System for Performance Optimization

This module provides:
- File caching for frequently accessed data
- Async file operations for non-critical writes
- Batch file operations instead of individual writes
- File change detection to avoid unnecessary reads
- Thread-safe operations
- Dedicated write queue for timer operations
"""

import os
import json
import time
import threading
import asyncio
from typing import Any, Dict, Optional, Callable
from pathlib import Path
from functools import lru_cache
import hashlib
from queue import Queue, Empty
from .logger import get_logger
import atexit

log = get_logger(__name__)

class FileCache:
	"""Thread-safe file cache with change detection and dedicated write queue"""
	
	def __init__(self, cache_ttl: int = 300, max_cache_size: int = 100):
		self._cache: Dict[str, Dict[str, Any]] = {}
		self._cache_timestamps: Dict[str, int] = {}
		self._file_hashes: Dict[str, str] = {}
		self._cache_ttl = cache_ttl
		self._max_cache_size = max_cache_size
		self._lock = threading.RLock()
		
		# Dedicated write queue for timer operations
		self._write_queue = Queue()
		self._write_thread = None
		self._shutdown_event = threading.Event()
		
		# Start dedicated write thread
		self._start_write_thread()

	def _start_write_thread(self):
		"""Start dedicated write thread for timer operations"""
		if self._write_thread is None or not self._write_thread.is_alive():
			self._write_thread = threading.Thread(target=self._write_worker, daemon=True)
			self._write_thread.start()

	def _write_worker(self):
		"""Dedicated worker thread for handling all file writes sequentially"""
		while not self._shutdown_event.is_set():
			try:
				# Process multiple writes in batch for efficiency
				tasks = []
				
				# Collect up to 10 writes or wait 100ms
				try:
					# Get first task
					task = self._write_queue.get(timeout=0.1)
					if task is None:  # Shutdown signal
						break
					tasks.append(task)
					
					# Collect additional tasks without blocking
					while len(tasks) < 10:
						try:
							task = self._write_queue.get_nowait()
							if task is None:  # Shutdown signal
								break
							tasks.append(task)
						except Empty:
							break
							
				except Empty:
					continue
				
				# Process all collected tasks
				for task in tasks:
					file_path, data, write_type = task
					if file_path is not None and data is not None:
						self._perform_write(file_path, data, write_type)
					self._write_queue.task_done()
				
			except Exception as e:
				log.error("write_worker_error", exc_info=True)

	def _perform_write(self, file_path: str, data: Dict[str, Any], write_type: str = "sync"):
		"""Perform the actual file write operation"""
		try:
			os.makedirs(os.path.dirname(file_path), exist_ok=True)
			
			# Fast atomic write for timer operations
			tmp_path = file_path + ".tmp"
			with open(tmp_path, 'w', encoding='utf-8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
			os.replace(tmp_path, file_path)
			
			# Update cache without lock for better performance
			self._cache[file_path] = data.copy()
			try:
				self._cache_timestamps[file_path] = os.stat(file_path).st_mtime_ns
			except Exception:
				self._cache_timestamps[file_path] = time.time_ns()
			self._file_hashes[file_path] = self._calculate_hash(data)
				
		except Exception:
			log.error("write_error", extra={"file_path": file_path}, exc_info=True)

	def _calculate_hash(self, data: Dict[str, Any]) -> str:
		"""Calculate hash of data for change detection"""
		data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
		return hashlib.md5(data_str.encode()).hexdigest()
	
	def _is_cache_valid(self, file_path: str) -> bool:
		"""Check if cached data is still valid"""
		if file_path not in self._cache_timestamps:
			return False
		
		age_sec = (time.time_ns() - self._cache_timestamps[file_path]) / 1_000_000_000
		return age_sec < self._cache_ttl
	
	def _is_file_changed(self, file_path: str) -> bool:
		"""Check if file has changed on disk using high-resolution mtime (ns)"""
		if file_path not in self._cache_timestamps:
			return True

		try:
			current_mtime_ns = os.stat(file_path).st_mtime_ns
			cached_mtime_ns = self._cache_timestamps.get(file_path, 0)
			return current_mtime_ns > cached_mtime_ns
		except Exception:
			return True

	def read_json(self, file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""Read JSON file with caching and change detection"""
		if default is None:
			default = {}

		with self._lock:
			# Check cache first
			if file_path in self._cache and self._is_cache_valid(file_path):
				# Verify file hasn't changed on disk
				if not self._is_file_changed(file_path):
					return self._cache[file_path].copy()

			# Read from disk
			try:
				if os.path.exists(file_path):
					with open(file_path, 'r', encoding='utf-8') as f:
						data = json.load(f)
					if not isinstance(data, dict):
						data = default.copy()
				else:
					data = default.copy()

				# Update cache with file modification time (ns)
				self._cache[file_path] = data.copy()
				if os.path.exists(file_path):
					try:
						self._cache_timestamps[file_path] = os.stat(file_path).st_mtime_ns
					except Exception:
						self._cache_timestamps[file_path] = time.time_ns()
				else:
					self._cache_timestamps[file_path] = time.time_ns()
				self._file_hashes[file_path] = self._calculate_hash(data)

				# Cleanup old cache entries
				self._cleanup_cache()

				return data

			except Exception:
				log.error("read_error", extra={"file_path": file_path}, exc_info=True)
				return default.copy()

	def write_json_async(self, file_path: str, data: Dict[str, Any]):
		"""Queue async JSON write for timer operations"""
		self._write_queue.put((file_path, data, "async"))
	
	def write_json_sync(self, file_path: str, data: Dict[str, Any]):
		"""Queue sync JSON write for timer operations"""
		self._write_queue.put((file_path, data, "sync"))
	
	def _cleanup_cache(self):
		"""Remove old cache entries"""
		if len(self._cache) <= self._max_cache_size:
			return
		
		# Remove oldest entries
		sorted_entries = sorted(
			self._cache_timestamps.items(), 
			key=lambda x: x[1]
		)
		
		entries_to_remove = len(self._cache) - self._max_cache_size
		for file_path, _ in sorted_entries[:entries_to_remove]:
			del self._cache[file_path]
			del self._cache_timestamps[file_path]
			del self._file_hashes[file_path]
	
	def invalidate_cache(self, file_path: Optional[str] = None):
		"""Invalidate cache for specific file or all files"""
		with self._lock:
			if file_path:
				self._cache.pop(file_path, None)
				self._cache_timestamps.pop(file_path, None)
				self._file_hashes.pop(file_path, None)
			else:
				self._cache.clear()
				self._cache_timestamps.clear()
				self._file_hashes.clear()

	def shutdown(self):
		"""Shutdown write thread and flush pending operations"""
		self._shutdown_event.set()
		
		# Send shutdown signal
		self._write_queue.put(None)
		
		# Wait for write thread to finish
		if self._write_thread and self._write_thread.is_alive():
			self._write_thread.join(timeout=5.0)


# Global file cache instance
_file_cache = FileCache()

# Ensure flush on interpreter exit
atexit.register(_file_cache.shutdown)

# Convenience functions
def read_json_cached(file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Read JSON file with caching"""
    return _file_cache.read_json(file_path, default)

def write_json_async(file_path: str, data: Dict[str, Any]):
    """Write JSON file asynchronously via queue"""
    _file_cache.write_json_async(file_path, data)

def write_json_sync(file_path: str, data: Dict[str, Any]):
    """Write JSON file synchronously via queue"""
    _file_cache.write_json_sync(file_path, data)

def batch_write_json(file_path: str, updates: Dict[str, Any]):
    """Queue batch JSON updates for timer operations"""
    # Read current data with minimal locking
    current_data = read_json_cached(file_path, {})
    
    # Merge updates properly - handle nested field structures
    for field_key, field_updates in updates.items():
        if isinstance(field_updates, dict):
            # If it's a field update (like field_1: {home_score: 5})
            if field_key not in current_data:
                current_data[field_key] = {}
            current_data[field_key].update(field_updates)
        else:
            # If it's a direct key-value update
            current_data[field_key] = field_updates
    
    # Queue the write operation
    write_json_sync(file_path, current_data)

def invalidate_file_cache(file_path: Optional[str] = None):
    """Invalidate file cache"""
    _file_cache.invalidate_cache(file_path)

def shutdown_file_cache():
    """Shutdown file cache system"""
    _file_cache.shutdown()
