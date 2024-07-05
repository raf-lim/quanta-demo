import pandas as pd

def adjust_columns_width(table: pd.DataFrame, sheet_name: str, writer) -> None:
    """Auto-adjust columns' width (xlsxwriter needed)"""
    for column in table:
        column_width = max(
            table[column].astype(str).map(len).max(), len(column)
        )
        col_idx = table.columns.get_loc(column)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, column_width)
