
"""
Advanced Test Data Management Utilities
 - Supports loading data from CSV, JSON, Excel
 - Provides random and dynamic data generation
 - Cleans up test data after execution
"""

import csv
import json
import random
import string
import os

class DataLoader:
	@staticmethod
	def load_csv(file_path):
		with open(file_path, newline='', encoding='utf-8') as csvfile:
			reader = csv.DictReader(csvfile)
			return [row for row in reader]

	@staticmethod
	def load_json(file_path):
		with open(file_path, encoding='utf-8') as jsonfile:
			return json.load(jsonfile)

	@staticmethod
	def generate_random_string(length=8):
		return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

	@staticmethod
	def generate_random_email():
		return f"user_{DataLoader.generate_random_string(6)}@example.com"

	@staticmethod
	def cleanup_temp_files(folder):
		for filename in os.listdir(folder):
			if filename.startswith('temp_'):
				os.remove(os.path.join(folder, filename))
