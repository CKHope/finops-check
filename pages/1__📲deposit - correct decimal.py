import streamlit as st
import pandas as pd
from decimal import Decimal, getcontext, ROUND_DOWN, InvalidOperation

# Set the precision level
getcontext().prec = 18

st.title('Cryptocurrency Deposit Transaction Validator')

# Helper function to truncate numbers
def truncate(number, decimals=2):
    factor = Decimal(10) ** -decimals
    return number.quantize(factor, rounding=ROUND_DOWN)

def recalculate_and_validate_deposits(df, truncations):
    recalculations = {
        'RC_CLEO.Lit Sell GDR/USD - Reference': lambda row: truncate(Decimal(row['CLEO.Lit buy X% (backup rate GDR/XAU) XAU/USD - reference']) * (Decimal('100') + Decimal(row['Total Markup - For Referrence'])) / Decimal('100'), truncations['RC_CLEO.Lit Sell GDR/USD - Reference']),
        'RC_Deposit Amount USD': lambda row: truncate(Decimal(row['Deposit Amount OC']) * Decimal(row['CLEO.lit Buy Token/USD Reference']), truncations['RC_Deposit Amount USD']),
        'RC_GDR Client Receive': lambda row: truncate(Decimal(row['RC_Deposit Amount USD']) / Decimal(row['RC_CLEO.Lit Sell GDR/USD - Reference']), truncations['RC_GDR Client Receive']),
        'RC_COGs': lambda row: truncate(Decimal(row['GDR Client Receive']) * Decimal(row['CLEO.Lit buy X% (backup rate GDR/XAU) XAU/USD - reference']), truncations['RC_COGs']),
        'RC_Revenue': lambda row: truncate(Decimal(row['GDR Client Receive']) * Decimal(row['RC_CLEO.Lit Sell GDR/USD - Reference']), truncations['RC_Revenue']),
        'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': lambda row: truncate(Decimal(row['Mark up rate 5 - Transfer transasaction & gas fee']) / Decimal(row['Total Markup - For Referrence']) * (Decimal(row['Revenue']) - Decimal(row['COGs'])), truncations['RC_Mark up rate 5 - Value - Transfer transasaction & gas fee']),
        'RC_Mark up rate 4 - Value - Business risk reserve': lambda row: truncate(Decimal(row['Mark up rate 4 - Business risk reserve']) / Decimal(row['Total Markup - For Referrence']) * (Decimal(row['Revenue']) - Decimal(row['COGs'])), truncations['RC_Mark up rate 4 - Value - Business risk reserve']),
        'RC_Mark up rate 3 - Value - Crypto to fiat conversion': lambda row: truncate(Decimal(row['Mark up rate 3 - Crypto to fiat conversion']) / Decimal(row['Total Markup - For Referrence']) * (Decimal(row['Revenue']) - Decimal(row['COGs'])), truncations['RC_Mark up rate 3 - Value - Crypto to fiat conversion']),
        'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': lambda row: truncate(Decimal(row['Mark up rate 2 - Withdrawal transasaction & gas fee']) / Decimal(row['Total Markup - For Referrence']) * (Decimal(row['Revenue']) - Decimal(row['COGs'])), truncations['RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee']),
        'RC_Mark up rate 1 - Value - Gold price fluctuation': lambda row: truncate(Decimal(row['Mark up rate 1 - Gold Price Fluctuation']) / Decimal(row['Total Markup - For Referrence']) * (Decimal(row['Revenue']) - Decimal(row['COGs'])), truncations['RC_Mark up rate 1 - Value - Gold price fluctuation'])
    }

    for col, func in recalculations.items():
        df[col] = df.apply(func, axis=1)

    results = []
    for _, row in df.iterrows():
        status = "Valid" if row['Amount Dc'] > 0 else "Invalid - Amount should be positive"
        discrepancies = []
        for col_name, tolerance in truncations.items():
            original_col = col_name.replace('RC_', '')
            if abs(Decimal(row[col_name]) - Decimal(row[original_col])) > tolerance:
                status = f"Invalid - Discrepancy in {original_col}"
                discrepancies.append({
                    'Column': original_col,
                    'Expected': row[col_name],
                    'Actual': row[original_col]
                })
        
        result = {
            'Transaction ID': row['Transaction ID'], 
            'Status': status, 
            'Discrepancies': discrepancies
        }
        for col_name in truncations.keys():
            original_col = col_name.replace('RC_', '')
            result[col_name] = row[col_name]
            result[original_col] = row[original_col]
        results.append(result)
    
    return pd.DataFrame(results)

deposit_file = st.file_uploader("Upload Deposit CSV", type=["csv"])

if deposit_file:
    deposit_df = pd.read_csv(deposit_file)
    st.write("Deposits", deposit_df.head())
    
    tolerance_inputs = {
        'RC_CLEO.Lit Sell GDR/USD - Reference': Decimal('0.01'),
        'RC_Deposit Amount USD': Decimal('0.01'),
        'RC_GDR Client Receive': Decimal('0.01'),
        'RC_COGs': Decimal('0.01'),
        'RC_Revenue': Decimal('0.01'),
        'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': Decimal('0.01'),
        'RC_Mark up rate 4 - Value - Business risk reserve': Decimal('0.01'),
        'RC_Mark up rate 3 - Value - Crypto to fiat conversion': Decimal('0.01'),
        'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': Decimal('0.01'),
        'RC_Mark up rate 1 - Value - Gold price fluctuation': Decimal('0.01')
    }

    with st.sidebar.expander("Set Truncations", expanded=True):
        truncations = {col: st.number_input(f"Truncate for {col}", min_value=0.0, format="%e", value=val, step=1e-15) 
                      for col, val in tolerance_inputs.items()}

    selected_columns = st.sidebar.multiselect("Additional Columns to Display", deposit_df.columns.tolist())

    deposit_results = recalculate_and_validate_deposits(deposit_df, truncations)
    
    display_columns = ['Transaction ID', 'Status', 'Discrepancies']
    for col in truncations.keys():
        original_col = col.replace('RC_', '')
        display_columns.extend([original_col, col])
    display_columns.extend(selected_columns)
    
    st.subheader("Validation Results")
    display_results = deposit_results.copy()
    display_results['Discrepancies'] = display_results['Discrepancies'].apply(lambda x: ', '.join([f"{item['Column']}: Expected {item['Expected']}, Actual {item['Actual']}" for item in x]))
    st.write(display_results[display_columns])
    
    invalid_count = (deposit_results['Status'] != 'Valid').sum()
    st.write("Invalid transactions:" if invalid_count else "All transactions are valid.", invalid_count)

with st.expander("About This App", expanded=True):
    st.markdown("""
    This Streamlit app validates cryptocurrency deposit transactions based on uploaded CSV data. It performs the following steps:
    1. **Upload CSV**: Allows users to upload a CSV file containing deposit transaction data.
    2. **Recalculation and Validation**: Recalculates certain columns based on predefined formulas and compares them against expected values.
    3. **Truncations**: Provides options to set truncations for each recalculated column to truncate to a specified number of decimal places.
    4. **Additional Columns**: Allows users to select additional columns from the CSV to display alongside validation results.
    5. **Recalculation Logic**: Displays the formulas used to recalculate each derived column based on the uploaded data.
    The app ensures transaction validity by checking for discrepancies in recalculated values compared to original data, providing detailed status and discrepancies for each transaction.
    For any questions or feedback, please contact [Your Contact Information].
    """)

with st.expander("Recalculation Logic", expanded=True):
    st.markdown("""
    ### Recalculation Formulas
    - **RC_CLEO.Lit Sell GDR/USD - Reference**: `CLEO.Lit buy X% (backup rate GDR/XAU) XAU/USD - reference * (100 + Total Markup - For Referrence) / 100`
    - **RC_Deposit Amount USD**: `Deposit Amount OC * CLEO.lit Buy Token/USD Reference`
    - **RC_GDR Client Receive**: `RC_Deposit Amount USD / RC_CLEO.Lit Sell GDR/USD - Reference`
    - **RC_COGs**: `GDR Client Receive * CLEO.Lit buy X% (backup rate GDR/XAU) XAU/USD - reference`
    - **RC_Revenue**: `GDR Client Receive * RC_CLEO.Lit Sell GDR/USD - Reference`
    - **RC_Mark up rate 5 - Value - Transfer transasaction & gas fee**: `Mark up rate 5 - Transfer transasaction & gas fee / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 4 - Value - Business risk reserve**: `Mark up rate 4 - Business risk reserve / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 3 - Value - Crypto to fiat conversion**: `Mark up rate 3 - Crypto to fiat conversion / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee**: `Mark up rate 2 - Withdrawal transasaction & gas fee / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 1 - Value - Gold price fluctuation**: `Mark up rate 1 - Gold Price Fluctuation / Total Markup - For Referrence * (Revenue - COGs)`
    """)
