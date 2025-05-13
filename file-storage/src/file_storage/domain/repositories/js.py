from faststream.nats import JStream
from nats.js.api import RetentionPolicy, StreamSource

stream = JStream(
    name="inference",
    retention=RetentionPolicy.LIMITS,
    subjects=["inference.upload"],
    sources=[StreamSource(name="INFERENCE")],
)
