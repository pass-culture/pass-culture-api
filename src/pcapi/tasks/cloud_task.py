from dataclasses import dataclass
import json
import logging
from typing import Optional

from google.api_core import retry
from google.api_core.exceptions import AlreadyExists
from google.cloud import tasks_v2

from pcapi import settings


logger = logging.getLogger(__name__)


AUTHORIZATION_HEADER_KEY = "AUTHORIZATION"
AUTHORIZATION_HEADER_VALUE = f"Bearer {settings.CLOUD_TASK_BEARER_TOKEN}"


def get_client():
    if not hasattr(get_client, "client"):
        get_client.client = tasks_v2.CloudTasksClient()

    return get_client.client


@dataclass
class CloudTaskHttpRequest:
    http_method: tasks_v2.HttpMethod
    url: str
    headers: Optional[dict] = None
    body: Optional[bytes] = None


def enqueue_task(queue: str, http_request: CloudTaskHttpRequest):
    client = get_client()
    parent = client.queue_path(settings.GCP_PROJECT, settings.GCP_REGION_CLOUD_TASK, queue)

    task_request = {"http_request": http_request}

    try:
        response = client.create_task(
            request={"parent": parent, "task": task_request},
            retry=retry.Retry(
                initial=settings.CLOUD_TASK_RETRY_INITIAL_DELAY,
                maximum=settings.CLOUD_TASK_RETRY_MAXIMUM_DELAY,
                multiplier=settings.CLOUD_TASK_RETRY_MULTIPLIER,
                deadline=settings.CLOUD_TASK_RETRY_DEADLINE,
            ),
        )
    except AlreadyExists:
        logger.info("Task on queue %s url %s already retried", queue, http_request.url)
        return None

    task_id = response.name.split("/")[-1]
    return task_id


def enqueue_internal_task(queue, url, payload):
    http_request = CloudTaskHttpRequest(
        http_method=tasks_v2.HttpMethod.POST,
        url=url,
        headers={"Content-type": "application/json", AUTHORIZATION_HEADER_KEY: AUTHORIZATION_HEADER_VALUE},
        body=json.dumps(payload).encode(),
    )

    return enqueue_task(queue, http_request)
