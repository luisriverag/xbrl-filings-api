"""
Define `FilingSet` class.

This is an extended set type with certain added attributes.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import copy
from collections.abc import AsyncIterator, Collection, Iterable, Mapping
from datetime import date, datetime
from pathlib import Path, PurePath
from typing import Any, Optional, Union

from xbrl_filings_api import (
    database_processor,
    download_specs_construct,
    downloader,
    options,
)
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import DataAttributeType, FileStringType
from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import ScopeFlag
from xbrl_filings_api.exceptions import CorruptDownloadError
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.validation_message import ValidationMessage

__all__ = ['FilingSet']


class FilingSet(set[Filing]):
    r"""Subclassed :class:`set` for `Filing` objects.

    Can be initialized with the single argument being a iterable of
    `Filing` objects.

    The class is an extended set type with certain filing-related
    attributes and methods.

    Support for all set operations and other methods of the ``set``
    class are implemented. It is possible to mix filing sets from
    different queries into a single ``FilingSet`` without redundant
    copies. Due to cross-referencing, the operations returning a new set
    (e.g. `union` method and ``|`` operator) always deep copy all
    objects to the results set. The in-place operations (e.g. `update`
    method and ``|=`` operator) retain the objects from the left set but
    deep copy everything from the right set. If working with large sets,
    it is recommended to use in-place operations over new set
    operations.

    Defines operators ``|``, ``|=``, ``&``, ``&=``, ``-``, ``-=``,
    ``^``, and ``^=``.

    `Filing` objects, as subclass of `APIResource`, have a custom
    `__hash__() <APIResource.__hash__>` method and their hash is based
    on a tuple of strings 'APIResource',
    `Filing.TYPE <APIResource.TYPE>`, and
    `Filing.api_id <APIResource.api_id>`. This means that equality
    checks (``==`` operator) and related methods are based on this
    tuple. For example, when the actual filing object is not available,
    the fastest way to check if a filing with ``api_id`` '123' is
    included in the filing set ``fs`` is::

        ('APIResource', Filing.TYPE, '123') in fs

    Same applies for `ResourceCollection` in attributes
    `entities` and `validation_messages`. These collections are,
    however, lazy iterators.
    """

    def __init__(self, filings: Optional[Iterable[Filing]] = None) -> None:
        """
        Initialize `FilingSet`.

        Parameters
        ----------
        filings : iterable of Filing, optional
            Initial filings.
        """
        if filings is None:
            super().__init__()
        else:
            if not isinstance(filings, FilingSet):
                for filing in filings:
                    if not isinstance(filing, Filing):
                        msg = 'All iterable items must be Filing objects.'
                        raise ValueError(msg)
            super().__init__(filings)

        self.entities = ResourceCollection(self, 'entity', Entity)
        """
        Lazy iterator for entity references in filings.

        See documentation for `ResourceCollection` class.
        """

        self.validation_messages = ResourceCollection(
            self, 'validation_messages', ValidationMessage)
        """
        Lazy iterator for validation message references in filings.

        See documentation for `ResourceCollection` class.
        """

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
            max_concurrent: Union[int, None] = 5,
            ) -> None:
        """
        Download files according to parameter ``files``.

        The ``files`` parameter accepts three formats::

            fs.download('json')
            fs.download(['json', 'package'])
            fs.download({
                    'json': DownloadItem(),
                    'package': DownloadItem(to_dir=other_dir)
                }, to_dir)

        The filesystem path of the downloaded file will be saved in the
        `Filing` object attributes ``<file>_download_path`` such as
        ``json_download_path`` for the downloaded JSON file.

        If ``package`` files are requested to be downloaded and
        parameter ``check_corruption`` is :pt:`True`, the downloaded
        package files will be checked through the `package_sha256`
        attribute. If these attribute values do not match the ones
        calculated from the downloaded files, an exception
        :exc:`~xbrl_filings_api.exceptions.CorruptDownloadError` of the
        first corrupt file is raised after all downloads have finished.
        The downloaded files will not be deleted but the filenames will
        be appended with ending ".corrupt". However, attributes
        `Filing.package_download_path` will not store these corrupt
        paths.

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
            any corrupt ``'package'`` file.
        max_concurrent : int or None, default 5
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
        Filing.download : For a single filing.
        """
        downloader.validate_stem_pattern(stem_pattern)

        items = []
        for filing in self:
            items.extend(
                download_specs_construct.construct(
                    files, filing, to_dir, stem_pattern,
                    Filing.VALID_DOWNLOAD_FORMATS,
                    check_corruption=check_corruption,
                    isfilingset=True
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
        Download files and yield `DownloadResult` objects.

        The function follows the same logic as method `download()`. See
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
        Filing.download_aiter : For a single filing.
        """
        downloader.validate_stem_pattern(stem_pattern)

        items = []
        for filing in self:
            items.extend(
                download_specs_construct.construct(
                    files, filing, to_dir, stem_pattern,
                    Filing.VALID_DOWNLOAD_FORMATS,
                    check_corruption=check_corruption,
                    isfilingset=True
                    ))
        dliter = downloader.download_parallel_aiter(
            items,
            max_concurrent=max_concurrent,
            timeout=options.timeout_sec
            )
        async for result in dliter:
            yresult = result
            if yresult.path:
                res_info: DownloadInfo = yresult.info
                setattr(
                    res_info.obj,
                    f'{res_info.file}_download_path',
                    yresult.path
                    )
            orig_err = yresult.err
            if isinstance(orig_err, downloader.CorruptDownloadError):
                # Wrap again with FilingsAPIError subclassed exception
                err = CorruptDownloadError(
                    path=orig_err.path,
                    url=orig_err.url,
                    calculated_hash=orig_err.calculated_hash,
                    expected_hash=orig_err.expected_hash
                    )
                yresult = downloader.DownloadResult(
                    yresult.url, yresult.path, err, yresult.info)
            yield yresult

    def to_sqlite(
            self,
            path: Union[str, Path],
            *,
            update: bool = False,
            flags: ScopeFlag = (
                ScopeFlag.GET_ENTITY
                | ScopeFlag.GET_VALIDATION_MESSAGES)
            ) -> None:
        """
        Save set to an SQLite3 database.

        The method has the same signature and follows the same rules as
        the query function :func:`~xbrl_filings_api.query.to_sqlite`
        with the exception of missing all query parameters.

        Flags also default to all tables turned on. If no additional
        information is present in the set, the tables will not be
        created if they do not exist.

        Parameters
        ----------
        path : path-like
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
        FileExistsError
            When ``update`` is :pt:`False` and the intended save path
            for the database is an existing file.
        DatabaseSchemaUnmatchError
            When ``update`` is :pt:`True` and the file contains a
            database whose schema does not match the expected format.
        sqlite3.DatabaseError
            For example when ``update`` is :pt:`True` and the file is
            not a database etc.

        See Also
        --------
        xbrl_filings_api.to_sqlite : Query and save to SQLite.
        """
        ppath = path if isinstance(path, Path) else Path(path)

        data_objs, flags = self._get_data_sets(flags)

        database_processor.sets_to_sqlite(
            flags, ppath, data_objs, update=update)

    def get_pandas_data(
            self, attr_names: Optional[Iterable[str]] = None, *,
            with_entity: bool = False, strip_timezone: bool = True,
            date_as_datetime: bool = True, include_urls : bool = False,
            include_paths : bool = False
            ) -> dict[str, list[DataAttributeType]]:
        """
        Get filings as data for :class:`pandas.DataFrame` constructor.

        A new dataframe can be instantiated by::

            import pandas as pd
            df = pd.DataFrame(data=filingset.get_pandas_data())

        If parameter ``attr_names`` is not given, data attributes
        excluding ones ending ``_date_str`` will be extracted.
        Attributes ending in ``_download_path`` will be extracted only
        if at least one file of this type has been downloaded (and
        ``include_paths`` is :pt:`True`) and `entity_api_id` if there is
        at least one entity object in the set and parameter
        ``with_entity`` is :pt:`False`.

        Parameters
        ----------
        attr_names : iterable of str, optional
            Valid attributes names of `Filing` object or ``entity.``
            prefixed attributes of its `Entity` object.
        with_entity : bool, default False
            When parameter ``attr_names`` is not given, include entity
            attributes to the filing.
        strip_timezone : bool, default True
            Strip timezone information (always UTC) from
            :class:`~datetime.datetime` values.
        date_as_datetime : bool, default True
            Convert :class:`~datetime.date` values to naive
            :class:`~datetime.datetime` to be converted to
            :class:`pandas.datetime64` by pandas.
        include_urls : bool, default False
            When parameter ``attr_names`` is not given, include
            attributes ending ``_url``.
        include_paths : bool, default False
            When parameter ``attr_names`` is not given, include
            attributes ending ``_path``.

        Returns
        -------
        data : dict of {str: list of DataAttributeType}
            Column names are the same as the attributes for resource of
            this type.

        See Also
        --------
        ResourceCollection.get_pandas_data : For other resources.
        """
        data: dict[str, list[DataAttributeType]]
        if attr_names:
            data = {col: [] for col in attr_names}
        else:
            data = {col: [] for col in self.columns}
            if with_entity:
                if 'entity_api_id' in data:
                    del data['entity_api_id']
                ent_cols: dict[str, list[DataAttributeType]] = {
                    f'entity.{col}': [] for col in self.entities.columns}
                data.update(ent_cols)
            if not include_urls:
                url_cols = [col for col in data if col.endswith('_url')]
                for col in url_cols:
                    del data[col]
            if not include_paths:
                path_cols = [col for col in data if col.endswith('_path')]
                for col in path_cols:
                    del data[col]
        for filing in self:
            for col_name in data:
                val: DataAttributeType = None
                if col_name.startswith('entity.'):
                    if filing.entity:
                        val = getattr(filing.entity, col_name[7:])
                else:
                    val = getattr(filing, col_name)
                if strip_timezone and isinstance(val, datetime):
                    val = val.replace(tzinfo=None)
                if (date_as_datetime
                        and isinstance(val, date)
                        and type(val) is not datetime):
                    val = datetime.fromordinal(val.toordinal())
                data[col_name].append(val)
        return data

    def pop_duplicates(
            self, languages: Union[Iterable[str], None] = ['en'], *,
            use_reporting_date: bool = False, all_markets: bool = False
            ) -> 'FilingSet':
        """
        Pops duplicates of the same enclosure from the set of filings.

        Entities must be available on the `FilingSet`.

        The method searches the ``FilingSet`` and leaves only one filing
        for each group of same `entity_api_id`, `last_end_date` pairs,
        i.e., one filing for each unique enclosure of the same entity
        for the same financial period. If parameter
        ``use_reporting_date`` is :pt:`True`, grouping is based on
        ``entity_api_id``, `reporting_date` instead.

        Some entities report on multiple markets. If all these
        country-specific filings are wished to retain, set parameter
        ``all_markets`` as :pt:`True`. Grouping will then also include
        `country` as the last item.

        The selected filing from the group is chosen primarily on
        ``languages`` parameter values matched on the `Filing.language`
        attribute. Parameter value ``['sv', 'fi']`` thus means that
        Swedish filings are preferred, secondarily Finnish, and lastly
        the ones which have language as :pt:`None`. Value :pt:`None` can
        be used in the iterable as well. Parameter value :pt:`None`
        means no language preference.

        If there are more than one filing for the language match (or
        ``language`` is :pt:`None`), the filings will be ordered based
        on their `filing_index` and the last one is chosen which is
        practically the one with highest filing number part of
        ``filing_index``.

        Parameters
        ----------
        languages : iterable of str or None, default ['en']
            Preferred languages for the retained filing.
        use_reporting_date : bool, default False
            Use `reporting_date` instead of `last_end_date` when
            grouping.
        all_markets : bool, default False
            Append `country` as the last item in grouping.

        Returns
        -------
        FilingSet
            The set of removed filings.
        """
        if not self.entities.exist:
            msg = 'Entities must be available on the FilingSet'
            raise ValueError(msg)
        if languages is None:
            langs = [None]
        else:
            # Expected type Iterable[None] ?
            langs = list(languages) # type: ignore[arg-type]
        if not any(lan is None for lan in langs):
            langs.append(None)

        enclosures: dict[str, set[Filing]] = {}
        for filing in self:
            key = f'{filing.entity_api_id}'
            if use_reporting_date:
                key += f':{filing.reporting_date}'
            else:
                key += f':{filing.last_end_date}'
            if all_markets:
                key += f':{filing.country}'

            if enclosures.get(key):
                enclosures[key].add(filing)
            else:
                enclosures[key] = {filing}

        popped: set[Filing] = set()
        for enc_filings in enclosures.values():
            # Select correct language filing to be retained
            retain_filing: Union[Filing, None] = None
            for lan in langs:
                lang_filings: set[Filing] = set(filter(
                    lambda f: f.language == lan, enc_filings))
                retain_filing = (
                    self._get_last_filing_index_filing(lang_filings))
                if retain_filing:
                    break
            else:
                # Fallback if no preferred language or None matches
                retain_filing = self._get_last_filing_index_filing(enc_filings)
            # Add the rest to be returned and remove popped from self
            for filing in enc_filings:
                if filing is not retain_filing:
                    popped.add(filing)
        # Execute pop
        self.difference_update(popped)
        return FilingSet(popped)

    def _get_last_filing_index_filing(
            self, filings: set[Filing]
            ) -> Union[Filing, None]:
        if len(filings) == 0:
            return None
        str_indexes = [
            '' if f.filing_index is None else f.filing_index
            for f in filings
            ]
        max_filing_index = max(str_indexes)
        def filter_filing_index_str(filing: Filing) -> bool:
            ismatch = filing.filing_index == max_filing_index
            if not ismatch and max_filing_index == '':
                ismatch = filing.filing_index is None
            return ismatch
        return next(filter(filter_filing_index_str, filings))

    def _get_data_sets(
            self, flags: ScopeFlag
            ) -> tuple[dict[str, Collection[APIResource]], ScopeFlag]:
        """Get sets of data objects and disable flags for empty sets."""
        data_objs: dict[str, Collection[APIResource]] = {'Filing': self}
        subresources = [
            (
                Entity,
                self.entities,
                ScopeFlag.GET_ENTITY
            ), (
                ValidationMessage,
                self.validation_messages,
                ScopeFlag.GET_VALIDATION_MESSAGES
            )]
        type_obj: type[APIResource]
        obj_set: ResourceCollection
        for type_obj, obj_set, type_flag in subresources:
            if not obj_set.exist:
                flags &= ~type_obj._FILING_FLAG
            elif type_flag in flags:
                data_objs[type_obj.__name__] = obj_set
        if flags == ScopeFlag(0):
            flags = ScopeFlag.GET_ONLY_FILINGS
        return data_objs, flags

    @property
    def columns(self) -> list[str]:
        """List of available columns for filings of this set."""
        return Filing.get_columns(
            filings=self,
            has_entities=self.entities.exist
            )

    def _check_arg_iters(self, args) -> None:
        for arg in args:
            if not isinstance(arg, Iterable):
                msg = f'{type(arg).__name__!r} object is not iterable'
                raise TypeError(msg)
            if any(not isinstance(item, Filing) for item in arg):
                msg = 'Arguments must be iterables of Filing objects.'
                raise ValueError(msg)

    def _deepcopy_filing_with_vmessages(self, source: Filing) -> Filing:
        """
        Deep copy Filing and its `validation_messages`.

        Retain `entity` reference without copying.
        """
        orig_entity = source.entity
        source.entity = None
        new = copy.deepcopy(source)
        source.entity = new.entity = orig_entity
        return new

    def _deepcopy_entity(self, source: Entity) -> Entity:
        """Deep copy Entity and shallow copy its `filings`."""
        orig_filings = source.filings
        source.filings = set()
        new = copy.deepcopy(source)
        source.filings = orig_filings
        new.filings = orig_filings.copy()
        return new

    def _deepcopy_filingset_contents(self, fs: 'FilingSet'):
        new_filings = [self._deepcopy_filing_with_vmessages(f) for f in fs]
        fs.clear()
        set.update(fs, new_filings)
        ents = list(fs.entities) # Freeze lazy collection
        for ent in ents:
            new_ent = self._deepcopy_entity(ent) # type: ignore[arg-type]
            new_ent_filings: set[Filing] = set()
            # Type of `filings` is `set[object]` due to cross-references
            for filing in new_ent.filings:
                match_id = filing.api_id # type: ignore[attr-defined]
                new_filing = next(f for f in fs if f.api_id == match_id)
                new_ent_filings.add(new_filing)
                new_filing.entity = new_ent
            new_ent.filings = new_ent_filings # type: ignore[assignment]

    # Superclass operations

    def _union(
            self, fs: 'FilingSet', others: tuple[Iterable[Filing], ...],
            *, isedit: bool) -> None:
        if not isedit:
            self._deepcopy_filingset_contents(fs)
        for fs_arg in others:
            for filing in fs_arg:
                fs.add(filing)

    def union( # type: ignore[override]
            self, *others: Iterable[Filing]) -> 'FilingSet':
        """Return union FilingSet and update cross-references."""
        self._check_arg_iters(others)
        fs = FilingSet(self)
        self._union(fs, others, isedit=False)
        return fs

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __or__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Return method `union` result for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.union(other)

    def update(self, *others: Iterable[Filing]) -> None:
        """Apply union in self and update cross-references."""
        self._check_arg_iters(others)
        self._union(self, others, isedit=True)

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __ior__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Apply method `update` for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        self.update(other)
        return self

    def _intersection(
            self, fs: 'FilingSet', others: tuple[Iterable[Filing], ...], *,
            isedit: bool) -> None:
        if not isedit:
            self._deepcopy_filingset_contents(fs)
        id_differs = {filing: True for filing in self}
        for fs_arg in others:
            for filing in fs_arg:
                if filing in id_differs:
                    id_differs[filing] = False
        for filing, differs in id_differs.items():
            if differs:
                fs.remove(filing)

    def intersection( # type: ignore[override]
            self, *others: Iterable[Filing]) -> 'FilingSet':
        """Return intersection FilingSet and update cross-references."""
        self._check_arg_iters(others)
        fs = FilingSet(self)
        self._intersection(fs, others, isedit=False)
        return fs

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __and__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Return method `intersection` result for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.intersection(other)

    def intersection_update(self, *others: Iterable[Filing]) -> None:
        """Apply intersection in self and update cross-references."""
        self._check_arg_iters(others)
        self._intersection(self, others, isedit=True)

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __iand__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Apply method `intersection_update` for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        self.intersection_update(other)
        return self

    def _difference(
            self, fs: 'FilingSet', others: tuple[Iterable[Filing], ...], *,
            isedit: bool) -> None:
        if not isedit:
            self._deepcopy_filingset_contents(fs)
        for fs_arg in others:
            for filing in fs_arg:
                fs.discard(filing)

    def difference( # type: ignore[override]
            self, *others: Iterable[Filing]) -> 'FilingSet':
        """Return difference FilingSet and update cross-references."""
        self._check_arg_iters(others)
        fs = FilingSet(self)
        self._difference(fs, others, isedit=False)
        return fs

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __sub__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Return method `difference` result for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.difference(other)

    def difference_update(self, *others: Iterable[Filing]) -> None:
        """Apply difference to self and update cross-references."""
        self._check_arg_iters(others)
        self._difference(self, others, isedit=True)

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __isub__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Apply method `difference_update` for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        self.difference_update(other)
        return self

    def _symmetric_difference(
            self, fs: 'FilingSet', other: Iterable[Filing], *, isedit: bool
            ) -> None:
        if not isedit:
            self._deepcopy_filingset_contents(fs)
        id_other_differs = {filing: True for filing in other}
        for filing in other:
            if filing in fs:
                fs.discard(filing)
                id_other_differs[filing] = False
        for filing, other_differs in id_other_differs.items():
            if other_differs:
                fs.add(filing)

    def symmetric_difference( # type: ignore[override]
            self, other: Iterable[Filing]) -> 'FilingSet':
        """Return symmetric difference and update cross-references."""
        self._check_arg_iters([other])
        fs = FilingSet(self)
        self._symmetric_difference(fs, other, isedit=False)
        return fs

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __xor__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Return method `symmetric_difference` result for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    def symmetric_difference_update(self, other: Iterable[Filing]) -> None:
        """Apply symmetric difference in self and update cross-refs."""
        self._check_arg_iters([other])
        self._symmetric_difference(self, other, isedit=True)

    # Any = types.NotImplementedType (n/a in Py3.9)
    def __ixor__( # type: ignore[override]
            self, other: Iterable[Filing]) -> Union['FilingSet', Any]:
        """Apply method `symmetric_difference_update` for iterables."""
        if not isinstance(other, Iterable):
            return NotImplemented
        self.symmetric_difference_update(other)
        return self

    def add(self, elem: Filing) -> None:
        """Add and update cross-references."""
        if not isinstance(elem, Filing):
            msg = 'FilingSet can only contain Filing objects'
            raise TypeError(msg)
        if elem in self:
            return
        new_elem = self._deepcopy_filing_with_vmessages(elem)
        if elem.entity_api_id:
            id_ent = elem.entity_api_id
            ent_existing: Union[Entity, None] = next(
                (e for e in self.entities # type: ignore[misc]
                 if e.api_id == id_ent),
                None
                )
            if ent_existing:
                ent_existing.filings.add(new_elem)
                new_elem.entity = ent_existing
        super().add(new_elem)

    def discard(self, elem: Filing) -> None:
        """Discard and update cross-references."""
        try:
            self.remove(elem)
        except KeyError:
            pass

    def remove(self, elem: Filing) -> None:
        """Remove and update cross-references."""
        if not isinstance(elem, Filing):
            msg = repr(elem)
            raise KeyError(msg)
        id_filing = elem.api_id
        match_elem = next((f for f in self if f.api_id == id_filing), None)
        if not match_elem:
            msg = repr(elem)
            raise KeyError(msg)
        if match_elem and match_elem.entity:
            match_elem.entity.filings.remove(match_elem)
        super().remove(match_elem)

    def pop(self) -> Filing:
        """Pop and update cross-references."""
        elem = super().pop()
        if elem.entity:
            elem.entity.filings.remove(elem)
        return elem

    def copy(self):
        """Return new FilingSet."""
        return FilingSet(self)

    def __repr__(self) -> str:
        """
        Return repr with `len()` of self, entities, validation_messages.

        Values len(`entities`) and len(`validation_messages`) are only
        shown if more than zero are present.
        """
        subreslist = ''
        if self.entities.exist:
            subreslist += f', len(entities)={len(self.entities)}'
        if self.validation_messages.exist:
            subreslist += (
                f', len(validation_messages)={len(self.validation_messages)}')
        return (
            f'{type(self).__name__}('
            f'len(self)={len(self)}{subreslist})'
            )
