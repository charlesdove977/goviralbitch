"""
Recon — Retry Logic with Exponential Backoff
Ported from ReelRecon.
"""

import time
import random
import functools
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Type, Any
from .logger import get_logger


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[Exception, int], None]] = None


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    delay = min(
        config.initial_delay * (config.exponential_base ** attempt),
        config.max_delay
    )
    if config.jitter:
        delay = delay * (0.5 + random.random())
    return delay


def retry_with_backoff(
    func: Optional[Callable] = None,
    *,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    category: str = "RETRY"
):
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
        on_retry=on_retry
    )

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return fn(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(category, f"Attempt {attempt + 1}/{config.max_attempts} failed, retrying in {delay:.1f}s", {
                            "function": fn.__name__,
                            "error": str(e),
                            "attempt": attempt + 1
                        })
                        if config.on_retry:
                            config.on_retry(e, attempt + 1)
                        time.sleep(delay)
                    else:
                        logger.error(category, f"All {config.max_attempts} attempts failed", {
                            "function": fn.__name__,
                            "final_error": str(e)
                        }, exception=e)

            raise last_exception

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


# Pre-configured retry decorators
network_retry = functools.partial(
    retry_with_backoff,
    max_attempts=3,
    initial_delay=1.0,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
    category="NETWORK"
)

api_retry = functools.partial(
    retry_with_backoff,
    max_attempts=3,
    initial_delay=2.0,
    max_delay=60.0,
    category="API"
)
