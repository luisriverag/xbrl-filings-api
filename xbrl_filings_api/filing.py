"""Define `Filing` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import re
import urllib.parse
from collections.abc import AsyncIterator, Iterable, Mapping
from datetime import date, datetime, timedelta
from pathlib import PurePath, PurePosixPath
from typing import ClassVar, Union

import xbrl_filings_api.options as options
from xbrl_filings_api import download_specs_construct, downloader
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import PROTOTYPE, FileStringType, Prototype
from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import _ParseType
from xbrl_filings_api.exceptions import CorruptDownloadError
from xbrl_filings_api.lang_code_transform import LANG_CODE_TRANSFORM
from xbrl_filings_api.validation_message import ValidationMessage

logger = logging.getLogger(__name__)


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
    added_time_str : str or None
    processed_time : datetime or None
    processed_time_str : str or None
    entity_api_id : str or None
    entity : Entity or None
    validation_messages : set of ValidationMessage or None
    json_url : str or None
    package_url : str or None
    viewer_url : str or None
    xhtml_url : str or None
    query_time : datetime
    request_url : str
    json_download_path : str or None
    package_download_path : str or None
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

    VALID_DOWNLOAD_FORMATS: ClassVar[set[str]] = {'json', 'package', 'xhtml'}
    _NOT_NUM_RE = re.compile(r'\D', re.ASCII)
    _DATE_RE = re.compile(
        pattern=r'''
            \b
            (\d{4})                # year part
            -
            (0[1-9]|1[012])        # month part
            -
            (0[1-9]|[12]\d|3[01])  # day part of date
            \b
        ''',
        flags=re.VERBOSE | re.ASCII
        )

    def __init__(
            self,
            json_frag: Union[dict, Prototype],
            api_request: Union[_APIRequest, None] = None,
            entity_iter: Union[Iterable[Entity], None] = None,
            message_iter: Union[Iterable[ValidationMessage], None] = None
            ) -> None:
        """Initialize a `Filing` object."""
        super().__init__(json_frag, api_request)

        self.country: Union[str, None] = self._json.get(self.COUNTRY)
        """
        The country where the filing was reported.

        In case of ESEF this is the country where the filer has issued
        securities on EU regulated markets. The securities are usually
        shares but could be other securities as well such as bonds.
        """

        self.filing_index: Union[str, None] = self._json.get(self.FILING_INDEX)
        """
        Database identifier for the filing.

        The index is structured as:
          1. LEI identifier
          2. Reporting date
          3. Filing system
          4. Country
          5. Entry number (0-based)

        For a correctly submitted filing, the entry number separates the
        different language versions from each other. Sometimes the filer
        also issues the same report more than once to correct the
        mistakes left in the first published version. The greatest entry
        number is the latest published filing.

        The parts are separated by a hyphen. Please note that the
        ISO-style reporting date is also delimited by hyphens.

        The original field name in the API is ``fxo_id``.
        """

        self.language: Union[str, None] = None
        """
        Derived two-letter lower-case language identifier defining the
        language of the filing.

        This code is based primarily on the file name in attribute
        `package_url` and secondarily on `xhtml_url`.

        Three-letter language identifiers are transformed into
        two-letter identifiers for official EU languages.
        """

        self.last_end_date: Union[date, None] = self._json.get(
            self.LAST_END_DATE, _ParseType.DATE)
        """
        The end date of the last period in the marked-up report
        contents.

        This is not always the end date of the primary reporting period
        of the report. The derived field `reporting_date` is more
        reliable for this use case.

        The original field name in the API is ``period_end``.
        """

        self.reporting_date: Union[date, None] = None
        """
        Derived end date of the reporting period.

        This date is based on file name in the attribute `package_url`
        and if it cannot be derived, value in the attribute
        `last_end_date` will be used.

        As `last_end_date` regards only the absolute last recorded fact
        in the report (even if there is only one fact reported for this
        date), it is unreliable regarding filing mistakes and and
        future-bound facts.

        Extracts a valid YYYY-MM-DD date in `package_url` URL stem
        (filename). If multiple dates exist in stem, selects the last
        one.
        """

        self.error_count: Union[str, None] = self._json.get(self.ERROR_COUNT)
        """The count of validation errors listed in
        `validation_messages`."""

        self.inconsistency_count: Union[str, None] = self._json.get(
            self.INCONSISTENCY_COUNT)
        """The count of validation inconsistencies listed in
        `validation_messages`."""

        self.warning_count: Union[str, None] = self._json.get(
            self.WARNING_COUNT)
        """The count of validation warnings listed in
        `validation_messages`."""

        self.added_time: Union[datetime, None] = self._json.get(
            self.ADDED_TIME, _ParseType.DATETIME)
        """
        Timezone-aware datetime when the filing was added to
        filings.xbrl.org index.

        Has an arbitrary delay after the issuer actually filed the
        report at the OAM.

        The original field name in the API is ``date_added``.
        """

        self.added_time_str: Union[str, None] = self._json.get(
            self.ADDED_TIME)
        """
        Original timestamp when the filing was added to filings.xbrl.org
        index.

        Has an arbitrary delay after the issuer actually filed the
        report at the OAM.

        The original field name in the API is ``date_added``.
        """

        self.processed_time: Union[datetime, None] = self._json.get(
            self.PROCESSED_TIME, _ParseType.DATETIME)
        """
        Timezone-aware datetime when the filing was processed for the
        filings.xbrl.org index.

        The original field name in the API is ``processed``.
        """

        self.processed_time_str: Union[str, None] = self._json.get(
            self.PROCESSED_TIME)
        """
        Original timestamp when the filing was processed for the
        filings.xbrl.org index.

        The original field name in the API is ``processed``.
        """

        self.entity_api_id: Union[str, None] = self._get_entity_api_id()
        """`api_id` of Entity object."""

        self.entity: Union[Entity, None] = None
        """
        The entity object of this filing.

        Is available when if GET_ENTITY is set in query function `flags`
        parameter.
        """

        self.validation_messages: Union[set[ValidationMessage], None] = None
        """
        The set of validation message objects of this filing.

        Is available when `flags` parameter contains
        `GET_VALIDATION_MESSAGES`. Not all filings have validation
        messages. Unfortunately too many do have.

        When flag is not set, this attribute is `None`.
        """

        self.json_url: Union[str, None] = self._json.get(
            self.JSON_URL, _ParseType.URL)
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

        self.package_url: Union[str, None] = self._json.get(
            self.PACKAGE_URL, _ParseType.URL)
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

        self.viewer_url: Union[str, None] = self._json.get(
            self.VIEWER_URL, _ParseType.URL)
        """
        URL to a website with an inline XBRL viewer for this report.

        The website features the original XHTML report with ability to
        examine the marked up Inline XBRL facts one at a time. The
        underlying software is called The Open Source Inline XBRL Viewer
        and it is developed by Workiva.

        This file cannot be downloaded.
        """

        self.xhtml_url: Union[str, None] = self._json.get(
            self.XHTML_URL, _ParseType.URL)
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

        self.json_download_path: Union[str, None] = None
        """Local path where `json_url` was downloaded."""

        self.package_download_path: Union[str, None] = None
        """Local path where `package_url` was downloaded."""

        self.xhtml_download_path: Union[str, None] = None
        """Local path where `xhtml_url` was downloaded."""

        self.package_sha256: Union[str, None] = self._json.get(
            self.PACKAGE_SHA256)
        """
        The SHA-256 hash of the report package file.

        Used for checking that the download of `package_url` was
        successful and the report is genuine.

        The original field name in the API is ``sha256``.
        """

        self.entity = self._search_entity(entity_iter, json_frag)
        self.validation_messages = (
            self._search_validation_messages(message_iter, json_frag))

        self._json.close()

        self.language = self._derive_language()
        self.reporting_date = self._derive_reporting_date()

    def __repr__(self) -> str:
        """
        Return string repr of filing.

        If queried with flag `GET_ENTITY`, displays `entity.name`,
        `reporting_date` and `language`. Otherwise displays only
        `filing_index`.
        """
        start = f'{type(self).__name__}('
        if self.entity:
            rrepdate = 'None'
            if self.reporting_date:
                rrepdate = f"date({self.reporting_date.strftime('%Y, %m, %d')})"
            return (
                start + f'entity.name={self.entity.name!r}, '
                f'reporting_date={rrepdate}, '
                f'language={self.language!r})'
                )
        else:
            return start + f'filing_index={self.filing_index!r})'

    def __str__(self) -> str:
        """
        Return filing as a string.

        Text has parts `entity.name`/`filing_index`, `reporting_date`
        and `language` (in square brackets).
        """
        parts = []
        if self.entity:
            if self.entity.name:
                parts.append(self.entity.name)
        if len(parts) == 0 and self.filing_index:
            parts.append(self.filing_index)

        if self.reporting_date:
            parts.append(self._get_simple_filing_date(self.reporting_date))
        if self.language:
            parts.append(f'[{self.language}]')
        return ' '.join(parts)

    def _get_simple_filing_date(self, rdate: date) -> str:
        if rdate.month == 12 and rdate.day == 31:
            return str(rdate.year)
        if rdate.month != (rdate + timedelta(days=1)).month:
            return rdate.strftime('%b-%Y')
        return str(rdate)

    def _derive_language(self) -> Union[str, None]:
        stems = (
            self._get_url_stem(self.package_url),
            self._get_url_stem(self.xhtml_url)
            )
        resolved = None
        for stem in stems:
            if not stem:
                continue

            normstem = stem.replace('_', '-')
            last_part = normstem.split('-')[-1]
            if not last_part.isalpha():
                continue

            part_len = len(last_part)
            last_part = last_part.lower()
            if part_len == 2:  # noqa: PLR2004
                resolved = last_part
                break
            elif part_len == 3:
                resolved = LANG_CODE_TRANSFORM.get(last_part)
                if resolved:
                    break
        resolved = self._correct_common_language_code_mistakes(
            resolved, self.country)
        return resolved

    def _correct_common_language_code_mistakes(
            self, resolved: Union[str, None], country: Union[str, None]
            ) -> Union[str, None]:
        if country == 'CZ' and resolved == 'cz':
            resolved = 'cs'
        if country == 'SE' and resolved == 'se':
            resolved = 'sv'
        if country == 'DK' and resolved == 'dk':
            resolved = 'da'
        if country == 'NO' and resolved in ('nb', 'nn'):
            # Not an actual mistake but specifying Bokmaal or Nynorsk
            # ortography is way too specific
            resolved = 'no'
        return resolved

    def _derive_reporting_date(self) -> Union[date, None]:
        out_dt = self.last_end_date

        stem = self._get_url_stem(self.package_url)
        if not stem:
            return out_dt

        normstem = self._NOT_NUM_RE.sub('-', stem)
        mlist = self._DATE_RE.findall(normstem)
        if mlist:
            year, month, day = mlist[-1]
            try:
                try_dt = date(int(year), int(month), int(day))
            except ValueError:
                # Bad date e.g. 2000-02-31
                pass
            else:
                out_dt = try_dt
        return out_dt

    def download(
            self,
            files: Union[
                FileStringType,
                Iterable[FileStringType],
                Mapping[FileStringType, DownloadItem]
                ],
            to_dir: Union[str, PurePath, None] = None,
            *,
            stem_pattern: Union[str, None] = None,
            check_corruption: bool = True,
            max_concurrent: Union[int, None] = None
            ) -> None:
        """
        Download files of this `Filing` according to `files` parameter.

        The filesystem path of the downloaded file will be saved in the
        `Filing` object attributes {file}_download_path such as
        ``json_download_path`` for the downloaded JSON file.

        If there are ``package`` download definition(s) in the parameter
        `files` and parameter `check_corruption` is True, the downloaded
        package files will be checked through the `package_sha256`
        attribute of `Filing` objects. If this hash attribute does not
        match the one calculated from the downloaded file, an exception
        `CorruptDownloadError` of the first erraneous occurrence will be
        raised after all downloads have finished. The downloaded file(s)
        will not be deleted but the filename(s) will be appended with
        ending ``.corrupt``. However, attributes {file}_download_path
        will not store these corrupt paths.

        The directories in `to_dir` will be created if they do not
        exist. By default, filename is derived from download URL. If the
        file already exists, it will be overwritten.

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

        HTTP request timeout is defined in `options.timeout_sec`.

        Parameters
        ----------
        files : str or iterable of str or mapping of str: DownloadItem
            Value, iterable item or mapping key must be in
            ``{'json', 'package', 'xhtml'}``. `DownloadItem` attributes
            override method parameters for a single file.
        to_dir : str or pathlike, optional
            Directory to save the files. Defaults to working directory.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder ``/name/``
            is always required.
        check_corruption : bool, default True
            Calculate hashes for package files.
        max_concurrent : int or None, default None
            Maximum number of simultaneous downloads allowed. Value
            `None` means unlimited.

        Raises
        ------
        CorruptDownloadError
            Filing attribute `package_sha256` does not match the
            calculated hash of package file.
        requests.HTTPError
            HTTP status error occurs.
        requests.ConnectionError
            Connection fails.
        """
        downloader.validate_stem_pattern(stem_pattern)
        items = download_specs_construct.construct(
            files, self, to_dir, stem_pattern, self.VALID_DOWNLOAD_FORMATS,
            check_corruption=check_corruption
            )
        results = downloader.download_parallel(
            items,
            max_concurrent=max_concurrent,
            timeout=options.timeout_sec
            )
        for result in results:
            if result.path:
                setattr(
                    result.info.obj,
                    f'{result.info.file}_download_path',
                    result.path
                    )
        excs = [
            result.err
            for result in results
            if isinstance(result.err, Exception)
            ]
        for err_i, err in enumerate(excs):
            if isinstance(err, downloader.CorruptDownloadError):
                # Wrap again with FilingsAPIError subclassed exception
                excs[err_i] = CorruptDownloadError(
                    path=err.path,
                    url=err.url,
                    calculated_hash=err.calculated_hash,
                    expected_hash=err.expected_hash
                    )
        if excs:
            raise excs[0]

    async def download_aiter(
            self,
            files: Union[
                FileStringType,
                Iterable[FileStringType],
                Mapping[FileStringType, DownloadItem]
                ],
            to_dir: Union[str, PurePath, None] = None,
            *,
            stem_pattern: Union[str, None] = None,
            check_corruption: bool = True,
            max_concurrent: Union[int, None] = 5
            ) -> AsyncIterator[downloader.DownloadResult]:
        """
        Download files in type or types of `files`.

        The method follows the same logic as `download()`. See
        documentation.

        Parameters
        ----------
        files : str or iterable of str or mapping of str: DownloadItem
            Value, iterable item or mapping key must be in
            ``{'json', 'package', 'xhtml'}``. `DownloadItem` attributes
            override method parameters for a single file.
        to_dir : str or pathlike, optional
            Directory to save the files. Defaults to working directory.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder ``/name/``
            is always required.
        check_corruption : bool, default True
            Calculate hashes for package files.
        max_concurrent : int or None, default 5
            Maximum number of simultaneous downloads allowed. Value
            `None` means unlimited.

        Yields
        ------
        DownloadResult
            Contains information on the finished download.
        """
        downloader.validate_stem_pattern(stem_pattern)

        items = download_specs_construct.construct(
            files, self, to_dir, stem_pattern, self.VALID_DOWNLOAD_FORMATS,
            check_corruption=check_corruption
            )
        dliter = downloader.download_parallel_aiter(
            items,
            max_concurrent=max_concurrent,
            timeout=options.timeout_sec
            )
        async for result in dliter:
            if result.path:
                res_info: DownloadInfo = result.info
                setattr(
                    res_info.obj,
                    f'{res_info.file}_download_path',
                    result.path
                    )
            if isinstance(result.err, downloader.CorruptDownloadError):
                # Wrap again with FilingsAPIError subclassed exception
                err = CorruptDownloadError(
                    path=result.err.path,
                    url=result.err.url,
                    calculated_hash=result.err.calculated_hash,
                    expected_hash=result.err.expected_hash
                    )
                result = downloader.DownloadResult(
                    result.url, result.path, err, result.info)
            yield result

    def open(self, new: int = 0, autoraise: bool = True) -> bool:
        """
        Open the filing on web browser.

        Opens the `viewer_url` if `options.open_viewer` is True
        (default), otherwise opens `xhtml_url`. They are the same
        document except the viewer has a JavaScript Inline XBRL viewer
        to drill into the tagged facts on the document.

        Parameters
        ----------
        new : int, default 0
            Parameter `new` of `webbrowser.BaseBrowser.open()`. `0` for
            the same window, `1` for a new window, `2` for a new tab.
        autoraise : bool, default True
            Parameter `autoraise` of `webbrowser.BaseBrowser.open()`.
            `False` for opening in background.

        Returns
        -------
        bool
            Value returned by `webbrowser.BaseBrowser.open()`.

        Raises
        ------
        ValueError
            If attribute `viewer_url` (or `xhtml_url`) is None or
            `options.browser` is not set.
        """
        file_url = self.viewer_url if options.open_viewer else self.xhtml_url
        if file_url is None:
            attr_name = 'viewer_url' if options.open_viewer else 'xhtml_url'
            msg = f'The attribute "{attr_name}" value is None.'
            raise ValueError(msg)
        if not (isinstance(options.browser, object)
                and callable(getattr(options.browser, 'open', None))):
            msg = (
                'Value options.browser is not webbrowser.BaseBrowser. It is '
                'likely that webbrowser.get() failed and there is no runnable '
                'browser.'
                )
            raise TypeError(msg)
        # Existence of open method is certain
        return options.browser.open( # type: ignore[union-attr]
            url=file_url,
            new=new,
            autoraise=autoraise
            )

    def _search_entity(
            self,
            entity_iter: Union[Iterable[Entity], None],
            json_frag: Union[dict, Prototype]
            ) -> Union[Entity, None]:
        """Search for an `Entity` object for the filing."""
        if json_frag == PROTOTYPE or entity_iter is None:
            return None
        if not self.entity_api_id:
            msg = f'No entity defined for {self!r}, api_id={self.api_id}'
            logger.warning(msg, stacklevel=2)
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
            logger.warning(msg, stacklevel=2)
        return entity

    def _search_validation_messages(
            self,
            message_iter: Union[Iterable[ValidationMessage], None],
            json_frag: Union[dict, Prototype]
            ) -> Union[set[ValidationMessage], None]:
        """Search `ValidationMessage` objects for this filing."""
        if json_frag == PROTOTYPE or message_iter is None:
            return None

        found_msgs = set()
        msgs_relfrags: Union[list, None] = self._json.get(
            self.VALIDATION_MESSAGES)
        if msgs_relfrags:
            for rel_api_id in (mf['id'] for mf in msgs_relfrags):
                if not isinstance(rel_api_id, str):
                    rel_api_id = str(rel_api_id)
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
                    logger.warning(msg, stacklevel=2)
        return found_msgs

    def _get_url_stem(self, url: Union[str, None]) -> Union[str, None]:
        if url is None:
            return None
        presult = None
        try:
            presult = urllib.parse.urlparse(url)
        except ValueError:
            pass
        if (not isinstance(presult, urllib.parse.ParseResult)
                or ':' not in url):
            return None

        url_path = None
        if presult.path.strip():
            url_path = urllib.parse.unquote(presult.path)
        if url_path is None:
            return None

        file_stem = None
        try:
            urlpath = PurePosixPath(url_path)
        except ValueError:
            pass
        else:
            file_stem = urlpath.stem

        if isinstance(file_stem, str) and file_stem.strip():
            return file_stem
        else:
            return None

    def _get_entity_api_id(self) -> Union[str, None]:
        api_id = self._json.get(self.ENTITY_API_ID)
        if api_id is not None and not isinstance(api_id, str):
            api_id = str(api_id)
        return api_id
