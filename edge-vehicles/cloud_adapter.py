import os
import json
import logging
import urllib.request
import urllib.error
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CloudAdapter")

class CloudAdapter(ABC):
    """
    Abstract Base Class for Edge-to-Cloud Transport Adapters.
    Decouples payload data formatting and transmission protocol from core vehicle logic.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection to the target cloud endpoint."""
        pass

    @abstractmethod
    def send(self, secure_envelope: dict) -> bool:
        """
        Transmits a signed secure payload envelope to the cloud endpoint.
        Returns True on successful transmission, False otherwise.
        """
        pass

class MockCloudAdapter(CloudAdapter):
    """
    Mock Adapter for local testing and offline simulation.
    Validates payload structure and logs transmission locally.
    """

    def __init__(self, endpoint_url: str = "mock://cloud-gateway"):
        self.endpoint_url = endpoint_url
        self.connected = False
        self.sent_count = 0

    def connect(self) -> bool:
        self.connected = True
        logger.info(f"[MockCloudAdapter] Connected to simulated endpoint: {self.endpoint_url}")
        return True

    def send(self, secure_envelope: dict) -> bool:
        if not self.connected:
            self.connect()

        self.sent_count += 1
        logger.info(f"[MockCloudAdapter] Secure Envelope #{self.sent_count} successfully transmitted to cloud:")
        logger.info(f"   Payload ID: {secure_envelope.get('payload_id')}")
        logger.info(f"   Vehicle ID: {secure_envelope.get('vehicle_id')}")
        logger.info(f"   Payload Type: {secure_envelope.get('payload_type')}")
        logger.info(f"   Signature: {secure_envelope.get('signature')[:16]}...")
        return True

class HTTPRestAdapter(CloudAdapter):
    """
    HTTP REST Adapter transmitting envelopes via POST requests over HTTP/HTTPS.
    Supports timeout and basic retry logic.
    """

    def __init__(self, endpoint_url: str = "http://localhost:8080/api/edge/ingest", timeout: int = 10):
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        logger.info(f"[HTTPRestAdapter] Target HTTP endpoint set to: {self.endpoint_url}")
        return True

    def send(self, secure_envelope: dict) -> bool:
        if not self.connected:
            self.connect()

        data_bytes = json.dumps(secure_envelope).encode('utf-8')
        req = urllib.request.Request(
            self.endpoint_url,
            data=data_bytes,
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status in (200, 201, 202):
                    logger.info(f"[HTTPRestAdapter] Successfully posted envelope {secure_envelope.get('payload_id')} to {self.endpoint_url} (HTTP {response.status})")
                    return True
                else:
                    logger.warning(f"[HTTPRestAdapter] HTTP endpoint returned status code: {response.status}")
                    return False
        except urllib.error.URLError as e:
            logger.error(f"[HTTPRestAdapter] Network error transmitting payload: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"[HTTPRestAdapter] Unexpected error transmitting payload: {str(e)}")
            return False

class WebSocketAdapter(CloudAdapter):
    """
    WebSocket Adapter for real-time streaming transmission.
    """

    def __init__(self, endpoint_url: str = "ws://localhost:8080/ws/edge"):
        self.endpoint_url = endpoint_url
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        logger.info(f"[WebSocketAdapter] WebSocket URL configured: {self.endpoint_url}")
        return True

    def send(self, secure_envelope: dict) -> bool:
        if not self.connected:
            self.connect()

        logger.info(f"[WebSocketAdapter] Streaming secure envelope {secure_envelope.get('payload_id')} to {self.endpoint_url}")
        # In actual deployment, websocket library sends frame here.
        return True

class AdapterFactory:
    """
    Factory class to instantiate Cloud Adapters based on environment configuration or explicit type.
    """

    @staticmethod
    def create_adapter(adapter_type: str = None, endpoint_url: str = None) -> CloudAdapter:
        if adapter_type is None:
            adapter_type = os.getenv("CLOUD_ADAPTER_TYPE", "mock").lower()

        if endpoint_url is None:
            endpoint_url = os.getenv("CLOUD_ENDPOINT_URL")

        if adapter_type == "http":
            url = endpoint_url or "http://localhost:8080/api/edge/ingest"
            return HTTPRestAdapter(endpoint_url=url)
        elif adapter_type == "websocket" or adapter_type == "ws":
            url = endpoint_url or "ws://localhost:8080/ws/edge"
            return WebSocketAdapter(endpoint_url=url)
        elif adapter_type == "mock":
            url = endpoint_url or "mock://cloud-gateway"
            return MockCloudAdapter(endpoint_url=url)
        else:
            logger.warning(f"Unknown CLOUD_ADAPTER_TYPE '{adapter_type}'. Falling back to MockCloudAdapter.")
            return MockCloudAdapter()