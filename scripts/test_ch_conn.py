"""Test ClickHouse connection from venv"""
import clickhouse_connect
ch = clickhouse_connect.get_client(
    host="localhost", port=8123,
    user="pipeline",
    password="wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E"
)
print("Rows in stock_basic:", ch.query("SELECT count() FROM tushare.tushare_stock_basic").result_rows[0][0])
