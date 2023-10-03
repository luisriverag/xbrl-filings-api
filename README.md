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

### Filing

Access to `entity` requires flag `GET_ENTITY` and to
`validation_messages` flag `GET_VALIDATION_MESSAGES`.

Data attributes:

| Attribute name          | Type     | Description                         | JSON:API field name | Query   |
| ----------------------- | -------- | ----------------------------------- | ------------------- | ------- |
| `api_id`                | str      | JSON:API identifier                 | Resource `id`       |         |
| `country`               | str      | Country of entity                   | `country`           | **X**   |
| `filing_index`          | str      | Database identifier                 | `fxo_id`            | **X**   |
| `language`              | str      | Language from `package_url`         | *derived*           |         |
| `last_end_date`         | date     | Last reported data date             | `period_end`        | **X**   |
| `reporting_date`        | date     | Financial period end from `package_url` | *derived*       |         |
| `error_count`           | str      | Count of validation errors          | `error_count`       | (**X**) |
| `inconsistency_count`   | str      | Count of validation inconsistencies | `inconsistency_count` | (**X**) |
| `warning_count`         | str      | Count of validation warnings        | `warning_count`     | (**X**) |
| `added_time`            | datetime | Time when added to `filings.xbrl.org` | `date_added`      | **X**   |
| `processed_time`        | datetime | Time when processed for `filings.xbrl.org` | `processed`  | **X**   |
| `entity_api_id`         | str      | Same as `entity.api_id`             | Entity resource `id` |        |
| `entity`                | Entity   | Reference to `Entity` object        | \-                  |         |
| `validation_messages`   | set of ValidationMessage | Validation messages | \-                  |         |
| `json_url`              | str      | xBRL-JSON download URL              | `json_url`          | (**X**) |
| `package_url`           | str      | ESEF report package download URL    | `package_url`       | (**X**) |
| `viewer_url`            | str      | Inline XBRL viewer URL              | `viewer_url`        | (**X**) |
| `xhtml_url`             | str      | Inline XBRL report download URL     | `report_url`        | (**X**) |
| `query_time`            | datetime | Time when query function was called | \-                  |         |
| `request_url`           | str      | URL of the API request              | \-                  |         |
| `json_download_path`    | str      | Path where `json_url` was downloaded | \-                 |         |
| `package_download_path` | str      | Path where `package_url` was downloaded | \-              |         |
| `viewer_download_path`  | str      | Path where `viewer_url` was downloaded | \-               |         |
| `xhtml_download_path`   | str      | Path where `xhtml_url` was downloaded | \-                |         |
| `package_sha256`        | str      | SHA-256 hash of `package_url` file  | `sha256             | **X**   |

> **Warning**
> As of October 2023, attributes ending with `_count` and `_url` could
> not be used for filtering or sorting queries.


### Entity

Data attributes:

| Attribute name           | Type     | Description                         | JSON:API field name |
| ------------------------ | -------- | ----------------------------------- | ------------------- |
| `api_id`                 | str      | JSON:API identifier                 | Resource `id`       |
| `identifier`             | str      | Identifier of entity (LEI code)     | `identifier`        |
| `name`                   | str      | Name                                | `name`              |
| `filings`                | set of Filing | Filings of the entity in current query | \-                  |
| `api_entity_filings_url` | str      | JSON:API query for full list of `filings` | `filings.links.related` of relationships |
| `query_time`             | datetime | Time when query function was called | \-                  |
| `request_url`            | str      | URL of the API request              | \-                  |


### ValidationMessage

Data attributes:

| Attribute name          | Type     | Description                         | JSON:API field name |
| ----------------------- | -------- | ----------------------------------- | ------------------- |
| `api_id`                | str      | JSON:API identifier                 | Resource `id`       |
| `severity`              | str      | Severity of the issue               | `severity`          |
| `text`                  | str      | Text of the message                 | `text`              |
| `code`                  | str      | Code of the breached rule           | `code`              |
| `filing_api_id`         | str      | Same as `filing.api_id`             | Filing resource `id` |
| `filing`                | Filing   | Reference to `Filing` object        | `filing`            |
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
