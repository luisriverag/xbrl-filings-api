"""Define `FilingsPage` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Iterable
from itertools import chain
from typing import Any, Union

from xbrl_filings_api.api_page import APIPage
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import ScopeFlag
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.validation_message import ValidationMessage

__all__ = ['FilingsPage']

logger = logging.getLogger(__name__)


class FilingsPage(APIPage):
    r"""Response page containing filings as primary resource."""

    def __init__(
            self, json_frag: dict, api_request: APIRequest,
            flags: ScopeFlag, received_api_ids: dict[str, set],
            res_colls: dict[str, ResourceCollection]
            ) -> None:
        super().__init__(json_frag, api_request)

        self.query_filing_count = self._data_count
        """Total count of filings of the query including the ones not on
        this page.
        """

        self.filing_list: list[Filing]
        """List of `Filing` objects on this page."""

        ents = self._get_inc_resource(
            type_obj=Entity,
            api_request=api_request,
            received_api_ids=received_api_ids,
            flag_member=ScopeFlag.GET_ENTITY,
            flags=flags
            )
        # type_obj=Entity always returns list[Entity] | None
        self.entity_list: Union[list[Entity], None] = (
            ents) # type: ignore[assignment]
        """
        Set of `Entity` objects on this page.

        Is :pt:`None` if ``flags`` parameter did not include
        `GET_ENTITY`.
        """

        vmsgs = self._get_inc_resource(
            type_obj=ValidationMessage,
            api_request=api_request,
            received_api_ids=received_api_ids,
            flag_member=ScopeFlag.GET_VALIDATION_MESSAGES,
            flags=flags
            )
        # type_obj=ValidationMessage always returns
        # list[ValidationMessage] | None
        self.validation_message_list: Union[list[ValidationMessage], None] = (
            vmsgs) # type: ignore[assignment]
        """
        Set of `ValidationMessage` objects on this page.

        Is :pt:`None` if ``flags`` parameter did not include
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
        """Get filings from from document ``data`` key."""
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
        """Get filings from from a single ``data`` key fragment."""
        res_id = str(res_frag.get('id'))
        if res_id in received_set:
            msg = f'Same filing returned again, api_id={res_id!r}.'
            logger.warning(msg, stacklevel=3)
            return None
        else:
            received_set.add(res_id)
            entity_iter: Union[Iterable[Entity], None] = None
            message_iter: Union[Iterable[ValidationMessage], None] = None
            if ScopeFlag.GET_ONLY_FILINGS not in flags:
                if ScopeFlag.GET_ENTITY in flags:
                    ents = self.entity_list if self.entity_list else ()
                    entity_iter = chain(
                        ents,
                        res_colls['Entity'] # type: ignore[arg-type]
                        )
                if ScopeFlag.GET_VALIDATION_MESSAGES in flags:
                    vmsgs = (
                        self.validation_message_list
                        if self.validation_message_list else ()
                        )
                    message_iter = chain(
                        vmsgs,
                        res_colls['ValidationMessage'] # type: ignore[arg-type]
                        )
            api_request = APIRequest(self.request_url, self.query_time)
            return Filing(res_frag, api_request, entity_iter, message_iter)

    def _get_inc_resource(
            self,
            type_obj: type[APIResource],
            api_request: APIRequest,
            received_api_ids: dict[str, set],
            flag_member: ScopeFlag,
            flags: ScopeFlag
            ) -> Union[list[APIResource], None]:
        if (ScopeFlag.GET_ONLY_FILINGS in flags or flag_member not in flags):
            return None

        resource_list = []
        type_name = type_obj.__name__
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
                    msg = f'No filing defined for {vmsg!r}'
                    logger.warning(msg, stacklevel=2)

    def __repr__(self) -> str:
        """
        Return repr with request_url, query_time, and len(filing_list).

        Attribute `request_url` is shown as repr, `query_time` as
        unprefixed datetime() constructor, and len(`filing_list`) as
        integer.
        """
        time_str = self.query_time.strftime('%Y, %m, %d, %H, %M, %S')
        query_time = f'datetime({time_str})'
        subreslist = ''
        if self.entity_list is not None:
            subreslist += f', len(entity_list)={len(self.entity_list)}'
        if self.validation_message_list is not None:
            subreslist += (
                ', len(validation_message_list)='
                + str(len(self.validation_message_list))
                )
        return (
            f'{type(self).__name__}('
            f'request_url={self.request_url!r}, '
            f'query_time={query_time}, '
            f'len(filing_list)={len(self.filing_list)}{subreslist})'
            )
