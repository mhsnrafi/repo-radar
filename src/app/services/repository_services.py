import functools

import redis
import httpx
import hashlib
import json
from fastapi import APIRouter, Request

from app.core.config import REDIS_HOST, REDIS_PASSWORD
from typing import Optional
from tenacity import retry, wait_exponential, stop_after_attempt
from fastapi import HTTPException
from app.core.limiter import limiter

# initialize routes
router = APIRouter()

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, db=0, password=REDIS_PASSWORD)

# GitHub API base URL
GITHUB_API_BASE_URL = "https://api.github.com"


def get_cache_key(func_name: str, request: Request):
    """Generates a unique cache key for a function and a request.

    Args:
        func_name (str): The name of the function.
        request (Request): The HTTP request.

    Returns:
        str: The cache key.
    """
    request_data = {
        "path": request.url.path,
        "query_params": dict(request.query_params),
    }
    serialized_data = json.dumps((func_name, request_data))
    return hashlib.sha256(serialized_data.encode()).hexdigest()


def cacheable(ttl=60):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            cache_key = get_cache_key(func.__name__, request)
            cached_result = redis_client.get(cache_key)

            if cached_result is not None:
                try:
                    return json.loads(cached_result)
                except (TypeError, ValueError):
                    raise HTTPException(status_code=500, detail="Cache deserialization error")

            result = await func(request, *args, **kwargs)  # add request here

            try:
                redis_client.set(cache_key, json.dumps(result), ex=ttl)
            except (TypeError, OverflowError):
                raise HTTPException(status_code=500, detail="Cache serialization error")

            return result

        return wrapper

    return decorator


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def resilient_request(endpoint: str, params: dict):
    """Handles resilient HTTP requests with retries.

    Args:
        endpoint (str): API endpoint, relative to the base URL.
        params (dict): Parameters for the request.

    Raises:
        Exception: If the status code of the response is not 200.

    Returns:
        dict: JSON response.
    """
    url = f"{GITHUB_API_BASE_URL}/{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    if response.status_code != 200:
        raise Exception("API request failed")
    return response.json()


def prepare_params(query: str, per_page: int):
    """Prepares the parameters for a GitHub API request.

    Args:
        query (str): Query string.
        per_page (int): Number of top repositories.

    Raises:
        TypeError: If input arguments are not of the expected types.

    Returns:
        dict: The prepared parameters.
    """
    if not isinstance(query, str) or not isinstance(per_page, int):
        raise TypeError("Invalid argument type")

    return {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }


@router.get("/popular/{top_n}")
@limiter.limit("10/minute")
@cacheable(ttl=300)
async def get_top_repositories(request: Request, top_n: int):
    """Fetches the top repositories.

    Args:
        top_n (int): The number of top repositories to fetch.

    Returns:
        list: The list of top repositories.
        :param request:
        :param top_n:
        :param _:
    """
    endpoint = "search/repositories"
    query = "stars:>=1"
    params = prepare_params(query, top_n)
    data = await resilient_request(endpoint, params)
    return data["items"]


@router.get("/popular")
@cacheable(ttl=120)
@limiter.limit("10/minute")
async def get_repositories_since(request: Request, since_date: str, language: Optional[str] = None,
                                 top_n: Optional[int] = 100):
    """Fetches the most popular repositories created since a specified date, optionally filtered by language and limited by number.

    Args:
        since_date (str): The starting date.
        language (Optional[str]): The language of the repositories. Default is None, which means all languages.
        top_n (Optional[int]): The number of top repositories to fetch. Default is 100.

    Returns:
        list: The list of repositories.
        :param request:
    """
    endpoint = "search/repositories"
    query = f"created:>{since_date}"
    if language:
        query += f" language:{language}"
    params = prepare_params(query, top_n)
    data = await resilient_request(endpoint, params)
    return data["items"]
