"""Define `Filing` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import re
import urllib.parse
import webbrowser
from collections.abc import AsyncIterator, Iterable, Mapping
from datetime import date, datetime, timedelta
from pathlib import PurePath, PurePosixPath
from typing import ClassVar, Optional, Union

from xbrl_filings_api import (
    download_specs_construct,
    downloader,
    options,
)
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import PROTOTYPE, FileStringType, Prototype
from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.exceptions import CorruptDownloadError
from xbrl_filings_api.lang_code_transform import LANG_CODE_TRANSFORM
from xbrl_filings_api.parse_type import ParseType
from xbrl_filings_api.validation_message import ValidationMessage

__all__ = ['Filing']

logger = logging.getLogger(__name__)


class Filing(APIResource):
    """
    XBRL filing in the database based on a report package.

    Different language versions of the same report are separate filings.
    The language versions of the same report share the same
    `filing_index` except for the last integer.
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
            api_request: Optional[APIRequest] = None,
            entity_iter: Optional[Iterable[Entity]] = None,
            message_iter: Optional[Iterable[ValidationMessage]] = None
            ) -> None:
        # Signatures::
        #     Filing(
        #         json_frag: dict,
        #         api_request: APIRequest,
        #         entity_iter: Optional[Iterable[Entity]],
        #         message_iter: Optional[Iterable[ValidationMessage]]
        #         )
        #     Filing(json_frag: Prototype)
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
            self.LAST_END_DATE, ParseType.DATE)
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
            self.ADDED_TIME, ParseType.DATETIME)
        """
        Timezone-aware datetime when the filing was added to the
        database.

        Has an arbitrary delay after the issuer actually filed the
        report at the OAM.

        The original field name in the API is ``date_added``.
        """

        self.added_time_str: Union[str, None] = self._json.get(
            self.ADDED_TIME)
        """
        Original timestamp when the filing was added to the database.

        Has an arbitrary delay after the issuer actually filed the
        report at the OAM.

        The original field name in the API is ``date_added``.
        """

        self.processed_time: Union[datetime, None] = self._json.get(
            self.PROCESSED_TIME, ParseType.DATETIME)
        """
        Timezone-aware datetime when the filing was processed for the
        database.

        The original field name in the API is ``processed``.
        """

        self.processed_time_str: Union[str, None] = self._json.get(
            self.PROCESSED_TIME)
        """
        Original timestamp when the filing was processed for the
        database.

        The original field name in the API is ``processed``.
        """

        self.entity_api_id: Union[str, None] = self._get_entity_api_id()
        """`api_id` of `entity` object."""

        self.entity: Union[Entity, None] = None
        """
        The entity object of this filing.

        The object is available when flag `GET_ENTITY` is set in query
        function parameter ``flags``.
        """

        self.validation_messages: Union[set[ValidationMessage], None] = None
        """
        The set of validation message objects of this filing.

        The object is available when flag `GET_VALIDATION_MESSAGES` is
        set in query function parameter ``flags``. If filing has no
        validation messages, the value is an empty :class:`set`.

        When flag is not set, this attribute is :pt:`None`.
        """

        self.json_url: Union[str, None] = self._json.get(
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

        self.package_url: Union[str, None] = self._json.get(
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

        self.viewer_url: Union[str, None] = self._json.get(
            self.VIEWER_URL, ParseType.URL)
        """
        URL to a website with an inline XBRL viewer for this report.

        The website features the original XHTML report with ability to
        examine the marked up Inline XBRL facts one at a time. The
        underlying software is called The Open Source Inline XBRL Viewer
        and it is developed by Workiva.

        This file cannot be downloaded.
        """

        self.xhtml_url: Union[str, None] = self._json.get(
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

        self.json_download_path: Union[str, None] = None
        """Local path where `json_url` was downloaded."""

        self.package_download_path: Union[str, None] = None
        """Local path where `package_url` was downloaded."""

        self.xhtml_download_path: Union[str, None] = None
        """Local path where `xhtml_url` was downloaded."""

        self.package_sha256: Union[str, None] = self._json.get(
            self.PACKAGE_SHA256)
        """
        The SHA-256 checksum of the report package file.

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
        Return repr of ``api_id`` and other properties.

        If has entity, displays also `Filing.entity.name <Entity.name>`,
        `reporting_date` and `language`.

        Otherwise displays ``api_id`` and `filing_index`.
        """
        start = f'{type(self).__name__}(api_id={self.api_id!r}, '
        if self.entity:
            rrepdate = 'None'
            if self.reporting_date:
                rdate_str = self.reporting_date.strftime('%Y, %m, %d')
                rrepdate = f'date({rdate_str})'
            return (
                start + f'entity.name={self.entity.name!r}, '
                f'reporting_date={rrepdate}, '
                f'language={self.language!r})'
                )
        else:
            return start + f'filing_index={self.filing_index!r})'

    def __str__(self) -> str:
        r"""
        Return "[entity.name/filing_index] [reporting_date] [language]".

        If has entity, the first part is
        `Filing.entity.name <Entity.name>`, otherwise it will be
        `filing_index`.

        Attribute ``reporting_date`` will be displayed in simple format
        and ``language`` in square brackets. Simple format means that
        last day of the year is the sole year (2022-12-31 -> "2022"),
        last day of the month is month-year (2022-01-31 -> "Jan-2022")
        and any other date is in ISO format (2022-01-15 ->
        "2022-01-15").
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
        if rdate.month == 12 and rdate.day == 31: # noqa: PLR2004 # No magic
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
                # Looks like an alpha-2 code, quacks like an alpha-2
                # code
                resolved = last_part
                break
            elif part_len == 3: # noqa: PLR2004
                # Seems like a translatable alpha-3 code
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
        Download file(s) according to parameter ``files``.

        The ``files`` parameter accepts three formats::

            filing.download('json')
            filing.download(['json', 'package'])
            filing.download(
                {'json': DownloadItem(filename='save.json')})

        The filesystem path of the downloaded file will be saved in the
        `Filing` object attributes ``<file>_download_path`` such as
        ``json_download_path`` for the downloaded JSON file.

        If ``package`` file is requested to be downloaded and parameter
        ``check_corruption`` is :pt:`True`, the downloaded package files
        will be checked through the `package_sha256` attribute. If this
        hash attribute does not match the one calculated from the
        downloaded file, an exception
        :exc:`~xbrl_filings_api.exceptions.CorruptDownloadError` is
        raised after all downloads have finished. The downloaded files
        will not be deleted but the filename will be appended with
        ending ".corrupt". However, attribute `package_download_path`
        will not store this corrupt paths.

        The directories in the path of parameter ``to_dir`` will be
        created if they do not exist. By default, filename is derived
        from download URL. If the file already exists, it will be
        overwritten.

        If download is interrupted, the files will be left with ending
        ".unfinished".

        If no name could be derived from the url attribute, the file
        will be named ``file0001``, ``file0002``, etc. In this case a
        new file is always created.

        Parameter ``stem_pattern`` requires a placeholder "/name/".
        For example pattern ``/name/_second_try`` will change original
        filename ``743700XJC24THUPK0S03-2022-12-31-fi.xhtml`` into
        ``743700XJC24THUPK0S03-2022-12-31-fi_second_try.xhtml``. Not
        recommended for packages as their names should not be changed.

        HTTP request timeout is defined in `options.timeout_sec`.

        Parameters
        ----------
        files : str or iterable of str or mapping of {str: DownloadItem}
            The ``str`` value must be in
            ``{'json', 'package', 'xhtml'}``. `DownloadItem` attributes
            override method arguments for the file.
        to_dir : path-like, optional
            Directory to save the files. Defaults to working directory.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder "/name/"
            is always required.
        check_corruption : bool, default True
            Raise
            :exc:`~xbrl_filings_api.exceptions.CorruptDownloadError` for
            a corrupt ``'package'`` file.
        max_concurrent : int or None, default None
            Maximum number of simultaneous downloads allowed. Value
            :pt:`None` means unlimited.

        Raises
        ------
        ~xbrl_filings_api.exceptions.CorruptDownloadError
            When attribute `Filing.package_sha256` does not match the
            calculated hash of ``'package'`` file and
            ``check_corruption`` is :pt:`True`.
        requests.HTTPError
            When HTTP status error occurs.
        requests.ConnectionError
            When connection fails.

        See Also
        --------
        FilingSet.download : For all filings in a `FilingSet`.
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
        Download file(s) and yield `DownloadResult` object(s).

        The method follows the same logic as `download()`. See
        documentation.

        Parameters
        ----------
        files : str or iterable of str or mapping of {str: DownloadItem}
            The ``str`` value must be in
            ``{'json', 'package', 'xhtml'}``. `DownloadItem` attributes
            override method arguments for the file.
        to_dir : path-like, optional
            Directory to save the files. Defaults to working directory.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder "/name/"
            is always required.
        check_corruption : bool, default True
            Raise
            :exc:`~xbrl_filings_api.exceptions.CorruptDownloadError` for
            any corrupt ``'package'`` file.
        max_concurrent : int or None, default 5
            Maximum number of simultaneous downloads allowed. Value
            :pt:`None` means unlimited.

        Yields
        ------
        DownloadResult
            Contains information on the finished download.

        See Also
        --------
        FilingSet.download_aiter : For all filings in a `FilingSet`.
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
            yresult = result
            if yresult.path:
                # Set Filing.<file>_download_path attribute
                res_info: DownloadInfo = yresult.info
                setattr(
                    res_info.obj,
                    f'{res_info.file}_download_path',
                    yresult.path
                    )
            if isinstance(result.err, downloader.CorruptDownloadError):
                # Wrap again with FilingsAPIError subclassed exception
                err = CorruptDownloadError(
                    path=result.err.path,
                    url=result.err.url,
                    calculated_hash=result.err.calculated_hash,
                    expected_hash=result.err.expected_hash
                    )
                yresult = downloader.DownloadResult(
                    yresult.url, yresult.path, err, yresult.info)
            yield yresult

    # Plethora of classes have `open` method despite builtin function
    # (A003).
    # Mirror `BaseBrowser.open` signature without mandated keyword names
    # for booleans (FBT001, FBT002).
    def open( # noqa: A003
            self,
            new: int = 0,
            autoraise: bool = True # noqa: FBT001, FBT002
            ) -> bool:
        """
        Open the filing on web browser.

        Opens the `viewer_url` if `options.open_viewer` is :pt:`True`
        (default), otherwise opens `xhtml_url`. They are the same
        document except the viewer has a JavaScript Inline XBRL viewer
        to drill into the tagged facts on the document.

        Browser can be customized by setting `options.browser` as value
        returned by :func:`webbrowser.get`.

        Parameters
        ----------
        new : int, default 0
            Parameter ``new`` of :meth:`webbrowser.BaseBrowser.open`.
            ``0`` for the same window, ``1`` for a new window, ``2`` for
            a new tab.
        autoraise : bool, default True
            Parameter ``autoraise`` of
            :meth:`webbrowser.BaseBrowser.open`. :pt:`False` for opening
            in background.

        Returns
        -------
        bool
            Value returned by :meth:`webbrowser.BaseBrowser.open`.

        Raises
        ------
        ValueError
            If attribute `viewer_url` (or `xhtml_url`) is :pt:`None`.
        webbrowser.Error
            When `options.browser` is :pt:`None` and no runnable browser
            is present.
        """
        if options.browser is None:
            options.browser = webbrowser.get()

        file_url = self.viewer_url if options.open_viewer else self.xhtml_url
        if file_url is None:
            attr_name = 'viewer_url' if options.open_viewer else 'xhtml_url'
            msg = f'The attribute "{attr_name}" value is None.'
            raise ValueError(msg)

        # Complicated `if` due to test mocking purposes
        if not (isinstance(options.browser, object)
                and callable(getattr(options.browser, 'open', None))):
            msg = 'Value options.browser is not webbrowser.BaseBrowser.'
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
            msg = f'No entity defined for {self!r}'
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
                f'Entity with api_id={self.entity_api_id!r} not found, '
                f'referenced by {self!r}'
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
                match_id = rel_api_id
                if not isinstance(match_id, str):
                    match_id = str(rel_api_id)
                for vmsg in message_iter:
                    if vmsg.api_id == match_id:
                        vmsg.filing_api_id = self.api_id
                        vmsg.filing = self
                        found_msgs.add(vmsg)
                        break
                else:
                    msg = (
                        f'Validation message with api_id={rel_api_id!r} not '
                        f'found, referenced by {self!r}'
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
