# utils/api_utils.py
import requests
from loguru import logger

class APIUtils:
    @staticmethod
    def get(url, headers=None, params=None):
        logger.info(f"GET {url} | params={params}")
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"Response: {response.status_code}")
        return response

    @staticmethod
    def post(url, headers=None, data=None, json=None):
        logger.info(f"POST {url} | data={data} | json={json}")
        response = requests.post(url, headers=headers, data=data, json=json)
        logger.info(f"Response: {response.status_code}")
        return response

    @staticmethod
    def put(url, headers=None, data=None, json=None):
        logger.info(f"PUT {url} | data={data} | json={json}")
        response = requests.put(url, headers=headers, data=data, json=json)
        logger.info(f"Response: {response.status_code}")
        return response

    @staticmethod
    def delete(url, headers=None):
        logger.info(f"DELETE {url}")
        response = requests.delete(url, headers=headers)
        logger.info(f"Response: {response.status_code}")
        return response
