"""
Define `FilingSet` class.

This is an extended set type with certain added attributes.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import AsyncIterator, Collection, Iterable, Mapping
from pathlib import Path, PurePath
from typing import Optional, Union

import xbrl_filings_api.options as options
from xbrl_filings_api import (
    database_processor,
    download_specs_construct,
    downloader,
)
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import ResourceLiteralType
from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_VALIDATION_MESSAGES,
    ScopeFlag,
)
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.validation_message import ValidationMessage


class FilingSet(set[Filing]):
    """Set for `Filing` objects.

    The class is an extended set type with certain filing-related
    attributes and functionality.

    Attributes
    ----------
    entities : ResourceCollection
    validation_messages : ResourceCollection
    columns : list of str
    """

    def __init__(self, filings: Optional[Iterable[Filing]] = None) -> None:
        if filings is None:
            super().__init__()
        else:
            super().__init__(filings)
        self.entities = ResourceCollection(self, 'entity', Entity)
        self.validation_messages = ResourceCollection(
            self, 'validation_messages', ValidationMessage)
        self._columns: Union[list[str], None] = None

    def download(
            self,
            files: Union[str, Iterable[str], Mapping[str, DownloadItem]],
            to_dir: Union[str, PurePath, None] = None,
            *,
            stem_pattern: Union[str, None] = None,
            check_corruption: bool = True,
            max_concurrent: Union[int, None] = 5,
            ) -> None:
        """
        Download files in type or types of `files`.

        The directories in `to_dir` will be created if they do not
        exist. By default, filename is derived from download URL. If the
        file already exists, it will be overwritten.

        If parameter `files` includes `package`, the downloaded files
        will be checked through the `package_sha256` attribute of Filing
        objects. If the hash does not match with the one calculated from
        download, exceptions `CorruptDownloadError` after all downloads
        have finished. The downloaded file will not be deleted but its
        name will be appended with ending ``.corrupt``.

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
            Directory to save the files.
        stem_pattern : str, optional
            Pattern to add to the filename stems. Placeholder ``/name/``
            is always required.
        check_corruption : bool, default True
            Calculate hashes for package files.
        max_concurrent : int or None, default 5
            Maximum number of simultaneous downloads allowed. Value
            `None` means unlimited.

        Raises
        ------
        CorruptDownloadError
            Parameter `sha256` does not match the calculated hash of
            package.
        requests.HTTPError
            HTTP status error occurs.
        requests.ConnectionError
            Connection fails.
        """
        downloader.validate_stem_pattern(stem_pattern)

        items = []
        for filing in self:
            items.extend(
                download_specs_construct.construct(
                    files, filing, to_dir, stem_pattern,
                    Filing.VALID_DOWNLOAD_FORMATS,
                    check_corruption=check_corruption
                    ))
        results = downloader.download_parallel(
            items,
            max_concurrent=max_concurrent,
            timeout=options.timeout_sec
            )
        for result in results:
            if result.path:
                res_info: DownloadInfo = result.info
                setattr(
                    res_info.obj,
                    f'{res_info.file}_download_path',
                    result.path
                    )
        excs = [
            result.err for result in results
            if isinstance(result.err, Exception)
            ]
        if excs:
            raise excs[0]

    async def download_aiter(
            self,
            files: Union[str, Iterable[str], Mapping[str, DownloadItem]],
            to_dir: Union[str, PurePath, None] = None,
            *,
            stem_pattern: Union[str, None] = None,
            check_corruption: bool = True,
            max_concurrent: Union[int, None] = 5
            ) -> AsyncIterator[downloader.DownloadResult]:
        """
        Download files in type or types of `files`.

        The function follows the same logic as method `download()`. See
        documentation.

        Parameters
        ----------
        files : str or iterable of str or mapping of str: DownloadItem
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
        max_concurrent : int or None, default 5
            Maximum number of simultaneous downloads allowed. Value
            `None` means unlimited.

        Yields
        ------
        DownloadResult
            Contains information on the finished download.
        """
        downloader.validate_stem_pattern(stem_pattern)

        items = []
        for filing in self:
            items.extend(
                download_specs_construct.construct(
                    files, filing, to_dir, stem_pattern,
                    Filing.VALID_DOWNLOAD_FORMATS,
                    check_corruption=check_corruption
                    ))
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
            yield result

    def to_sqlite(
            self,
            path: Union[str, Path],
            *,
            update: bool = False,
            flags: ScopeFlag = GET_ENTITY | GET_VALIDATION_MESSAGES
            ) -> None:
        """
        Save set to an SQLite3 database.

        The method has the same signature and follows the same rules as
        `to_sqlite()` with the exception of missing parameters
        `filters`, `sort`, `max_size` and `add_api_params`. See
        documentation.

        Flags also default to all tables turned on. If no additional
        information is present in the set, the tables will not be
        created if they do not exist.

        Parameters
        ----------
        path or Path
            Path to the SQLite database.
        update : bool, default False
            If the database already exists, update it with these
            records. Old records are updated and new ones are added.
        flags : ScopeFlag, default GET_ENTITY | GET_VALIDATION_MESSAGES
            Scope of saving. Flag `GET_ENTITY` will save entity records
            of filings and `GET_VALIDATION_MESSAGES` the validation
            messages.

        Raises
        ------
        DatabaseFileExistsError
            When ``update=False``, if the intended save path for the
            database is an existing file.
        DatabasePathIsReservedError
            The intended save path for the database is already reserved
            by a non-file database object.
        DatabaseSchemaUnmatchError
            When ``update=True``, if the file contains a database whose
            schema does not match the expected format.
        sqlite3.DatabaseError
            When ``update=True``, if the file is not a database
            (``err.sqlite_errorname='SQLITE_NOTADB'``) etc.
        """
        ppath = path if isinstance(path, Path) else Path(path)

        data_objs, flags = self._get_data_sets(flags)

        database_processor.sets_to_sqlite(
            flags, ppath, data_objs, update=update)

    def get_pandas_data(
            self, attr_names: Optional[Iterable[str]] = None
            ) -> dict[str, list[ResourceLiteralType]]:
        """
        Get data for `pandas.DataFrame` constructor for filings.

        A new dataframe can be instantiated by::

            pandas.DataFrame(data=filingset.get_pandas_data())

        If `attr_names` is not given, most data attributes will be
        extracted. Attributes ending in ``_download_path`` will be
        extracted only if at least one file of this type has been
        downloaded and `entity_api_id` if there is at least one entity
        object in the set.

        Parameters
        ----------
        attr_names: iterable of str, optional
            Valid attributes names of `Filing` object.

        Returns
        -------
        dict of str: list of ResourceLiteralType
            Column names are the same as the attributes for resource of
            this type.
        """
        data: dict[str, list[ResourceLiteralType]]
        if attr_names:
            data = {col: [] for col in attr_names}
        else:
            data = {col: [] for col in self.columns}
        for filing in self:
            for col_name in data:
                data[col_name].append(getattr(filing, col_name))
        return data

    def _get_data_sets(
            self, flags: ScopeFlag
            ) -> tuple[dict[str, Collection[APIResource]], ScopeFlag]:
        """Get sets of data objects and disable flags for empty sets."""
        data_objs: dict[str, Collection[APIResource]] = {'Filing': self}
        subresources = [
            (Entity, self.entities),
            (ValidationMessage, self.validation_messages)
            ]
        type_obj: type[APIResource]
        obj_set: ResourceCollection
        for type_obj, obj_set in subresources:
            if not obj_set.exist:
                flags &= ~type_obj._FILING_FLAG
            else:
                data_objs[type_obj.__name__] = obj_set
        return data_objs, flags

    @property
    def columns(self) -> list[str]:
        """List of available columns for filings of this set."""
        if self._columns:
            return self._columns
        self._columns = Filing.get_columns(
            filings=self,
            has_entities=self.entities.exist
            )
        return self._columns
