import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from great_expectations.data_context import get_context
import snowflake.connector
import pandas as pd

# Load environment variables
load_dotenv()


def build_expectation_function(expectation_type, column_name, params):
    def expectation_func(validator):
        expectation_method = getattr(validator, expectation_type)
        # Incluir el formato de resultado en los parámetros
        full_params = {**params, "result_format": "COMPLETE"} if params else {"result_format": "COMPLETE"}

        # Handle expectations that use column_list instead of column_name
        if "column_list" in full_params:
            expectation_method(
                column_list=full_params["column_list"],
                **{k: v for k, v in full_params.items() if k != "column_list"},
            )
        elif column_name:
            expectation_method(column_name, **full_params)
        else:
            expectation_method(**full_params)

    return expectation_func

def load_config_from_snowflake():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    )

    try:
        query = "SELECT table_name, column_name, expectation_type, params_json FROM TABLE_VALIDATION_CONFIG WHERE is_enabled = TRUE"
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"⚠️ Error loading config from Snowflake: {e}")
        # Fallback: provide a default validation config
        df = pd.DataFrame(
            [
                {
                    "table_name": "TEST_DATES",
                    "column_name": "ID",
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "params_json": "{}",
                },
                {
                    "table_name": "TEST_DATES",
                    "column_name": "EVENT_DATE",
                    "expectation_type": "expect_column_values_to_be_between",
                    "params_json": '{"min_value": "2025-01-01", "max_value": "2025-12-02"}',
                },
            ]
        )
    finally:
        conn.close()

    grouped = defaultdict(list)
    for _, row in df.iterrows():
        table = row["table_name"]
        column = row["column_name"]
        params = json.loads(row["params_json"]) if row["params_json"] else {}
        grouped[table].append(
            build_expectation_function(row["expectation_type"], column, params)
        )
    return grouped


def monitor_all_tables():
    context = get_context()
    
    # Load configs from Snowflake
    expectations_by_table = load_config_from_snowflake()

    # Connection string for Fluent API
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema_name = os.getenv("SNOWFLAKE_SCHEMA")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    connection_string = f"snowflake://{user}:{password}@{account}/{database}/{schema_name}?warehouse={warehouse}"

    datasource_name = "snowflake_ds"
    context.sources.add_or_update_snowflake(
        name=datasource_name, connection_string=connection_string
    )
    datasource = context.get_datasource("snowflake_ds")  # ✅ Works in Fluent v3

    for table_name, expectation_functions in expectations_by_table.items():
        suite_name = f"{table_name.lower()}_suite"
        asset_name = f"{schema_name.lower()}_{table_name.lower()}"

        table_asset = datasource.add_table_asset(
            name=asset_name, table_name=table_name, schema_name=schema_name
        )

        try:
            context.get_expectation_suite(suite_name)
        except Exception:
            context.add_expectation_suite(suite_name)

        validator = context.get_validator(
            datasource_name=datasource_name,
            data_asset_name=asset_name,
            expectation_suite_name=suite_name,
        )

        for func in expectation_functions:
            func(validator)

        validator.save_expectation_suite(discard_failed_expectations=False)

        checkpoint = context.add_or_update_checkpoint(
            name=f"{suite_name}_checkpoint", validator=validator
        )
        checkpoint_result = checkpoint.run()

        result = validator.validate()        

        # Get results as JSON
        # result_json = result.to_json_dict()
        # print(json.dumps(result_json, indent=2))

        context.build_data_docs(site_names=["local_site"])
        context.open_data_docs()

        print(
            f"Validation {'passed' if result.success else 'failed'} for {table_name}."
        )


if __name__ == "__main__":
    monitor_all_tables()
