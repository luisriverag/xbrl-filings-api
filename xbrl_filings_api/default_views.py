"""
Define default views for SQLite output.

Views
-----
ViewNumericInconsistency
    Show accounting errors in the statements ordered from the most
    severe to the least severe. The last records in the list are due to
    rounding errors.
ViewFiling
    A more compact view for Filing table including the entity name on
    each row. Excludes URLs, download paths, codes as well as unreliable
    and meta dates.
ViewTime
    Shows times including the age of the reported data in months and
    time it took to process the reports at XBRL International after
    adding it in the filing index.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from xbrl_filings_api.sqlite_view import SQLiteView

DEFAULT_VIEWS = frozenset({
    SQLiteView(
        name='ViewNumericInconsistency',
        required_tables=('ValidationMessage', 'Entity'),
        sql="""
-- Eliminate redundant language versions of the same enclosure in 'fs'
WITH fs AS (
  SELECT
    name,
    reporting_date,
    language,
    Filing.api_id,
    entity_api_id,
    row_number() OVER (
      PARTITION BY name, reporting_date ORDER BY language
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
    row_number() OVER (
      PARTITION BY duplicate_greater, duplicate_lesser
    ) AS dup_occur
  FROM ValidationMessage
)
-- Columns ending in 'K' are in thousands of monetary units
SELECT * FROM (
  SELECT
    name,
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
    entity_api_id
  FROM fs INNER JOIN v ON filing_api_id = fs.api_id
  WHERE
    dup_occur = 1
    AND lan_order = 1
    AND code = 'message:tech_duplicated_facts1'

  UNION ALL

  SELECT
    name,
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
    entity_api_id
  FROM fs
    JOIN ValidationMessage ON filing_api_id = fs.api_id
  WHERE lan_order = 1 AND code = 'xbrl.5.2.5.2:calcInconsistency'
)
ORDER BY errorPercent DESC NULLS FIRST
"""
        ),
    SQLiteView(
        name='ViewFiling',
        required_tables=('Entity',),
        sql="""
SELECT
  name,
  reporting_date,
  country,
  GROUP_CONCAT(language, ', ') AS languages,
  error_count,
  inconsistency_count,
  warning_count,
  added_time,
  processed_time,
  identifier
FROM Filing AS f
  JOIN Entity AS e ON f.entity_api_id=e.api_id
GROUP BY identifier, reporting_date
ORDER BY language, name, reporting_date
"""
        ),
    SQLiteView(
        name='ViewTime',
        required_tables=('Entity',),
        sql="""
SELECT
  name,
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
  ) AS INTEGER) AS addedToProcessedDays
FROM Filing AS f
  JOIN Entity AS e ON f.entity_api_id=e.api_id
ORDER BY added_to_processed_days DESC
"""
        ),
    })
