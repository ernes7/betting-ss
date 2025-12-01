"""Configuration loader for YAML-based settings.

Loads configuration from YAML files and provides typed access.
Supports environment variable overrides and default values.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from shared.scraping.scraper_config import ScraperConfig, RateLimitConfig


@dataclass
class ClaudeAPIConfig:
    """Claude API configuration."""
    model: str
    temperature: float
    max_tokens: int
    input_cost_per_mtok: float
    output_cost_per_mtok: float


@dataclass
class LoggingConfig:
    """Logging configuration."""
    directory: str
    format: str
    date_format: str
    max_bytes: int
    backup_count: int
    level: str


@dataclass
class ErrorConfig:
    """Error handling configuration."""
    output_file: str
    include_traceback: bool


class ConfigLoader:
    """Loads and manages application configuration from YAML files.

    Example:
        config = ConfigLoader()
        scraper_config = config.get_scraper_config("odds")
        api_config = config.get_api_config()
    """

    _instance: Optional["ConfigLoader"] = None
    _config: Dict[str, Any] = {}
    _urls: Dict[str, Any] = {}

    def __new__(cls):
        """Singleton pattern to ensure config is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from YAML files."""
        config_dir = Path("config")

        # Load main settings
        settings_path = config_dir / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, "r") as f:
                self._config = yaml.safe_load(f) or {}

        # Load URLs
        urls_path = config_dir / "urls.yaml"
        if urls_path.exists():
            with open(urls_path, "r") as f:
                self._urls = yaml.safe_load(f) or {}

    def reload(self) -> None:
        """Reload configuration from disk."""
        self._load_config()

    def get_scraper_config(self, service: str) -> ScraperConfig:
        """Get scraper configuration for a specific service.

        Args:
            service: Service name (odds, results, prediction)

        Returns:
            ScraperConfig with service-specific settings
        """
        scraping = self._config.get("scraping", {})
        service_config = scraping.get(service, {})

        return ScraperConfig(
            interval_seconds=service_config.get("interval_seconds", 5.0),
            timeout_ms=service_config.get("timeout_ms", 30000),
            max_retries=service_config.get("max_retries", 3),
            retry_delay_seconds=service_config.get("retry_delay_seconds", 2.0),
            headless=service_config.get("headless", True),
            wait_time_ms=service_config.get("wait_time_ms", 1000),
        )

    def get_rate_limit_config(self, source: str) -> RateLimitConfig:
        """Get rate limit configuration for a specific source.

        Args:
            source: Source name (sports_reference, draftkings)

        Returns:
            RateLimitConfig with source-specific settings
        """
        rate_limits = self._config.get("scraping", {}).get("rate_limits", {})
        source_config = rate_limits.get(source, {})

        return RateLimitConfig(
            calls=source_config.get("calls", 1),
            period_seconds=source_config.get("period_seconds", 5.0),
        )

    def get_api_config(self) -> ClaudeAPIConfig:
        """Get Claude API configuration.

        Environment variable ANTHROPIC_API_KEY should be set separately.

        Returns:
            ClaudeAPIConfig with API settings
        """
        api = self._config.get("api", {}).get("claude", {})

        return ClaudeAPIConfig(
            model=api.get("model", "claude-sonnet-4-5-20250929"),
            temperature=api.get("temperature", 0.7),
            max_tokens=api.get("max_tokens", 16000),
            input_cost_per_mtok=api.get("input_cost_per_mtok", 3.0),
            output_cost_per_mtok=api.get("output_cost_per_mtok", 15.0),
        )

    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration.

        Returns:
            LoggingConfig with logging settings
        """
        logging = self._config.get("logging", {})

        return LoggingConfig(
            directory=logging.get("directory", "logs"),
            format=logging.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            date_format=logging.get("date_format", "%Y-%m-%d %H:%M:%S"),
            max_bytes=logging.get("max_bytes", 10485760),
            backup_count=logging.get("backup_count", 5),
            level=logging.get("level", "INFO"),
        )

    def get_error_config(self) -> ErrorConfig:
        """Get error handling configuration.

        Returns:
            ErrorConfig with error handling settings
        """
        errors = self._config.get("errors", {})

        return ErrorConfig(
            output_file=errors.get("output_file", "errors.json"),
            include_traceback=errors.get("include_traceback", True),
        )

    def get_data_path(self, path_type: str, **kwargs) -> Path:
        """Get data path with variable substitution.

        Args:
            path_type: Type of path (odds, predictions, results, etc.)
            **kwargs: Variables for substitution (sport, date, team, etc.)

        Returns:
            Path with variables substituted

        Example:
            path = config.get_data_path("odds", sport="nfl", date="2024-12-01")
            # Returns Path("nfl/data/odds/2024-12-01")
        """
        paths = self._config.get("paths", {})

        # Get data_root first and substitute
        data_root = paths.get("data_root", "{sport}/data")
        for key, value in kwargs.items():
            data_root = data_root.replace(f"{{{key}}}", str(value))

        # Get specific path and substitute
        path_template = paths.get(path_type, "")
        path_template = path_template.replace("{data_root}", data_root)
        for key, value in kwargs.items():
            path_template = path_template.replace(f"{{{key}}}", str(value))

        return Path(path_template)

    def get_url(self, source: str, sport: str, url_type: str, **kwargs) -> str:
        """Get URL with variable substitution.

        Args:
            source: Data source (draftkings, reference)
            sport: Sport name (nfl, nba)
            url_type: URL type (schedule, boxscore, team_profile, etc.)
            **kwargs: Variables for substitution

        Returns:
            URL with variables substituted

        Example:
            url = config.get_url("reference", "nfl", "boxscore",
                                 date="202412010", home_abbr="dal")
        """
        url_template = self._urls.get(source, {}).get(sport, {}).get(url_type, "")
        for key, value in kwargs.items():
            url_template = url_template.replace(f"{{{key}}}", str(value))
        return url_template

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Access raw configuration dictionary."""
        return self._config

    @property
    def raw_urls(self) -> Dict[str, Any]:
        """Access raw URLs dictionary."""
        return self._urls


# Convenience function
def get_config() -> ConfigLoader:
    """Get the singleton ConfigLoader instance."""
    return ConfigLoader()
