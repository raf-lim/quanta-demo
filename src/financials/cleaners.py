
# Processing raw data from API


def clean_income_statements_data(
        raw_data: list[list[dict]]
    ) -> dict[str, list[dict[str, str]]]:
    """Process income statement data into clean output."""
    output_data = {}
    for raw_statement in raw_data:
        if raw_statement:  # skip if not available (empty list)
            output_data[raw_statement[0]['symbol'].upper()] = [{
                'cik': data.get('cik'),
                'date': data.get('fillingDate'),
                'eps_dill': data.get('epsdiluted'),
                'revenue': data.get('revenue'),
                'end': data.get('date'),
            } for data in raw_statement]
    return output_data


def clean_balance_sheets_data(
        raw_data: list[list[dict]]
    ) -> dict[str, list[dict[str, str]]]:
    """Process balance sheet data into clean output."""
    output_data = {}
    for raw_statement in raw_data:
        if raw_statement:  # skip if not available (empty list)
            output_data[raw_statement[0]['symbol'].upper()] = [{
                'date': data.get('fillingDate'),
                'sh_equity': data.get('totalStockholdersEquity'),
            } for data in raw_statement]
    return output_data


def clean_earning_calendar_data(
        raw_data: list[list[dict]]
    ) -> dict[str, list[dict[str, str]]]:
    """Process earining calendar data into clean output."""
    output_data = {}
    for raw_statement in raw_data:
        if raw_statement:  # skip if not available (empty list)
            output_data[raw_statement[0]['symbol'].upper()] = [{
                'eps': data.get('eps'),
                'end': data.get('fiscalDateEnding')
            } for data in raw_statement]
    return output_data


def clean_prices_data(
        raw_data: list[dict[str, str] | dict[str, list[dict[str, str]]]]
    ) -> dict[str, dict[str, dict[str, str]]]:
    """Process prices data into clean output."""
    prices = {}
    for raw_prices in raw_data:
        if raw_prices:
            prices[raw_prices['symbol'].upper().replace('.', '-')] = {
                data['date']: {'open': data['open'], 'close': data['close']}
                  for data in raw_prices['historical'] 
            }
    return prices
