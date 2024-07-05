import streamlit as st
import pandas as pd

st.title('Cryptocurrency Deposit Transaction Validator')

# Helper function to perform high-precision calculation
def high_precision_calc(func):
    def wrapper(*args):
        result = func(*args)
        return int(result * 1e18) / 1e18
    return wrapper

# Updated recalculations with high-precision wrapper
recalculations = {
    'RC_CLEO.Lit Sell GDR/USD - Reference': high_precision_calc(lambda row: row['CLEO.Lit buy X% (backup rate GDR/XAU) XAU/USD - reference'] * (100 + row['Total Markup - For Referrence']) / 100),
    'RC_Deposit Amount USD': high_precision_calc(lambda row: row['Deposit Amount OC'] * row['CLEO.lit Buy Token/USD Reference']),
    'RC_GDR Client Receive': high_precision_calc(lambda row: row['RC_Deposit Amount USD'] / row['RC_CLEO.Lit Sell GDR/USD - Reference']),
    'RC_COGs': high_precision_calc(lambda row: row['GDR Client Receive'] * row['CLEO.Lit buy X% (backup rate GDR/XAU) XAU/USD - reference']),
    'RC_Revenue': high_precision_calc(lambda row: row['GDR Client Receive'] * row['RC_CLEO.Lit Sell GDR/USD - Reference']),
    'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': high_precision_calc(lambda row: row['Mark up rate 5 - Transfer transasaction & gas fee'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs'])),
    'RC_Mark up rate 4 - Value - Business risk reserve': high_precision_calc(lambda row: row['Mark up rate 4 - Business risk reserve'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs'])),
    'RC_Mark up rate 3 - Value - Crypto to fiat conversion': high_precision_calc(lambda row: row['Mark up rate 3 - Crypto to fiat conversion'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs'])),
    'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': high_precision_calc(lambda row: row['Mark up rate 2 - Withdrawal transasaction & gas fee'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs'])),
    'RC_Mark up rate 1 - Value - Gold price fluctuation': high_precision_calc(lambda row: row['Mark up rate 1 - Gold Price Fluctuation'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs']))
}

def recalculate_and_validate_deposits(df, tolerances):
    for col, func in recalculations.items():
        df[col] = df.apply(func, axis=1)

    results = []
    for _, row in df.iterrows():
        status = "Valid" if row['Amount Dc'] > 0 else "Invalid - Amount should be positive"
        discrepancies = []
        for col_name, tolerance in tolerances.items():
            original_col = col_name.replace('RC_', '')
            if abs(row[col_name] - row[original_col]) > tolerance:
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
        for col_name in tolerances.keys():
            original_col = col_name.replace('RC_', '')
            result[col_name] = row[col_name]
            result[original_col] = row[original_col]
        results.append(result)
    
    return pd.DataFrame(results)

# Rest of the Streamlit app code remains the same
...

with st.expander("About This App", expanded=True):
    st.markdown("""
    This Streamlit app validates cryptocurrency deposit transactions based on uploaded CSV data. It performs the following steps:
    1. **Upload CSV**: Allows users to upload a CSV file containing deposit transaction data.
    2. **Recalculation and Validation**: Recalculates certain columns based on predefined formulas and compares them against expected values.
    3. **High-Precision Calculations**: Uses a technique to improve floating-point arithmetic precision by multiplying and dividing by 1e18.
    4. **Tolerances**: Provides options to set tolerances for each recalculated column to account for numerical discrepancies.
    5. **Additional Columns**: Allows users to select additional columns from the CSV to display alongside validation results.
    6. **Recalculation Logic**: Displays the formulas used to recalculate each derived column based on the uploaded data.
    The app ensures transaction validity by checking for discrepancies in recalculated values compared to original data, providing detailed status and discrepancies for each transaction.
    For any questions or feedback, please contact [Your Contact Information].
    """)

with st.expander("Recalculation Logic", expanded=True):
    st.markdown("""
    ### Recalculation Formulas (with High-Precision Calculation)
    All formulas are wrapped in a high-precision calculation function that multiplies the result by 1e18 and then divides by 1e18 to mitigate floating-point arithmetic errors.

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