"""Define `FilingsPage` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Iterable
from itertools import chain
from typing import Any, Union

from xbrl_filings_api.api_page import _APIPage
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    ScopeFlag,
)
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.validation_message import ValidationMessage

logger = logging.getLogger(__name__)


class FilingsPage(_APIPage):
    """
    JSON:API response page containing filing resources.

    Attributes
    ----------
    query_time : datetime
    query_filing_count : int or None
    filing_list: list of Filing
    entity_list : list of Entity or None
    validation_message_list : list of ValidationMessage or None
    jsonapi_version : str or None
    api_self_url : str or None
    api_prev_page_url : str or None
    api_next_page_url : str or None
    api_first_page_url : str or None
    api_last_page_url : str or None
    request_url : str
    """

    def __init__(
            self, json_frag: dict, api_request: _APIRequest,
            flags: ScopeFlag, received_api_ids: dict[str, set],
            res_colls: dict[str, ResourceCollection]
            ) -> None:
        """Initiate a JSON:API response page."""
        super().__init__(json_frag, api_request)

        self.query_filing_count = self._data_count
        """Total count of filings of the query including the ones not on
        this page.
        """

        self.filing_list: list[Filing]
        """List of `Filing` objects on this page."""

        ents = self._get_inc_resource(
            api_request=api_request,
            received_api_ids=received_api_ids,
            type_obj=Entity,
            flag_member=GET_ENTITY,
            flags=flags
            )
        self.entity_list: Union[list[Entity], None] = ents # type: ignore
        """
        Set of `Entity` objects on this page.

        Is `None` if `flags` parameter did not include `GET_ENTITY`.
        """

        vmsgs = self._get_inc_resource(
            api_request=api_request,
            received_api_ids=received_api_ids,
            type_obj=ValidationMessage,
            flag_member=GET_VALIDATION_MESSAGES,
            flags=flags
            )
        self.validation_message_list: Union[list[ValidationMessage], None] = (
            vmsgs) # type: ignore
        """
        Set of `ValidationMessage` objects on this page.

        Is `None` if `flags` parameter did not include
        `GET_VALIDATION_MESSAGES`.
        """

        self._json.close()

        self.filing_list = self._get_filings(
            received_api_ids, res_colls, flags)
        self._check_validation_messages_references()
        self._determine_unexpected_inc_resources()

    def _get_filings(
            self, received_api_ids: dict[str, set],
            res_colls: dict[str, ResourceCollection], flags: ScopeFlag
            ) -> list[Filing]:
        """Get filings from from `data` key list."""
        filing_list = []
        if not received_api_ids.get('Filing'):
            received_api_ids['Filing'] = set()
        received_set = received_api_ids['Filing']

        if self._data:
            for res_frag in self._data:
                res_type = str(res_frag.get('type')).lower()

                if res_type == Filing.TYPE:
                    filing = self._parse_filing_fragment(
                        res_frag, received_set, res_colls, flags)
                    if filing:
                        filing_list.append(filing)
                else:
                    self._json.unexpected_resource_types.add(
                        (res_type, 'data'))
        return filing_list

    def _parse_filing_fragment(
            self, res_frag: dict[str, Any], received_set: set[str],
            res_colls: dict[str, ResourceCollection], flags: ScopeFlag
            ) -> Union[Filing, None]:
        """Get filings from from a single `data` key fragment."""
        res_id = str(res_frag.get('id'))
        if res_id in received_set:
            msg = f'Same filing returned again, api_id={res_id!r}.'
            logger.warning(msg, stacklevel=3)
            return None
        else:
            received_set.add(res_id)
            entity_iter = None
            message_iter = None
            if GET_ONLY_FILINGS not in flags:
                if GET_ENTITY in flags:
                    ents = self.entity_list if self.entity_list else ()
                    entity_iter = chain(ents, res_colls['Entity'])
                if GET_VALIDATION_MESSAGES in flags:
                    vmsgs = (
                        self.validation_message_list
                        if self.validation_message_list else ()
                        )
                    message_iter = chain(vmsgs, res_colls['ValidationMessage'])
            iters: tuple[
                Union[Iterable[Entity], None],
                Union[Iterable[ValidationMessage], None]
                ] = entity_iter, message_iter # type: ignore
            return Filing(
                res_frag,
                _APIRequest(self.request_url, self.query_time),
                *iters
                )

    def _get_inc_resource(
            self,
            api_request: _APIRequest,
            received_api_ids: dict[str, set],
            type_obj: type[APIResource],
            flag_member: ScopeFlag,
            flags: ScopeFlag
            ) -> Union[list[APIResource], None]:
        if (GET_ONLY_FILINGS in flags or flag_member not in flags):
            return None

        resource_list = []
        type_name = type_obj.__class__.__name__
        if not received_api_ids.get(type_name):
            received_api_ids[type_name] = set()
        received_set = received_api_ids[type_name]

        found_ix = []
        for res_i, res in enumerate(self._included_resources):
            if res.type_ == type_obj.TYPE:
                if res.id_ not in received_set:
                    received_set.add(res.id_)
                    # Construct Entity() or ValidationMessage()
                    res_instance = type_obj(res.frag, api_request)
                    resource_list.append(res_instance)
                    found_ix.append(res_i)
        found_ix.reverse()
        for res_i in found_ix:
            del self._included_resources[res_i]
        return resource_list

    def _determine_unexpected_inc_resources(self) -> None:
        self._json.unexpected_resource_types.update(
            [(res.type_, 'included') for res in self._included_resources])

    def _check_validation_messages_references(self) -> None:
        if self.validation_message_list is not None:
            for vmsg in self.validation_message_list:
                if vmsg.filing is None:
                    msg = (
                        f'No filing defined for {vmsg!r}, api_id={vmsg.api_id}'
                        )
                    logger.warning(msg, stacklevel=2)
