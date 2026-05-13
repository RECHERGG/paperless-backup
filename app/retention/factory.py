"""
Retention policy factory.

Maps strategy names from config to concrete RetentionPolicy instances.
Adding a new strategy means: implement the class, register it here.
"""

import logging

from app.config.typed import RetentionConfig
from app.retention.base import RetentionPolicy
from app.retention.policy.gfs import GFSRetentionPolicy
from app.retention.policy.simple import SimpleRetentionPolicy
from app.retention.policy.time_based import TimeBasedRetentionPolicy
from app.retention.policy.daily import DailyRetentionPolicy
from app.retention.policy.none import NoRetentionPolicy

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[RetentionPolicy]] = {
    "gfs": GFSRetentionPolicy,
    "simple": SimpleRetentionPolicy,
    "time": TimeBasedRetentionPolicy,
    "daily": DailyRetentionPolicy,
    "none": NoRetentionPolicy,
}


def get_policy(config: RetentionConfig) -> RetentionPolicy:
    """
    Instantiate the correct retention policy from configuration.

    Args:
        config: Typed retention configuration.

    Returns:
        Configuraed RetentionPolicy instance.

    Raises:
        ValueError: If the strategy name is unknown.
    """
    strategy = config.strategy.lower()

    if strategy not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(
            f"Unknown retention strategy '{strategy}'.Available: {available}"
        )

    logger.info("Using retention strategy: '%s'", strategy)

    if strategy == "gfs":
        return GFSRetentionPolicy(
            hourly=config.hourly,
            daily=config.daily,
            weekly=config.weekly,
            monthly=config.monthly,
        )

    if strategy == "simple":
        return SimpleRetentionPolicy(keep_last=config.keep_last)

    if strategy == "time":
        return TimeBasedRetentionPolicy(
            max_age_days=config.max_age_days,
            minimum_keep=config.minimum_keep,
        )

    if strategy == "daily":
        return DailyRetentionPolicy(
            keep_days=config.keep_days,
            minimum_keep=config.minimum_keep,
        )

    if strategy == "none":
        return NoRetentionPolicy()

    # Unreachable - registry check above catches unkowns
    raise ValueError(f"Unhandled strategy: {strategy}")
