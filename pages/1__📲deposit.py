import streamlit as st
import pandas as pd

st.title('Cryptocurrency Deposit Transaction Validator')

def recalculate_and_validate_deposits(df, tolerances):
    recalculations = {
        'RC_CLEO.Lit Sell GDR/USD - Reference': lambda row: row['CLEO.Lit Buy GDR/USD - Reference'] * (100 + row['Total Markup - For Referrence']) / 100,
        'RC_Deposit Amount USD': lambda row: row['Deposit Amount OC'] * row['CLEO.lit Buy Token/USD Reference'],
        'RC_GDR Client Receive': lambda row: row['RC_Deposit Amount USD'] / row['RC_CLEO.Lit Sell GDR/USD - Reference'],
        'RC_COGs': lambda row: row['GDR Client Receive'] * row['CLEO.Lit Buy GDR/USD - Reference'],
        'RC_Revenue': lambda row: row['GDR Client Receive'] * row['RC_CLEO.Lit Sell GDR/USD - Reference'],
        'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': lambda row: row['Mark up rate 5 - Transfer transasaction & gas fee'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs']),
        'RC_Mark up rate 4 - Value - Business risk reserve': lambda row: row['Mark up rate 4 - Business risk reserve'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs']),
        'RC_Mark up rate 3 - Value - Crypto to fiat conversion': lambda row: row['Mark up rate 3 - Crypto to fiat conversion'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs']),
        'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': lambda row: row['Mark up rate 2 - Withdrawal transasaction & gas fee'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs']),
        'RC_Mark up rate 1 - Value - Gold price fluctuation': lambda row: row['Mark up rate 1 - Gold Price Fluctuation'] / row['Total Markup - For Referrence'] * (row['Revenue'] - row['COGs'])
    }

    for col, func in recalculations.items():
        df[col] = df.apply(func, axis=1)

    results = []
    for _, row in df.iterrows():
        status = "Valid" if row['Amount Dc'] > 0 else "Invalid - Amount should be positive"
        discrepancies = []
        for col_name, tolerance in tolerances.items():
            if abs(row[col_name] - row[col_name.replace('RC_', '')]) > tolerance:
                status = f"Invalid - Discrepancy in {col_name.replace('RC_', '')}"
                discrepancies.append({
                    'Column': col_name.replace('RC_', ''),
                    'Expected': row[col_name.replace('RC_', '')],
                    'Actual': row[col_name]
                })
        
        result = {
            'Transaction ID': row['Transaction ID'], 
            'Status': status, 
            'Discrepancies': discrepancies,
            **{col: row[col] for col in tolerances.keys()},
            **{col.replace('RC_', ''): row[col.replace('RC_', '')] for col in tolerances.keys()}
        }
        results.append(result)
    
    return pd.DataFrame(results)

deposit_file = st.file_uploader("Upload Deposit CSV", type=["csv"])

if deposit_file:
    deposit_df = pd.read_csv(deposit_file)
    st.write("Deposits", deposit_df.head())
    
    tolerance_inputs = {
        'RC_CLEO.Lit Sell GDR/USD - Reference': 1e-15,
        'RC_Deposit Amount USD': 1e-10,
        'RC_GDR Client Receive': 1e-10,
        'RC_COGs': 1e-10,
        'RC_Revenue': 1e-10,
        'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': 1e-10,
        'RC_Mark up rate 4 - Value - Business risk reserve': 1e-10,
        'RC_Mark up rate 3 - Value - Crypto to fiat conversion': 1e-10,
        'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': 1e-10,
        'RC_Mark up rate 1 - Value - Gold price fluctuation': 1e-10
    }

    with st.sidebar.expander("Set Tolerances", expanded=True):
        tolerances = {col: st.number_input(f"Tolerance for {col}", min_value=0.0, format="%e", value=val, step=1e-15) 
                      for col, val in tolerance_inputs.items()}

    selected_columns = st.sidebar.multiselect("Additional Columns to Display", deposit_df.columns.tolist())

    deposit_results = recalculate_and_validate_deposits(deposit_df, tolerances)
    
    display_columns = ['Transaction ID', 'Status', 'Discrepancies'] + [col for col in tolerances.keys()] + [col.replace('RC_', '') for col in tolerances.keys()] + selected_columns
    
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
    3. **Tolerances**: Provides options to set tolerances for each recalculated column to account for numerical discrepancies.
    4. **Additional Columns**: Allows users to select additional columns from the CSV to display alongside validation results.
    5. **Recalculation Logic**: Displays the formulas used to recalculate each derived column based on the uploaded data.
    The app ensures transaction validity by checking for discrepancies in recalculated values compared to original data, providing detailed status and discrepancies for each transaction.
    For any questions or feedback, please contact [Your Contact Information].
    """)

with st.expander("Recalculation Logic", expanded=True):
    st.markdown("""
    ### Recalculation Formulas
    - **RC_CLEO.Lit Sell GDR/USD - Reference**: `CLEO.Lit Buy GDR/USD - Reference * (100 + Total Markup - For Referrence) / 100`
    - **RC_Deposit Amount USD**: `Deposit Amount OC * CLEO.lit Buy Token/USD Reference`
    - **RC_GDR Client Receive**: `RC_Deposit Amount USD / RC_CLEO.Lit Sell GDR/USD - Reference`
    - **RC_COGs**: `GDR Client Receive * CLEO.Lit Buy GDR/USD - Reference`
    - **RC_Revenue**: `GDR Client Receive * RC_CLEO.Lit Sell GDR/USD - Reference`
    - **RC_Mark up rate 5 - Value - Transfer transasaction & gas fee**: `Mark up rate 5 - Transfer transasaction & gas fee / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 4 - Value - Business risk reserve**: `Mark up rate 4 - Business risk reserve / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 3 - Value - Crypto to fiat conversion**: `Mark up rate 3 - Crypto to fiat conversion / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee**: `Mark up rate 2 - Withdrawal transasaction & gas fee / Total Markup - For Referrence * (Revenue - COGs)`
    - **RC_Mark up rate 1 - Value - Gold price fluctuation**: `Mark up rate 1 - Gold Price Fluctuation / Total Markup - For Referrence * (Revenue - COGs)`
    """)