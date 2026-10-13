import sqlite3


def test_cloud_quality_predicate_catches_nulls_and_invalid_values(settings):
    sql = (settings.root / "tire-demo/sql/snowflake/quality.sql").read_text()
    predicate = sql.split("SELECT 'invalid_product_values',COUNT(*) FROM product\nWHERE ")[1].split(
        "\nUNION ALL"
    )[0]
    # Exercise SQL-standard null semantics locally; this is not live Snowflake execution.
    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE product (product_id,size,price,comfort,wet_grip,load_index,speed_rank)"
        )
        valid = ("T0001", "225/55R17", 125, 7, 8, 98, 4)
        rows = [valid]
        for index in range(7):
            broken = list(valid)
            broken[index] = None
            rows.append(tuple(broken))
        rows.append(("T0002", "225/55R17", 125, 11, 8, 98, 4))
        connection.executemany("INSERT INTO product VALUES (?,?,?,?,?,?,?)", rows)
        assert (
            connection.execute("SELECT COUNT(*) FROM product WHERE " + predicate).fetchone()[0] == 8  # noqa: S608
        )
