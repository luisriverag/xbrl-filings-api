"""
Define default views for SQLite output.

See full documentation for views in attribute `SQLiteView.doc`.

SQL Views
---------
ViewNumericErrors
    Examine summation errors and duplicate errors in filings.
ViewEnclosure
    Examine multi-language enclosures in an easy to read listing.
ViewFilingAge
    Examine the age of the data on the filings.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from xbrl_filings_api.sqlite_view import SQLiteView

DEFAULT_VIEWS = [
    SQLiteView(
        name='ViewNumericErrors',
        required_tables=('ValidationMessage', 'Entity'),
        doc="""
        Examine summation errors and duplicate errors in filings.

        The purpose of this view is to reduce the set of validation
        messages to the ones most relevant from an accounting
        reliability perspective.

        Ordered starting from the most severe error based on
        ``errorPercent``. The last rows are typically rounding errors.

        A summation error arises in the filing when the reported data
        points and reported calculation tree (calculation linkbase) do
        not match. A duplicate errors arises when there is one data
        point which is reported twice (e.g. net income on income
        statement and cash flow statement) but with different values.

        The view only takes into account one language version of a
        single accounting disclosure. It is assumed that all language
        versions contain the same data but only language of the report
        differs. It is customary that entities reporting in ESEF format
        report in the language of their domicile and English. Selected
        language is NULL or the first occurrence in an alphabetically
        ordered list. It is assumed that filings are part of the same
        enclosure when they have the same entity ``api_id`` and
        ``reporting_date``.

        Duplicate errors are reported twice in the data but these
        duplicates are reported only once in the view. A serious caveat
        for duplicates is that the source data does not report the line
        item element name. Duplicates are matched solely based on their
        numeric values in the same filing and thus there could be two
        different line items which have been both reported twice and
        with the exact same numeric values. This is also true with
        regards to reporting periods for the same line item (in other
        words, for a data point).

        Columns
        -------
        entity_name : TEXT or NULL
            Name of the entity from column ``Entity.name``.
        reporting_date : TEXT or NULL
            Reporting date of the enclosure from column
            ``Filing.reporting_date``.
        problem : 'calc' or 'duplicate'
            Type of matched validation message(s), 'calc' for summation
            errors and 'duplicate' for duplicate errors.
        reportedK : REAL or NULL
            Column ``ValidationMessage.calc_reported_sum`` for
            problem='calc' or ``ValidationMessage.duplicate_lesser``
            for problem='duplicate' in thousands.
        computedOrDuplicateK : REAL or NULL
            Column ``ValidationMessage.calc_computed_sum`` for
            problem='calc' or ``ValidationMessage.duplicate_greater``
            for problem='duplicate' in thousands.
        reportedErrorK : REAL or NULL
            Deviation from properly calculated value or the value of the
            other duplicate in thousands.
        errorPercent : REAL or NULL
            Percentage of error `reportedErrorK` based on reported value
            or lesser duplicate.
        calc_line_item : TEXT or NULL
            Line item element name from
            ``ValidationMessage.calc_line_item`` for problem='calc'.
        calc_short_role : TEXT or NULL
            Short linkrole name (name of financial statement) from
            ``ValidationMessage.calc_short_role`` for problem='calc'.
        calc_context_id : TEXT or NULL
            Context ID of XBRL fact from
            ``ValidationMessage.calc_context_id`` for problem='calc'.
        language : TEXT or NULL
            Language of the filing from ``Filing.language``.
        filing_api_id : TEXT
            Column ``Filing.api_id``.
        entity_api_id : TEXT
            Column ``Entity.api_id``.
        validation_message_api_id : TEXT
            Column ``ValidationMessage.api_id``.
        """,
        sql="""
-- Eliminate redundant language versions of the same enclosure in 'fs'
WITH fs AS (
  SELECT
    name AS entity_name,
    reporting_date,
    language,
    Filing.api_id,
    entity_api_id,
    row_number() OVER (
      PARTITION BY entity_api_id, reporting_date ORDER BY language
    ) AS lan_order
  FROM Filing
    JOIN Entity ON Entity.api_id = entity_api_id
),
-- Eliminate redundant duplicate messages for the same fact values in 'v'
v AS (
  SELECT
    filing_api_id,
    duplicate_lesser AS lesser,
    duplicate_greater AS greater,
    code,
    api_id AS validation_message_api_id,
    row_number() OVER (
      PARTITION BY duplicate_greater, duplicate_lesser
    ) AS dup_occur
  FROM ValidationMessage
)
-- Duplicate errors
SELECT * FROM (
  SELECT
    entity_name,
    reporting_date,
    'duplicate' AS problem,
    lesser/1000 AS reportedK,
    greater/1000 AS computedOrDuplicateK,
    (greater-lesser)/1000 AS reportedErrorK,
    round(100*abs((greater-lesser)/lesser), 2) AS errorPercent,
    NULL AS calc_line_item,
    NULL AS calc_short_role,
    NULL AS calc_context_id,
    language,
    filing_api_id,
    entity_api_id,
    validation_message_api_id
  FROM fs INNER JOIN v ON filing_api_id = fs.api_id
  WHERE
    dup_occur = 1
    AND lan_order = 1
    AND code = 'message:tech_duplicated_facts1'

  UNION ALL

-- Summation errors
  SELECT
    entity_name,
    reporting_date,
    'calc' AS problem,
    calc_reported_sum/1000 AS reportedK,
    calc_computed_sum/1000 AS computedOrDuplicateK,
    abs(calc_reported_sum-calc_computed_sum)/1000 AS reportedErrorK,
    round(
      100*abs((calc_reported_sum-calc_computed_sum)/calc_reported_sum), 2
    ) AS errorPercent,
    calc_line_item,
    calc_short_role,
    calc_context_id,
    language,
    filing_api_id,
    entity_api_id,
    ValidationMessage.api_id AS validation_message_api_id
  FROM fs
    JOIN ValidationMessage ON filing_api_id = fs.api_id
  WHERE lan_order = 1 AND code = 'xbrl.5.2.5.2:calcInconsistency'
)
ORDER BY errorPercent DESC NULLS FIRST
"""
        ),
    SQLiteView(
        name='ViewEnclosure',
        required_tables=('Entity',),
        doc="""
        Examine multi-language enclosures in an easy to read listing.

        Ordered ascending on ``name``, ``reporting_date``.

        Columns
        -------
        entity_name : TEXT or NULL
            From ``Entity.name``.
        reporting_date : TEXT or NULL
            From ``Filing.reporting_date``.
        country : TEXT or NULL
            From ``Filing.country``.
        languages : TEXT or NULL
            Comma-separated list from ``Filing.language`` in arbitrary
            order.
        filing_api_ids : TEXT or NULL
            Comma-separated list from ``Filing.api_id`` in arbitrary
            order.
        error_count : REAL or NULL
            Average from ``Filing.error_count`` values.
        inconsistency_count : REAL or NULL
            Average from ``Filing.inconsistency_count`` values.
        warning_count : REAL or NULL
            Average from ``Filing.warning_count`` values.
        added_time : TEXT or NULL
            From ``Filing.added_time``.
        processed_time : TEXT or NULL
            From ``Filing.processed_time``.
        identifier : TEXT or NULL
            From ``Entity.identifier``.
        entity_api_id : TEXT
            From ``Entity.api_id``.
        """,
        sql="""
SELECT
  name AS entity_name,
  reporting_date,
  country,
  group_concat(language, ', ') AS languages,
  group_concat(f.api_id, ', ') AS filing_api_ids,
  avg(error_count) AS error_count,
  avg(inconsistency_count) AS inconsistency_count,
  avg(warning_count) AS warning_count,
  added_time,
  processed_time,
  identifier,
  e.api_id AS entity_api_id
FROM Filing AS f
  JOIN Entity AS e ON f.entity_api_id = e.api_id
GROUP BY e.api_id, reporting_date
ORDER BY name, reporting_date
"""
        ),
    SQLiteView(
        name='ViewFilingAge',
        required_tables=('Entity',),
        doc="""
        Examine the age of the data on the filings.

        Ordered descending on ``ageNowMonths``.

        Columns
        -------
        entity_name : TEXT or NULL
            From ``Entity.name``.
        reporting_date : TEXT or NULL
            From ``Filing.reporting_date``.
        ageNowMonths : INTEGER or NULL
            Age of the filing in months expecting month to be 29.53
            days.
        country : TEXT or NULL
            From ``Filing.country``.
        language : TEXT or NULL
            From ``Filing.language``.
        added_time : TEXT or NULL
            From ``Filing.added_time``.
        processed_time : TEXT or NULL
            From ``Filing.processed_time``.
        addedToProcessedDays : INTEGER or NULL
            Days passed from ``Filing.added_time`` to
            ``Filing.processed_time`` rounded to full days.
        filing_api_id : TEXT
            From ``Filing.api_id``.
        entity_api_id : TEXT
            From ``Entity.api_id``.
        """,
        sql="""
SELECT
  name AS entity_name,
  reporting_date,
  cast(round(
    (julianday(date('now'))-julianday(reporting_date))/29.53
  ) AS INTEGER) AS ageNowMonths,
  country,
  language,
  added_time,
  processed_time,
  cast(round(
    julianday(date(processed_time))-julianday(date(added_time))
  ) AS INTEGER) AS addedToProcessedDays,
  f.api_id AS filing_api_id,
  e.api_id AS entity_api_id
FROM Filing AS f
  JOIN Entity AS e ON f.entity_api_id=e.api_id
ORDER BY ageNowMonths DESC
"""
        ),
    ]
