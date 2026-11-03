"""Adaptador do Pub/Sub: publicação em lote e pull síncrono com confirmação explícita (ack)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from google.api_core import exceptions as gax
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import BatchSettings

from radar_alfabetizacao.ports import ReceivedMessage

_ACK_CHUNK = 1000


class PubSubPublisher:
    def __init__(self, project_id: str, topic: str) -> None:
        self._client = pubsub_v1.PublisherClient(
            batch_settings=BatchSettings(max_messages=500, max_latency=0.05)
        )
        self._topic = self._client.topic_path(project_id, topic)

    def publish_all(self, messages: Sequence[tuple[bytes, Mapping[str, str]]]) -> int:
        futures = [
            self._client.publish(self._topic, data, **dict(attributes))
            for data, attributes in messages
        ]
        for future in futures:
            future.result(timeout=120)
        return len(futures)


class PubSubPuller:
    def __init__(self, project_id: str, subscription: str) -> None:
        self._client = pubsub_v1.SubscriberClient()
        self._subscription = self._client.subscription_path(project_id, subscription)

    def pull(self, max_messages: int) -> list[ReceivedMessage]:
        try:
            response = self._client.pull(
                request={"subscription": self._subscription, "max_messages": max_messages},
                timeout=30,
            )
        except gax.DeadlineExceeded:
            return []
        return [
            ReceivedMessage(
                message_id=item.message.message_id,
                data=bytes(item.message.data),
                publish_time=item.message.publish_time,
                ack_id=item.ack_id,
                attributes=dict(item.message.attributes),
            )
            for item in response.received_messages
        ]

    def ack(self, ack_ids: Sequence[str]) -> None:
        for start in range(0, len(ack_ids), _ACK_CHUNK):
            chunk = list(ack_ids[start : start + _ACK_CHUNK])
            self._client.acknowledge(request={"subscription": self._subscription, "ack_ids": chunk})
