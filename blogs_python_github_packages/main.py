import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from snowflake.extensions import SnowflakeConnection  # type: ignore


def load_to_snowflake(
    conn: SnowflakeConnection,
    df: pd.DataFrame,
    table_name: str
) -> None:
    """
    Use the write_pandas function to load data into Snowflake.
    """
    write_pandas(
        conn=conn,
        df=df,
        table_name=table_name,
        auto_create_table=True,
        overwrite=True
    )

    return
