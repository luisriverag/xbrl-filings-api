"""
Define `Filing` class.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import re
import urllib.parse
import warnings
from collections.abc import AsyncIterator, Iterable, Mapping
from datetime import date, datetime
from pathlib import PurePath
from types import EllipsisType

import xbrl_filings_api.download_specs_construct as download_specs_construct
import xbrl_filings_api.downloader as downloader
import xbrl_filings_api.save_paths as save_paths
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import ParseType
from xbrl_filings_api.exceptions import ApiReferenceWarning, DownloadErrorGroup
from xbrl_filings_api.lang_code_transform import LANG_CODE_TRANSFORM
from xbrl_filings_api.validation_message import ValidationMessage


class Filing(APIResource):
    """
    Represents a single XBRL filing i.e. a report package.

    Different language versions of the same report are separate filings.
    The language versions of the same report share the same
    `filing_index` except for the last integer.

    Attributes
    ----------
    api_id : str or None
    country : str or None
    filing_index : str or None
    language : str or None
    last_end_date : date or None
    reporting_date : date or None
    error_count : str or None
    inconsistency_count : str or None
    warning_count : str or None
    added_time : datetime or None
    processed_time : datetime or None
    entity_api_id : str or None
    entity : Entity or None
    validation_messages : set of ValidationMessage or None
    json_url : str or None
    package_url : str or None
    viewer_url : str or None
    xhtml_url : str or None
    request_time : datetime
    request_url : str
    json_download_path : str or None
    package_download_path : str or None
    viewer_download_path : str or None
    xhtml_download_path : str or None
    package_sha256 : str or None
    """

    TYPE: str = 'filing'
    COUNTRY = 'attributes.country'
    FILING_INDEX = 'attributes.fxo_id'
    LAST_END_DATE = 'attributes.period_end'
    ERROR_COUNT = 'attributes.error_count'
    INCONSISTENCY_COUNT = 'attributes.inconsistency_count'
    WARNING_COUNT = 'attributes.warning_count'
    ADDED_TIME = 'attributes.date_added'
    PROCESSED_TIME = 'attributes.processed'
    ENTITY_API_ID = 'relationships.entity.data.id'
    VALIDATION_MESSAGES = 'relationships.validation_messages.data'
    JSON_URL = 'attributes.json_url'
    PACKAGE_URL = 'attributes.package_url'
    VIEWER_URL = 'attributes.viewer_url'
    XHTML_URL = 'attributes.report_url'
    PACKAGE_SHA256 = 'attributes.sha256'

    VALID_DOWNLOAD_FORMATS = {'json', 'package', 'xhtml'}

    def __init__(
            self,
            json_frag: dict | EllipsisType,
            api_request: APIRequest | None = None,
            entity_iter: Iterable[Entity] | None = None,
            message_iter: Iterable[ValidationMessage] | None = None
            ) -> None:
        """Initialize a `Filing` object.

        Warns
        -----
        ApiReferenceWarning
            Resource referencing to/from entities and validation
            messages fails.
        """
        super().__init__(json_frag, api_request)

        self.country: str | None = self._json.get(self.COUNTRY)
        """
        The country where the filing was reported.

        In case of ESEF this is the country where the filer has issued
        securities on EU regulated markets. The securities are usually
        shares but could be other securities as well such as bonds.
        """

        self.filing_index: str | None = self._json.get(self.FILING_INDEX)
        """
        The filing index.

        The index is structured as:
          1. LEI identifier
          2. Reporting date
          3. Filing system
          4. Country
          5. Integer specifying the language version (arbitrary)

        The parts are separated by a hyphen. Please note that the
        ISO-style reporting date is also delimited by hyphens.

        The original field name in the API is ``fxo_id``.
        """

        self.language: str | None = None
        """
        Derived two-letter lower-case language identifier defining the
        language of the filing.

        This code is based on the file name in attribute `package_url`.

        Three-letter language identifiers are transformed into
        two-letter identifiers for official EU languages.
        """

        self.last_end_date: date | None = self._json.get(
            self.LAST_END_DATE, ParseType.DATE)
        """
        The end date of the last period in the marked-up report
        contents.

        This is not always the end date of the primary reporting period
        of the report. The derived field `reporting_date` is more
        reliable for this use case.

        The original field name in the API is ``period_end``.
        """

        self.reporting_date: date | None = None
        """
        Derived end date of the reporting period.

        This date is based on file name in the attribute `package_url`
        and if it cannot be derived, value in the attribute
        `last_end_date` will be used.

        As `last_end_date` regards only the absolute last recorded fact
        in the report (even if there is only one fact reported for this
        date), it is unreliable regarding filing mistakes and and
        future-bound facts.
        """

        self.error_count: str | None = self._json.get(self.ERROR_COUNT)
        """The count of validation errors listed in
        `validation_messages`."""

        self.inconsistency_count: str | None = self._json.get(
            self.INCONSISTENCY_COUNT)
        """The count of validation inconsistencies listed in
        `validation_messages`."""

        self.warning_count: str | None = self._json.get(
            self.WARNING_COUNT)
        """The count of validation warnings listed in
        `validation_messages`."""

        self.added_time: datetime | None = self._json.get(
            self.ADDED_TIME, ParseType.DATETIME)
        """
        Timezone-aware datetime when the filing was added to
        filings.xbrl.org index.

        Has an arbitrary delay after the issuer actually filed the
        report at the OAM. This library expects the dates to be returned
        in UTC, even though they do not have a timezone specifier and no
        documentation exists for its content.

        The timezone of the datetime is chosen according to option
        `utc_time`.

        The original field name in the API is ``date_added``.
        """

        self.processed_time: datetime | None = self._json.get(
            self.PROCESSED_TIME, ParseType.DATETIME)
        """
        Timezone-aware datetime when the filing was processed for the
        filings.xbrl.org index.

        The timezone of the datetime is chosen according to option
        `utc_time`.

        The original field name in the API is ``processed``.
        """

        self.entity_api_id: str | None = self._json.get(self.ENTITY_API_ID)
        """`api_id` of Entity object."""

        self.entity: Entity | None = None
        """
        The entity object of this filing.

        Is available when if GET_ENTITY is set in method
        `flags` parameter.
        """

        self.validation_messages: set[ValidationMessage] | None = None
        """
        The set of validation message objects of this filing.

        Is available when `flags` parameter contains
        `GET_VALIDATION_MESSAGES`. Not all filings have validation
        messages. Unfortunately too many do have.

        When flag is not set, this attribute is `None`.
        """

        self.json_url: str | None = self._json.get(
            self.JSON_URL, ParseType.URL)
        """
        Download URL for a derived xBRL-JSON document.

        The document is programmatically reserialized version of the
        Inline XBRL report. The conversion was carried by Arelle XBRL
        processor. The file is not a 'pure' data file but follows the
        information model of Open Information Model which includes for
        example declaration of XML-like namespaces inside a JSON file.

        The strange case of letters in this new XBRL term emphasizing
        the last three instead of all four was probably due to the fact
        that in the history of XBRL, more than one person has written
        these letters in a noncanonical order.
        """

        self.package_url: str | None = self._json.get(
            self.PACKAGE_URL, ParseType.URL)
        """
        Download URL for the official ESEF report package as filed to
        the OAM by the issuer.

        The report package is a ZIP archive which follows a predefined
        format. It consists of an inline XBRL report (iXBRL) and the
        extension taxonomy. The graphical iXBRL report can be found from
        'reports' directory inside the root folder and due to its visual
        elements (including embedded image files) it is typically the
        largest file in the package.
        """

        self.viewer_url: str | None = self._json.get(
            self.VIEWER_URL, ParseType.URL)
        """
        URL to a website with an inline XBRL viewer for this report.

        The website features the original XHTML report with ability to
        examine the marked up Inline XBRL facts one at a time. The
        underlying software is called The Open Source Inline XBRL Viewer
        and it is developed by Workiva.
        """

        self.xhtml_url: str | None = self._json.get(
            self.XHTML_URL, ParseType.URL)
        """
        Download URL for the inline XBRL report extracted from the
        official report package.

        Contains the actual data of the filing and its visual, PDF-like
        representation. The document has been extracted from the
        'reports' folder of the official report package. The report is
        an XHTML document with embedded inline XBRL markup.

        As this file is not compressed, it is likely to have a larger
        download size than the actual report package file.

        The original field name in the API is ``report_url`` despite the
        fact that this file is not the official report but a part of it.
        """

        self.json_download_path: str | None = None
        """Local path where `json_url` was downloaded."""

        self.package_download_path: str | None = None
        """Local path where `package_url` was downloaded."""

        self.viewer_download_path: str | None = None
        """Local path where `viewer_url` was downloaded."""

        self.xhtml_download_path: str | None = None
        """Local path where `xhtml_url` was downloaded."""

        self.package_sha256: str | None = self._json.get(self.PACKAGE_SHA256)
        """
        The SHA-256 hash of the report package file.

        Used for checking that the download of `package_url` was
        successful and the report is genuine.

        The original field name in the API is ``sha256``.
        """

        self.entity = self._search_entity(json_frag, entity_iter)
        self.validation_messages = (
            self._search_validation_messages(json_frag, message_iter))

        self._json.close()

        self.language = self._derive_language()
        self.reporting_date = self._derive_reporting_date()

    def __repr__(self) -> str:
        start = f'{self.__class__.__name__}('
        if self.entity:
            return (
                start + f'entity.name={self.entity.name!r}, '
                f'reporting_date={self.reporting_date}, '
                f'language={self.language!r})'
                )
        else:
            return start + f'filing_index={self.filing_index!r})'

    def download(
            self,
            formats: str | Iterable[str] | Mapping[str, DownloadItem],
            to_dir: str | PurePath | None = None,
            stem_pattern: str | None = None,
            check_corruption: bool = True,
            max_concurrent: int = 5,
            filename: str | None = None
            ) -> None:
        """
        Download files in type or types of `formats`.

        The directories in `to_dir` will be created if they do not
        exist. By default, filename is derived from download URL. If the
        file already exists, it will be overwritten.

        If parameter `formats` includes `package`, the downloaded files
        will be checked through the `package_sha256` attribute of Filing
        objects. If the hash does not match with the one calculated from
        download, exceptions `CorruptDownloadError` will be raised in a
        `DownloadErrorGroup` after all downloads have finished. The
        downloaded file will not be deleted but its name will be
        appended with ending ``.corrupt``.

        If download is interrupted, the files will be left with ending
        ``.unfinished``.

        If no name could be derived from `url`, the file will be named
        ``file0001``, ``file0002``, etc. In this case a new file is
        always created.

        Parameter `stem_pattern` requires a placeholder ``/name/``. For
        example pattern ``/name/_second_try`` will change original
        filename ``743700XJC24THUPK0S03-2022-12-31-fi.xhtml`` into
        ``743700XJC24THUPK0S03-2022-12-31-fi_second_try.xhtml``. Not
        recommended for packages as their names should not be changed.

        Parameters
        ----------
        formats : str or iterable of str or mapping of str: DownloadItem
            Value, iterable item or mapping key must be in
            ``{'json', 'package', 'xhtml'}``. `DownloadItem` attributes
            override method parameters for a single file.
        to_dir : str or pathlike, optional
            Directory to save the files.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder ``/name/``
            is always required.
        check_corruption : bool, default True
            Calculate hashes for package files.
        max_concurrent : int, default 5
            Maximum number of simultaneous downloads allowed.
        filename : str, optional
            Full filename for the saved file.

        Raises
        ------
        DownloadErrorGroup of
            CorruptDownloadError
                Parameter `sha256` does not match the calculated hash of
                package.
            requests.HTTPError
                HTTP status error occurs.
            requests.ConnectionError
                Connection fails.

        Warns
        -----
        FileNotAvailableWarning
            Requested file type for this filing is not available.
        """
        downloader.validate_stem_pattern(stem_pattern)
        items = download_specs_construct.construct(
            formats, self, to_dir, stem_pattern, filename, check_corruption,
            self.VALID_DOWNLOAD_FORMATS
            )
        dlset = downloader.download_parallel(
            items, max_concurrent)
        excs = save_paths.assign_all(dlset)
        if excs:
            msg = 'Exceptions raised while downloading.'
            raise DownloadErrorGroup(msg, excs)

    async def download_async_iter(
            self,
            formats: str | Iterable[str] | Mapping[str, DownloadItem],
            to_dir: str | PurePath | None = None,
            stem_pattern: str | None = None,
            check_corruption: bool = True,
            max_concurrent: int = 5
            ) -> AsyncIterator[tuple['Filing', str, Exception | None]]:
        """
        Download files in type or types of `formats`.

        The function follows the same logic as method `download()`. See
        documentation.

        Parameters
        ----------
        formats : str or iterable of str or mapping of str: DownloadItem
            Value, iterable item or mapping key must be in
            ``{'json', 'package', 'xhtml'}``. `DownloadItem` attributes
            override method parameters for a single file.
        to_dir : str or pathlike, optional
            Directory to save the files.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder ``/name/``
            is always required.
        check_corruption : bool, default True
            Calculate hashes for package files.
        max_concurrent : int, default 5
            Maximum number of simultaneous downloads allowed.

        Yields
        ------
        Filing
            Filing object.
        {'json', 'package', 'xhtml'}
            Format name of the download.
        Exception or None
            Possible exception such as `CorruptDownloadError`,
            `requests.HTTPError` or `requests.ConnectionError`.

        Warns
        -----
        FileNotAvailableWarning
            Requested file type for this filing is not available.
        """
        downloader.validate_stem_pattern(stem_pattern)

        items = download_specs_construct.construct(
            formats, self, to_dir, stem_pattern, None,
            check_corruption, Filing.VALID_DOWNLOAD_FORMATS
            )
        dliter = downloader.download_parallel_async_iter(
            items, max_concurrent)
        async for filing, format, result in dliter:
            exc = save_paths.assign_single(filing, format, result)
            yield filing, format, exc

    def _search_entity(
            self, json_frag: dict | EllipsisType,
            entity_iter: Iterable[Entity] | None
            ) -> Entity | None:
        """
        Search for an `Entity` object for the filing.

        Warns
        -----
        ApiReferenceWarning
        """
        if json_frag == Ellipsis or entity_iter is None:
            return None
        if not self.entity_api_id:
            msg = f'No entity defined for {self!r}, api_id='
            warnings.warn(f'{msg}{self.api_id}', ApiReferenceWarning, stacklevel=2)
            return None

        entity = None
        for ent in entity_iter:
            if ent.api_id == self.entity_api_id:
                entity = ent
                entity.filings.add(self)
                break
        if entity is None:
            msg = (
                f'Entity with api_id={self.entity_api_id} not found, '
                f'referenced by {self!r}, api_id={self.api_id}'
                )
            warnings.warn(msg, ApiReferenceWarning, stacklevel=2)
        return entity

    def _search_validation_messages(
            self, json_frag: dict | EllipsisType,
            message_iter: Iterable[ValidationMessage] | None
            ) -> set[ValidationMessage] | None:
        """
        Search `ValidationMessage` objects for this filing.

        Warns
        -----
        ApiReferenceWarning
        """
        if json_frag == Ellipsis or message_iter is None:
            return None

        found_msgs = set()
        msgs_relfrags: list | None = self._json.get(self.VALIDATION_MESSAGES)
        if msgs_relfrags:
            for rel_api_id in (mf['id'] for mf in msgs_relfrags):
                for vmsg in message_iter:
                    if vmsg.api_id == rel_api_id:
                        vmsg.filing_api_id = self.api_id
                        vmsg.filing = self
                        found_msgs.add(vmsg)
                        break
                else:
                    msg = (
                        f'Validation message with api_id={rel_api_id} not '
                        f'found, referenced by {self!r}, api_id={self.api_id}'
                        )
                    warnings.warn(msg, ApiReferenceWarning, stacklevel=2)
        return found_msgs

    def _derive_language(self) -> str | None:
        stem = self._get_package_url_stem()
        if not stem:
            return None

        stem = stem.replace('_', '-')
        last_part = stem.split('-')[-1]
        part_len = len(last_part)
        if (part_len < 2
                or part_len > 3
                or not last_part.isalpha()):
            return None

        last_part = last_part.lower()
        if part_len == 2:
            return last_part
        else:
            return LANG_CODE_TRANSFORM.get(last_part)

    def _derive_reporting_date(self) -> date | None:
        stem = self._get_package_url_stem()
        if not stem:
            return self.last_end_date

        stem = stem.replace('_', '-')
        mt = re.search(r'(^|\D)(\d{4}-\d{1,2}-\d{1,2})($|\D)', stem)
        if mt:
            year, month, day = mt[2].split('-')
            return date(int(year), int(month), int(day))
        return self.last_end_date

    def _get_package_url_stem(self) -> str | None:
        url_path = urllib.parse.urlparse(self.package_url).path
        if not url_path.strip():
            return None
        if isinstance(url_path, bytes):
            url_path = url_path.decode('utf-8')
        file_stem = PurePath(url_path).stem
        if not file_stem.strip():
            return None
        return file_stem
