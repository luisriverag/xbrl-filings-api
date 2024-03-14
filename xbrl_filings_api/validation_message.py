"""Define `ValidationMessage` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import re
import urllib.parse
from pathlib import PurePath
from typing import Union

from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.enums import GET_VALIDATION_MESSAGES

EllipsisType = type(Ellipsis) # No valid solution for Python 3.9
logger = logging.getLogger(__name__)


class ValidationMessage(APIResource):
    """
    A single validation message of any severity.

    The source of validation has not been published by filings.xbrl.org
    but it seems likely that they originate from Arelle software.

    Validation messages are issues in XBRL standard conformance, and the
    formula rules defined in the XBRL taxonomy.

    Country-specific filing rules defined by financial regulatory
    authorities and other agencies are not in the scope of validation.
    The rules defined in ESEF Reporting Manual are not checked if they
    are not codified in the taxonomy formula rules.

    Calculation inconsistency is the term used for issues in accounting
    coherence.

    Attributes
    ----------
    api_id : str or None
    severity : str or None
    text : str or None
    code : str or None
    filing_api_id : str or None
    filing : Filing or None
    calc_computed_sum : float or None
    calc_reported_sum : float or None
    calc_context_id : str or None
    calc_line_item : str or None
    calc_short_role : str or None
    calc_unreported_items : list of str or None
    duplicate_greater : float or None
    duplicate_lesser : float or None
    query_time : datetime
    request_url : str
    """

    TYPE: str = 'validation_message'
    SEVERITY = 'attributes.severity'
    TEXT = 'attributes.message'
    CODE = 'attributes.code'

    _FILING_FLAG = GET_VALIDATION_MESSAGES

    _LINE_ITEM_RE = re.compile(r'\bfrom (\S+)')
    _SHORT_ROLE_RE = re.compile(r'\blink role (\S+)')
    _REPORTED_SUM_RE = re.compile(r'\breported sum (\S+)')
    _COMPUTED_SUM_RE = re.compile(r'\bcomputed sum (\S+)')
    _CONTEXT_ID_RE = re.compile(r'\bcontext (\S+)')
    _UNREPORTED_ITEMS_RE = re.compile(r'\bunreportedContributingItems (.+)')
    _COMMA_RE = re.compile(r'\s*,\s*')
    _DUPLICATE_1_RE = re.compile(r'\bvalue:\s*(\S+)')
    _DUPLICATE_2_RE = re.compile(r'!=\s+(\S+)')

    def __init__(
            self,
            json_frag: Union[dict, EllipsisType],
            api_request: Union[_APIRequest, None] = None
            ) -> None:
        super().__init__(json_frag, api_request)

        self.severity: Union[str, None] = self._json.get(self.SEVERITY)
        """
        Severity of the validation message.

        Can be ``ERROR``, ``WARNING`` or ``INCONSISTENCY``.
        Might include ``ERROR-SEMANTIC`` and ``WARNING-SEMANTIC`` but
        most likely not.

        Arelle has also more message levels, but these are very
        certainly not included anywhere (``(DYNAMIC)``, ``CRITICAL``,
        ``DEBUG``, ``EXCEPTION``, ``INFO``, ``INFO-RESULT``).
        """

        self.text: Union[str, None] = self._json.get(self.TEXT)
        """Validation message text."""
        if isinstance(self.text, str):
            self.text = self.text.strip()

        self.code: Union[str, None] = self._json.get(self.CODE)
        """
        The code describing the source of the broken rule.

        For example, code ``xbrl.5.2.5.2:calcInconsistency`` refers to
        XBRL 2.1 base specification heading 5.2.5.2 with title "The
        <calculationArc> element".
        """

        self.filing_api_id: Union[str, None] = None
        """`api_id` of Filing object."""

        # Filing object
        self.filing: Union[object, None] = None
        """`Filing` object of this validation message."""

        self._json.close()

        self.calc_computed_sum: Union[float, None] = None
        """
        Derived computed sum of the calculation inconsistency.

        Based on attribute `text` for validation messages whose `code`
        is ``xbrl.5.2.5.2:calcInconsistency``.
        """

        self.calc_reported_sum: Union[float, None] = None
        """
        Derived reported sum of the calculation inconsistency.

        Based on attribute `text` for validation messages whose `code`
        is ``xbrl.5.2.5.2:calcInconsistency``.
        """

        self.calc_context_id: Union[str, None] = None
        """
        Derived XBRL context ID of the calculation inconsistency.

        Based on attribute `text` for validation messages whose `code`
        is ``xbrl.5.2.5.2:calcInconsistency``.
        """

        self.calc_line_item: Union[str, None] = None
        """
        Derived line item name of the calculation inconsistency.

        This field contains the qualified name of the line item (XBRL
        concept) with the taxonomy prefix and the local name parts. It
        could be for example "ifrs-full:Assets".

        Based on attribute `text` for validation messages whose `code`
        is ``xbrl.5.2.5.2:calcInconsistency``.
        """

        self.calc_short_role: Union[str, None] = None
        """
        Derived last part of the link role of the calculation
        inconsistency.

        For example a link role URI
        "http://www.example.com/esef/taxonomy/2022-12-31/FinancialPositionConsolidated"
        is truncated to "FinancialPositionConsolidated".

        Based on attribute `text` for validation messages whose `code`
        is ``xbrl.5.2.5.2:calcInconsistency``.
        """

        self.calc_unreported_items: Union[list[str], None] = None
        """
        Derived unreported contributing line items of the calculation
        inconsistency.

        This refers to the line item names of items which are defined as
        the addends for `calc_line_item` in any of the link roles in the
        XBRL taxonomies of this report and which were not reported in
        the same XBRL context with this fact.

        When the data is output to a database, this field is a string
        with parts joined by a newline character ('\\n').

        Based on attribute `text` for validation messages whose `code`
        is ``xbrl.5.2.5.2:calcInconsistency``.
        """

        self.duplicate_greater: Union[float, None] = None
        """
        Derived greater item of the duplicate pair.

        Based on attribute `text` for validation messages whose `code`
        is ``message:tech_duplicated_facts1``.

        Does not include code ``formula:assertionUnsatisfied`` with
        ``tech_duplicated_facts1`` in the beginning of the message (more
        than 2 duplicated facts).
        """

        self.duplicate_lesser: Union[float, None] = None
        """
        Derived lesser item of the duplicate pair.

        Based on attribute `text` for validation messages whose `code`
        is ``message:tech_duplicated_facts1``.

        Does not include code ``formula:assertionUnsatisfied`` with
        ``tech_duplicated_facts1`` in the beginning of the message (more
        than 2 duplicated facts).
        """

        if self.code == 'xbrl.5.2.5.2:calcInconsistency':
            self.calc_computed_sum = self._derive_calc_float(
                self._COMPUTED_SUM_RE, 'calc_computed_sum')
            self.calc_reported_sum = self._derive_calc_float(
                self._REPORTED_SUM_RE, 'calc_reported_sum')
            self.calc_context_id = self._derive_calc(
                self._CONTEXT_ID_RE)
            self.calc_line_item = self._derive_calc(
                self._LINE_ITEM_RE)
            self.calc_short_role = self._derive_calc(
                self._SHORT_ROLE_RE)
            unreported_items = self._derive_calc(
                self._UNREPORTED_ITEMS_RE)

            uri_path = urllib.parse.urlparse(self.calc_short_role).path
            if uri_path.strip():
                last_part = PurePath(uri_path).name
                if last_part.strip():
                    self.calc_short_role = last_part

            if unreported_items and unreported_items.lower() != 'none':
                self.calc_unreported_items = (
                    self._COMMA_RE.split(unreported_items))

        if self.code == 'message:tech_duplicated_facts1':
            duplicate_1 = self._derive_calc_float(
                self._DUPLICATE_1_RE, 'duplicate_*')
            duplicate_2 = self._derive_calc_float(
                self._DUPLICATE_2_RE, 'duplicate_*')
            if (isinstance(duplicate_1, float)
                    and isinstance(duplicate_2, float)):
                self.duplicate_greater = max(duplicate_1, duplicate_2)
                self.duplicate_lesser = min(duplicate_1, duplicate_2)

    def __repr__(self) -> str:
        """
        Return string repr of validation message.

        Displays `code` attribute.
        """
        return f'{self.__class__.__name__}(code={self.code!r})'

    def __str__(self) -> str:
        """Return `text` attribute value."""
        if self.text is None:
            return ''
        return self.text

    def _derive_calc(self, re_obj: re.Pattern) -> Union[str, None]:
        mt = re_obj.search(self.text)
        if mt:
            return mt[1]
        return None

    def _derive_calc_float(
            self, re_obj: re.Pattern, attr_name: str) -> Union[float, None]:
        calc_str = self._derive_calc(re_obj)
        calc_float = None
        if calc_str is not None:
            try:
                calc_float = float(calc_str.replace(',', ''))
            except ValueError:
                msg = (
                    f'String {calc_str!r} of attribute {attr_name!r} could '
                    'not be parsed into float.'
                    )
                logger.warning(msg, stacklevel=2)
        return calc_float
