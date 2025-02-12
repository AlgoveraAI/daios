# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the handlers for the skill of ChatCompletionAbciApp."""

import fnmatch
import json
import re
import subprocess
import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urlparse

from aea.configurations.data_types import PublicId
from aea.protocols.base import Message

from packages.algovera.protocols.chat_completion.message import ChatCompletionMessage
from packages.algovera.skills.valory_chat_abci.dialogues import (
    HttpDialogue,
    HttpDialogues,
)
from packages.algovera.skills.valory_chat_abci.rounds import SynchronizedData
from packages.algovera.skills.valory_chat_abci.schemas import Chat, Embedding
from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler as BaseABCIRoundHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import AbstractResponseHandler
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler as BaseContractApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    IpfsHandler as BaseIpfsHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    LedgerApiHandler as BaseLedgerApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    SigningHandler as BaseSigningHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    TendermintHandler as BaseTendermintHandler,
)


ABCIHandler = BaseABCIRoundHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler
IpfsHandler = BaseIpfsHandler


OK_CODE = 200
NOT_FOUND_CODE = 404
BAD_REQUEST_CODE = 400
AVERAGE_PERIOD_SECONDS = 10


class HttpMethod(Enum):
    """Http methods"""

    GET = "get"
    POST = "post"


class HttpHandler(BaseHttpHandler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""
        service_endpoint_base = urlparse(
            self.context.params.service_endpoint_base
        ).hostname
        propel_uri_base_hostname = (
            r"https?:\/\/[a-zA-Z0-9]{16}.agent\.propel\.(staging\.)?autonolas\.tech"
        )

        # Route regexes
        hostname_regex = rf".*({service_endpoint_base}|{propel_uri_base_hostname}|localhost|127.0.0.1|0.0.0.0)(:\d+)?"
        self.handler_url_regex = rf"{hostname_regex}\/.*"

        # Endpoint regexes
        post_embedding_url_regex = rf"{hostname_regex}\/embedding\/?$"
        post_chat_url_regex = rf"{hostname_regex}\/chat\/?$"

        cc_id_regex = r"(?P<chat_id>[a-fA-F0-9]{32})"
        get_cc_url_regex = rf"{hostname_regex}\/get\/{cc_id_regex}"

        # Routes
        self.routes = {
            (HttpMethod.POST.value,): [
                (post_embedding_url_regex, self._handle_post_embedding),
                (post_chat_url_regex, self._handle_post_chat),
            ],
            (HttpMethod.GET.value,): [
                (get_cc_url_regex, self._handle_get_request),
            ],
        }

        self.json_content_header = "Content-Type: application/json\n"

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return SynchronizedData(
            db=self.context.state.round_sequence.latest_synchronized_data.db
        )

    def _get_handler(self, url: str, method: str) -> Tuple[Optional[Callable], Dict]:
        """Check if an url is meant to be handled in this handler

        We expect url to match the pattern {hostname}/.*,
        where hostname is allowed to be localhost, 127.0.0.1 or the token_uri_base's hostname.
        Examples:
            localhost:8000/0
            127.0.0.1:8000/100
            https://pfp.staging.autonolas.tech/45
            http://pfp.staging.autonolas.tech/120

        :param url: the url to check
        :returns: the handling method if the message is intended to be handled by this handler, None otherwise, and the regex captures
        """
        # Check base url
        if not re.match(self.handler_url_regex, url):
            self.context.logger.info(
                f"The url {url} does not match the this HttpHandler's pattern"
            )
            return None, {}

        # Check if there is a route for this request
        for methods, routes in self.routes.items():
            if method not in methods:
                continue

            for route in routes:
                # Routes are tuples like (route_regex, handle_method)
                m = re.match(route[0], url)
                if m:
                    return route[1], m.groupdict()

        # No route found
        self.context.logger.info(
            f"The message [{method}] {url} is intended for the this HttpHandler but did not match any valid pattern"
        )
        return self._handle_bad_request, {}

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # Check if this is a request sent from the http_server skill
        if (
            http_msg.performative != HttpMessage.Performative.REQUEST
            or message.sender != str(HTTP_SERVER_PUBLIC_ID.without_hash())
        ):
            super().handle(message)
            return

        # Check if this message is for this skill. If not, send to super()
        handler, kwargs = self._get_handler(http_msg.url, http_msg.method)
        if not handler:
            super().handle(message)
            return

        # Retrieve dialogues
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))

        # Invalid message
        if http_dialogue is None:
            self.context.logger.info(
                "Received invalid http message={}, unidentified dialogue.".format(
                    http_msg
                )
            )
            return

        # Handle message
        self.context.logger.info(
            "Received http request with method={}, url={} and body={!r}".format(
                http_msg.method,
                http_msg.url,
                http_msg.body,
            )
        )
        handler(http_msg, http_dialogue, **kwargs)

    def _handle_bad_request(
        self,
        http_msg: HttpMessage,
        http_dialogue: HttpDialogue,
        status_txt: str = "Bad request",
    ) -> None:
        """
        Handle a Http bad request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=BAD_REQUEST_CODE,
            status_text=status_txt,
            headers=http_msg.headers,
            body=b"",
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_post_embedding(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """Handle a POST embedding request."""

        self.context.logger.info("Received embedding request")
        # Check if the request is valid
        request_data = json.loads(http_msg.body)

        # Check valid admin_password
        # TODO: Move password to env variable
        if request_data["admin_password"] != "valory_algover":
            self.context.logger.error("Invalid admin password")
            self._handle_bad_request(
                http_msg, http_dialogue, status_txt="Invalid admin password"
            )
            return

        # # Get github repo for embedding
        # repo_url = "https://github.com/valory-xyz/docs.git"

        # # Get documents
        # documents = self.get_github_docs(repo_url)
        # Check if data meets schema

        try:
            embedding_request = Embedding.parse_obj({"documents": []})
            self.context.logger.info("Request data meets schema: {embedding_request}}")
        except Exception as e:
            self.context.logger.error(f"Request data does not meet schema: {e}")
            self._handle_bad_request(http_msg, http_dialogue)
            return

        self.context.state.new_embedding_requests.append(embedding_request.dict())

        response_body_data = {"ok": True, "message": "Embedding request received"}

        self._send_ok_response(http_msg, http_dialogue, response_body_data)

    def _handle_post_chat(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """Handle a POST chat request."""

        self.context.logger.info("Received request")

        request_data = json.loads(http_msg.body)

        # Add the new request to the list of requests on state
        # Generate a new id if one is not provided
        id_ = request_data["id"] if "id" in request_data else uuid.uuid4().hex

        # Check memory_id exists if provided
        if "memory_id" in request_data:
            memories = self.synchronized_data.chat_histories
            memory_ids = list(memories.keys())
            if not request_data["memory_id"] in memory_ids:
                self.context.logger.error(
                    f"memory_id {request_data['memory_id']} does not exist"
                )
                self._handle_bad_request(
                    http_msg,
                    http_dialogue,
                    f"memory_id {request_data['memory_id']} does not exist",
                )
                return
        else:
            # Assume new conversation
            request_data["memory_id"] = uuid.uuid4().hex

        # Check if data meets schema
        try:
            chat_request = Chat.parse_obj(request_data)
        except Exception as e:
            self.context.logger.error(f"Request data does not meet schema: {e}")
            self._handle_bad_request(http_msg, http_dialogue)
            return

        self.context.state.new_chat_requests.append(
            chat_request.dict(),
        )

        response_body_data = {"id": id_, "memory_id": request_data["memory_id"]}

        self._send_ok_response(http_msg, http_dialogue, response_body_data)

    def _handle_get_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue, chat_id: str
    ) -> None:

        # Get the token address
        id_ = http_msg.url.split("/")[-1]

        self.context.logger.info(f"Received request for id {id_}")
        self.context.logger.info(f"Chat id {chat_id}")

        response = [d for d in self.synchronized_data.chats if d["id"] == id_]

        response_body_data = response

        self._send_ok_response(http_msg, http_dialogue, response_body_data)

    def _send_ok_response(
        self,
        http_msg: HttpMessage,
        http_dialogue: HttpDialogue,
        data: Union[Dict, List],
    ) -> None:
        """Send an OK response with the provided data"""
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=OK_CODE,
            status_text="Success",
            headers=f"{self.json_content_header}{http_msg.headers}",
            body=json.dumps(data).encode("utf-8"),
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _send_not_found_response(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """Send an not found response"""
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=NOT_FOUND_CODE,
            status_text="Not found",
            headers=http_msg.headers,
            body=b"",
        )
        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)


class ChatCompletionHandler(AbstractResponseHandler):
    SUPPORTED_PROTOCOL: Optional[PublicId] = ChatCompletionMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            ChatCompletionMessage.Performative.REQUEST,
            ChatCompletionMessage.Performative.RESPONSE,
        }
    )
