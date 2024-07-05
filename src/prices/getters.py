from typing import Iterable
import sqlite3


def get_stocks_prices_form_db(
        symbols: Iterable[str], db_file_path: str
        ) -> dict[str, dict[str, dict[str, float | None]]]:
    connection = sqlite3.connect(db_file_path)
    cursor = connection.cursor()
    # print(cur.execute('PRAGMA table_list').fetchall())
    stocks_prices = {}
    for symbol in symbols:
        try:
            row = cursor.execute(
                f"SELECT date, open, close FROM '{symbol.lower()}' ORDER BY date"
                ).fetchall()
            stocks_prices[symbol.upper()] = (
                {i[0]: {'Open': i[1], 'Close': i[2]} for i in row}
                )
        except sqlite3.OperationalError:
            continue
    connection.close()

    return stocks_prices

