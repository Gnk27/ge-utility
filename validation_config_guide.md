
# 📘 Validation Configuration Guide for QA Engineers

This guide explains how to use the `TABLE_VALIDATION_CONFIG` table to define and manage data validations using Great Expectations.

---

## Table Structure: `TABLE_VALIDATION_CONFIG`

Each row in this table represents **one validation rule** applied to a column or a group of columns in a Snowflake table.

| Column Name       | Type         | Description                                                      |
|-------------------|--------------|------------------------------------------------------------------|
| `table_name`      | STRING       | The target table to validate                                     |
| `column_name`     | STRING (nullable) | The single column to validate (if applicable)               |
| `expectation_type`| STRING       | The GE expectation name (function-style string)                  |
| `params_json`     | STRING (nullable) | JSON-formatted string for expectation parameters         |
| `is_enabled`      | BOOLEAN      | Whether the validation is active (TRUE = run, FALSE = skip)      |

---

## Examples of Validations

### 1. `expect_column_values_to_not_be_null`

Ensures values in a column are never NULL.

| Example | Value |
|--------|-------|
| `expectation_type` | `expect_column_values_to_not_be_null` |
| `column_name` | `EMAIL` |
| `params_json` | *NULL* |

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('CUSTOMERS', 'EMAIL', 'expect_column_values_to_not_be_null', NULL, TRUE);
```

---

### 2. `expect_column_values_to_be_unique`

Ensures column values are unique (no duplicates).

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('CUSTOMERS', 'ID', 'expect_column_values_to_be_unique', NULL, TRUE);
```

---

### 3. `expect_column_values_to_match_regex`

Ensures column values match a pattern (e.g. valid email).

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('CUSTOMERS', 'EMAIL', 'expect_column_values_to_match_regex', '{"regex": "[^@]+@[^@]+\\.[^@]+"}', TRUE);
```

---

### 4. `expect_column_values_to_be_between`

Validates values fall between min/max values.

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('ORDERS', 'AMOUNT', 'expect_column_values_to_be_between', '{"min_value": 0, "max_value": 1000}', TRUE);
```

---

### 5. `expect_column_values_to_be_in_set`

Validates that values are within a predefined list.

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('PRODUCTS', 'CATEGORY', 'expect_column_values_to_be_in_set', '{"value_set": ["ELECTRONICS", "TOYS"]}', TRUE);
```

---

### 6. `expect_column_values_to_match_strftime_format`

Checks that dates match a specified format.

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('ORDERS', 'ORDER_DATE', 'expect_column_values_to_match_strftime_format', '{"strftime_format": "%Y-%m-%d"}', TRUE);
```

---

### 7. `expect_column_values_to_be_of_type`

Checks that column matches a specified data type.

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('CUSTOMERS', 'ID', 'expect_column_values_to_be_of_type', '{"type_": "INTEGER"}', TRUE);
```

---

### 8. `expect_compound_columns_to_be_unique`

Ensures the combination of multiple columns is unique. (e.g. ID must be unique per DATE + USER)

| `column_name` | NULL |
|---------------|------|
| `params_json` | `{"column_list": ["DATE", "USER", "ID"]}` |

```sql
INSERT INTO TABLE_VALIDATION_CONFIG VALUES
('EVENTS', NULL, 'expect_compound_columns_to_be_unique', '{"column_list": ["DATE", "USER", "ID"]}', TRUE);
```

---

## 💡 Tips for QA Engineers

- Use **double quotes** (`"`) in JSON strings.
- Escape backslashes in regex (e.g. `\.`).
- `column_name` can be NULL if the expectation works on multiple columns (e.g. compound).
- Use Snowflake column names as they appear in the schema.
- Keep validations simple and atomic — one expectation per row.

---

## Supported Expectations

You can use any standard GE expectation. See the full list here:  
https://docs.greatexpectations.io/docs/reference/expectations/standard_expectations/

---

