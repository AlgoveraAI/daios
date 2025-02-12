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

"""This module contains the transaction payloads of the ValoryChatAbciApp."""

from dataclasses import dataclass
from typing import Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


@dataclass(frozen=True)
class ChatPayload(BaseTxPayload):
    """Represent a transaction payload for the ChatRound."""

    sender: str
    processed_chat: str


@dataclass(frozen=True)
class EmbeddingPayload(BaseTxPayload):
    """Represent a transaction payload for the EmbeddingRound."""

    sender: str
    processed_embedding: str


@dataclass(frozen=True)
class RegistrationPayload(BaseTxPayload):
    """Represent a transaction payload for the RegistrationRound."""

    sender: str


@dataclass(frozen=True)
class SynchronizeEmbeddingsPayload(BaseTxPayload):
    """Represent a transaction payload for the SynchronizeEmbeddingsRound."""

    sender: str
    new_embedding_requests: Optional[str] = None


@dataclass(frozen=True)
class SynchronizeRequestsPayload(BaseTxPayload):
    """Represent a transaction payload for the SynchronizeRequestsRound."""

    sender: str
    new_chat_requests: Optional[str] = None
