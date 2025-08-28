"""HTTP client utilities with retry logic and rate limiting."""

import time
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from config.settings import settings
from .logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """HTTP client with retry logic and rate limiting."""
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with retry strategy."""
        retry_strategy = Retry(
            total=settings.api.max_retries,
            backoff_factor=settings.api.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Termometro-Tecnologia/0.1.0 (+https://github.com/lucianfialho/tecdata)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
        })
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = settings.collection.min_request_interval
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """Make GET request with rate limiting and error handling."""
        
        self._apply_rate_limit()
        
        timeout = timeout or settings.api.request_timeout
        
        try:
            logger.debug(f"Making GET request to: {url}")
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout
            )
            
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make GET request and return JSON response."""
        
        response = self.get(url, params, headers, timeout)
        
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response.text[:500]}...")
            raise
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()