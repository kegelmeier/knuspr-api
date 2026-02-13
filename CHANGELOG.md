# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-13

### Added

- Core `KnusprClient` with context manager for automatic login/logout
- Product search with automatic promoted-item filtering
- Cart management: add items, view cart, remove items by order field ID
- Delivery time slot retrieval
- Order history and order detail lookup
- Upcoming orders retrieval
- Premium subscription profile info
- Account data aggregation (user, address, cart, delivery info)
- CLI with 8 commands: `search`, `add`, `cart`, `remove`, `slots`, `orders`, `order`, `account`
- Cookie-based authentication via httpx
- Configurable rate limiting (default 100ms between requests)
- Pydantic v2 models with camelCase alias mapping
- Configuration via environment variables or `.env` file
- PEP 561 typed package marker
- 38 unit tests with respx mocking
