import streamlit as st
import pandas as pd
from decimal import Decimal, getcontext

st.title('Cryptocurrency Deposit Transaction Validator')

# Set a high precision for decimal calculations
getcontext().prec = 28

def get_max_precision(numbers):
    return max(abs(Decimal(str(n)).as_tuple().exponent) for n in numbers if n != 0)

# Helper function to perform high-precision calculation
def high_precision_calc(func):
    def wrapper(row):
        # Extract the values used in the calculation
        values = [row[col] for col in row.index if pd.notna(row[col]) and isinstance(row[col], (int, float))]
        max_precision = get_max_precision(values)
        
        # Perform the calculation using Decimal for high precision
        result = func(*[Decimal(str(v)) for v in values])
        
        # Round to the maximum precision encountered
        return float(round(result, max_precision))
    return wrapper

# Updated recalculations with high-precision wrapper
recalculations = {
    'RC_CLEO.Lit Sell GDR/USD - Reference': high_precision_calc(lambda a, b: a * (Decimal('100') + b) / Decimal('100')),
    'RC_Deposit Amount USD': high_precision_calc(lambda a, b: a * b),
    'RC_GDR Client Receive': high_precision_calc(lambda a, b: a / b),
    'RC_COGs': high_precision_calc(lambda a, b: a * b),
    'RC_Revenue': high_precision_calc(lambda a, b: a * b),
    'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': high_precision_calc(lambda a, b, c, d: a / b * (c - d)),
    'RC_Mark up rate 4 - Value - Business risk reserve': high_precision_calc(lambda a, b, c, d: a / b * (c - d)),
    'RC_Mark up rate 3 - Value - Crypto to fiat conversion': high_precision_calc(lambda a, b, c, d: a / b * (c - d)),
    'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': high_precision_calc(lambda a, b, c, d: a / b * (c - d)),
    'RC_Mark up rate 1 - Value - Gold price fluctuation': high_precision_calc(lambda a, b, c, d: a / b * (c - d))
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

deposit_file = st.file_uploader("Upload Deposit CSV", type=["csv"])

if deposit_file:
    deposit_df = pd.read_csv(deposit_file)
    st.write("Deposits", deposit_df.head())
    
    tolerance_inputs = {
        'RC_CLEO.Lit Sell GDR/USD - Reference': 1e-2,
        'RC_Deposit Amount USD': 1e-2,
        'RC_GDR Client Receive': 1e-2,
        'RC_COGs': 1e-2,
        'RC_Revenue': 1e-2,
        'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': 1e-2,
        'RC_Mark up rate 4 - Value - Business risk reserve': 1e-2,
        'RC_Mark up rate 3 - Value - Crypto to fiat conversion': 1e-2,
        'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': 1e-2,
        'RC_Mark up rate 1 - Value - Gold price fluctuation': 1e-2
    }

    with st.sidebar.expander("Set Tolerances", expanded=True):
        tolerances = {col: st.number_input(f"Tolerance for {col}", min_value=0.0, format="%e", value=val, step=1e-15) 
                      for col, val in tolerance_inputs.items()}

    selected_columns = st.sidebar.multiselect("Additional Columns to Display", deposit_df.columns.tolist())

    deposit_results = recalculate_and_validate_deposits(deposit_df, tolerances)
    
    display_columns = ['Transaction ID', 'Status', 'Discrepancies']
    for col in tolerances.keys():
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
    3. **High-Precision Calculations**: Uses Python's Decimal type for high-precision arithmetic, maintaining the maximum precision of input numbers.
    4. **Tolerances**: Provides options to set tolerances for each recalculated column to account for numerical discrepancies.
    5. **Additional Columns**: Allows users to select additional columns from the CSV to display alongside validation results.
    6. **Recalculation Logic**: Displays the formulas used to recalculate each derived column based on the uploaded data.
    The app ensures transaction validity by checking for discrepancies in recalculated values compared to original data, providing detailed status and discrepancies for each transaction.
    For any questions or feedback, please contact [Your Contact Information].
    """)

with st.expander("Recalculation Logic", expanded=True):
    st.markdown("""
    ### Recalculation Formulas (with High-Precision Calculation)
    All formulas are wrapped in a high-precision calculation function that uses Python's Decimal type for accurate arithmetic and maintains the maximum precision of input numbers.

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