# XBRL Filings API

Python API for filings.xbrl.org XBRL report repository.

> **Note**
> This library is still under development.

As of July 2023, all the filings are Inline XBRL reports prepared in
accordance to the European Single Electronic Format (ESEF). This
means that the reporters have issued securities on European
regulated markets. In most of the cases these securities are shares,
but not always. Issuers on alternative stock exchanges such as the
Nordic exchange First North are exempted from ESEF mandate and thus
are not included.

The library is not connected to XBRL International.

**Table of Contents**

- [Installation](#installation)
- [License](#license)
- [Data objects](#data-objects)
    * [Filing](#filing)
    * [Entity](#entity)
    * [ValidationMessage](#validationmessage)

## Installation

```console
pip install xbrl-filings-api
```

## License

`xbrl-filings-api` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Data objects

This library expects the API returning datetimes in UTC, if no timezone
is specified (situation as of 6 Nov 2023).

### Filing

Access to `entity` requires flag `GET_ENTITY` and to
`validation_messages` flag `GET_VALIDATION_MESSAGES`.

Data attributes:

| Attribute name          | Type     | Description                         | Query   | JSON:API field name   |
| ----------------------- | -------- | ----------------------------------- | ------- | --------------------- |
| `api_id`                | str      | JSON:API identifier                 | **X**   | Resource `id`         |
| `country`               | str      | Country of entity                   | **X**   | `country`             |
| `filing_index`          | str      | Database identifier                 | **X**   | `fxo_id`              |
| `language`              | str      | Language from `package_url`         |         | *derived*             |
| `last_end_date`         | date     | Last reported data date             | **X**   | `period_end`          |
| `reporting_date`        | date     | Financial period end from `package_url` |     | *derived*             |
| `error_count`           | int      | Count of validation errors          | (**X**) | `error_count`         |
| `inconsistency_count`   | int      | Count of validation inconsistencies | (**X**) | `inconsistency_count` |
| `warning_count`         | int      | Count of validation warnings        | (**X**) | `warning_count`       |
| `added_time`            | datetime | Time when added to `filings.xbrl.org` | **X** | `date_added  `        |
| `processed_time`        | datetime | Time when processed for `filings.xbrl.org` | **X** | `processed`      |
| `entity_api_id`         | str      | Same as `entity.api_id`             |         | Entity resource `id`  |
| `json_url`              | str      | xBRL-JSON download URL              | (**X**) | `json_url`            |
| `package_url`           | str      | ESEF report package download URL    | (**X**) | `package_url`         |
| `viewer_url`            | str      | Inline XBRL viewer URL              | (**X**) | `viewer_url`          |
| `xhtml_url`             | str      | Inline XBRL report download URL     | (**X**) | `report_url`          |
| `query_time`            | datetime | Time when query function was called |         | \-                    |
| `request_url`           | str      | URL of the API request              |         | \-                    |
| `json_download_path`    | str      | Path where `json_url` was downloaded |        | \-                    |
| `package_download_path` | str      | Path where `package_url` was downloaded |     | \-                    |
| `viewer_download_path`  | str      | Path where `viewer_url` was downloaded |      | \-                    |
| `xhtml_download_path`   | str      | Path where `xhtml_url` was downloaded |       | \-                    |
| `package_sha256`        | str      | SHA-256 hash of `package_url` file  |  **X**  |`sha256`               |

> **Warning**
> As of October 2023, attributes ending with `_count` and `_url` could
> not be used for filtering or sorting queries.

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
| `identifier`             | str      | Identifier of entity (LEI code)     | `identifier`        |
| `name`                   | str      | Name                                | `name`              |
| `api_entity_filings_url` | str      | JSON:API query for full list of `filings` | `filings.links.related` of relationships |
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
| `calc_unreported_items` | str      | Unreported contibuting items of calcInconsistency | *derived* |
| `duplicate_greater`     | float    | Greater one of duplicated facts     | *derived*           |
| `duplicate_lesser`      | float    | Lesser one of duplicated facts      | *derived*           |
| `query_time`            | datetime | Time when query function was called | \-                  |
| `request_url`           | str      | URL of the API request              | \-                  |

Derived attributes beginning ``calc_`` are only available for validation
messages with `code` "xbrl.5.2.5.2:calcInconsistency". The ones
beginning ``duplicate_`` are available for `code`
"message:tech_duplicated_facts1" if the values are numeric. They are
parsed out from the `text` of the message.

Object references:

| Attribute name | Type          |
| -------------- | --------------|
| `filing`       | Filing        |
