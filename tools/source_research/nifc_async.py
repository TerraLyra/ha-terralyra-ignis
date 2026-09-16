"""Research compatibility entry point for integration-owned NIFC retrieval."""
import asyncio
from nifc_package import load_module
_client = load_module("client")
_read = _client._read
fetch_incidents_async = _client.fetch_incidents_async
NifcClient = _client.NifcClient
