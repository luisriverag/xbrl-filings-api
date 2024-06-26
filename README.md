[api]: https://filings.xbrl.org
[pd]: https://pandas.pydata.org
[sqlite]: https://www.sqlite.org/
[docs]: https://lsalmela.github.io/xbrl-filings-api
[pypi]: https://pypi.org/project/xbrl-filings-api "xbrl-filings-api entry on PyPI"
[lic]: https://spdx.org/licenses/MIT.html "MIT License"

# XBRL Filings API

Python API for filings.xbrl.org XBRL report repository.

This library provides:

1. Python-friendly access to the public API in [filings.xbrl.org][api]
2. Parallel downloading of associated files (ZIP, XHTML and JSON)
3. Integration to [pandas][pd]
4. Integration to [SQLite][sqlite] database, incl. SQLite views
   (accounting reliability)
5. A few useful derived attributes
6. Possibility to strip redundant language versions/corrected filings

As of March 2024, all the filings in the database are Inline XBRL
reports. They are prepared in accordance to the European Single
Electronic Format (ESEF), the United Kingdom Single Electronic Format
(UKSEF), or the Ukraine Financial Reporting System. The first reports
are from financial year 2020 for all reporting formats.

In the case of ESEF, the reporters have issued securities on European
regulated markets in European Union member states. In most of the cases
these securities are shares. Issuers on alternative stock exchanges in
the EU such as the Nordic exchange First North are exempted from the
ESEF mandate and are thus not available.

This library is independent of XBRL International.

See [documentation for XBRL Filings API][docs]. The library is available
on [PyPI][pypi].

**Table of Contents**

- [License](#license)
- [Installation](#installation)
- [Data objects](#data-objects)
    * [Filing](#filing)
    * [Entity](#entity)
    * [ValidationMessage](#validationmessage)

## License

``xbrl-filings-api`` is distributed under the terms of the [MIT][lic]
license.

## Installation

Install the library using pip.

```console
python -m pip install xbrl-filings-api
```

## Data objects

### Filing

Access to `entity` requires flag `GET_ENTITY` and to
`validation_messages` flag `GET_VALIDATION_MESSAGES`.

Data attributes:

| Attribute name          | Type     | Description                         | Query   | JSON:API field name   |
| ----------------------- | -------- | ----------------------------------- | ------- | --------------------- |
| `api_id`                | str      | JSON:API identifier                 | **X**   | Resource `id`         |
| `country`               | str      | Country of entity                   | **X**   | `country`             |
| `filing_index`          | str      | Database identifier                 | **X**   | `fxo_id`              |
| `language`              | str      | Language from `package_url`, `xhtml_url` |    | *derived*             |
| `last_end_date`         | date     | Last reported data date             | **X**   | `period_end`          |
| `reporting_date`        | date     | Financial period end from `package_url` |     | *derived*             |
| `error_count`           | int      | Count of validation errors          |         | `error_count`         |
| `inconsistency_count`   | int      | Count of validation inconsistencies |         | `inconsistency_count` |
| `warning_count`         | int      | Count of validation warnings        |         | `warning_count`       |
| `added_time`            | datetime | Time when added to the database     | **X** | `date_added  `          |
| `processed_time`        | datetime | Time when processed for the database | **X** | `processed`            |
| `entity_api_id`         | str      | Same as `entity.api_id`             |         | Entity resource `id`  |
| `json_url`              | str      | xBRL-JSON download URL              |         | `json_url`            |
| `package_url`           | str      | ESEF report package download URL    |         | `package_url`         |
| `viewer_url`            | str      | Inline XBRL viewer URL              |         | `viewer_url`          |
| `xhtml_url`             | str      | Inline XBRL report download URL     |         | `report_url`          |
| `query_time`            | datetime | Time when query function was called |         | \-                    |
| `request_url`           | str      | URL of the API request              |         | \-                    |
| `json_download_path`    | str      | Path where `json_url` was downloaded |        | \-                    |
| `package_download_path` | str      | Path where `package_url` was downloaded |     | \-                    |
| `xhtml_download_path`   | str      | Path where `xhtml_url` was downloaded |       | \-                    |
| `package_sha256`        | str      | SHA-256 checksum of `package_url` file |  **X**  |`sha256`            |

As of April 2024, attributes ending with `_count` and `_url` could not
be used for filtering or sorting queries. This might change in future.

Object references:

| Attribute name        | Type                     | Required flag for access  |
| --------------------- | ------------------------ | ------------------------- |
| `entity`              | Entity                   | `GET_ENTITY`              |
| `validation_messages` | set of ValidationMessage | `GET_VALIDATION_MESSAGES` |


### Entity

Data attributes:

| Attribute name           | Type     | Description                         | JSON:API field name |
| ------------------------ | -------- | ----------------------------------- | ------------------- |
| `api_id`                 | str      | JSON:API identifier                 | Resource `id`       |
| `identifier`             | str      | XBRL identifier (e.g. LEI code)     | `identifier`        |
| `name`                   | str      | Name                                | `name`              |
| `api_entity_filings_url` | str      | JSON:API query for its `filings`    | \-                  |
| `query_time`             | datetime | Time when query function was called | \-                  |
| `request_url`            | str      | URL of the API request              | \-                  |

Object references:

| Attribute name | Type          |
| -------------- | --------------|
| `filings`      | set of Filing |


### ValidationMessage

Data attributes:

| Attribute name          | Type     | Description                         | JSON:API field name |
| ----------------------- | -------- | ----------------------------------- | ------------------- |
| `api_id`                | str      | JSON:API identifier                 | Resource `id`       |
| `severity`              | str      | Severity of the issue               | `severity`          |
| `text`                  | str      | Text of the message                 | `text`              |
| `code`                  | str      | Code of the breached rule           | `code`              |
| `filing_api_id`         | str      | Same as `filing.api_id`             | Filing resource `id` |
| `calc_computed_sum`     | float    | Computed sum of calcInconsistency   | *derived*           |
| `calc_reported_sum`     | float    | Reported sum of calcInconsistency   | *derived*           |
| `calc_context_id`       | str      | Context ID of calcInconsistency     | *derived*           |
| `calc_line_item`        | str      | Line item of calcInconsistency      | *derived*           |
| `calc_short_role`       | str      | Short role of calcInconsistency     | *derived*           |
| `calc_unreported_items` | str      | Unreported contributing items of calcInconsistency | *derived* |
| `duplicate_greater`     | float    | Greater one of duplicated facts     | *derived*           |
| `duplicate_lesser`      | float    | Lesser one of duplicated facts      | *derived*           |
| `query_time`            | datetime | Time when query function was called | \-                  |
| `request_url`           | str      | URL of the API request              | \-                  |

Derived attributes beginning `"calc_"` are only available for validation
messages with `code` `"xbrl.5.2.5.2:calcInconsistency"`. The ones
beginning `"duplicate_"` are available for `code`
`'message:tech_duplicated_facts1'` if the values are numeric. They are
parsed out from the `text` of the message.

Object references:

| Attribute name | Type          |
| -------------- | --------------|
| `filing`       | Filing        |
