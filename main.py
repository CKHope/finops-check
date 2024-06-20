import streamlit as st
import pandas as pd

# Streamlit app title
st.title('Cryptocurrency Deposit Transaction Validator')

# Step 1: Upload Deposit CSV file
deposit_file = st.file_uploader("Upload Deposit CSV", type=["csv"])

# Step 2: Define recalculation, validation, and comparison logic for deposit transactions
def recalculate_and_validate_deposits(df, tolerances=None):
    results = []

    if tolerances is None:
        tolerances = {
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

    # Define recalculations
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

    # Apply recalculations
    for col, func in recalculations.items():
        df[col] = df.apply(func, axis=1)

    for index, row in df.iterrows():
        status = "Valid"
        discrepancies = []

        # Example validation logic: deposit amount should be positive
        if row['Amount Dc'] <= 0:
            status = "Invalid - Amount should be positive"
        
        # Comparison logic with custom tolerance for each recalculated column
        for col_name in tolerances:
            if col_name in df.columns:
                if abs(row[col_name] - row[col_name.replace('RC_', '')]) > tolerances[col_name]:
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
            'RC_CLEO.Lit Sell GDR/USD - Reference': row['RC_CLEO.Lit Sell GDR/USD - Reference'],
            'CLEO.Lit Sell GDR/USD - Reference': row['CLEO.Lit Sell GDR/USD - Reference'],
            'RC_Deposit Amount USD': row['RC_Deposit Amount USD'],
            'Deposit Amount USD': row['Deposit Amount USD'],
            'RC_GDR Client Receive': row['RC_GDR Client Receive'],
            'GDR Client Receive': row['GDR Client Receive'],
            'RC_COGs': row['RC_COGs'],
            'COGs': row['COGs'],
            'RC_Revenue': row['RC_Revenue'],
            'Revenue': row['Revenue'],
            'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': row['RC_Mark up rate 5 - Value - Transfer transasaction & gas fee'],
            'Mark up rate 5 - Value - Transfer transasaction & gas fee': row['Mark up rate 5 - Value - Transfer transasaction & gas fee'],
            'RC_Mark up rate 4 - Value - Business risk reserve': row['RC_Mark up rate 4 - Value - Business risk reserve'],
            'Mark up rate 4 - Value - Business risk reserve': row['Mark up rate 4 - Value - Business risk reserve'],
            'RC_Mark up rate 3 - Value - Crypto to fiat conversion': row['RC_Mark up rate 3 - Value - Crypto to fiat conversion'],
            'Mark up rate 3 - Value - Crypto to fiat conversion': row['Mark up rate 3 - Value - Crypto to fiat conversion'],
            'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': row['RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee'],
            'Mark up rate 2 - Value - Withdrawal transasaction & gas fee': row['Mark up rate 2 - Value - Withdrawal transasaction & gas fee'],
            'RC_Mark up rate 1 - Value - Gold price fluctuation': row['RC_Mark up rate 1 - Value - Gold price fluctuation'],
            'Mark up rate 1 - Value - Gold price fluctuation': row['Mark up rate 1 - Value - Gold price fluctuation']
        }

        results.append(result)
    
    return pd.DataFrame(results)

# Step 3: Read and validate the deposit CSV file
if deposit_file is not None:
    try:
        deposit_df = pd.read_csv(deposit_file)
        st.write("Deposits")
        st.write(deposit_df.head())
        
        # Streamlit widgets for tolerance inputs
        with st.sidebar.expander("Set Tolerances", expanded=True):
            tolerance_rc_cleo_lit_sell = st.number_input("Tolerance for RC_CLEO.Lit Sell GDR/USD - Reference", min_value=0.0, format="%e", value=1e-15, step=1e-16)
            tolerance_rc_deposit_amount = st.number_input("Tolerance for RC_Deposit Amount USD", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_gdr_receive = st.number_input("Tolerance for RC_GDR Client Receive", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_cogs = st.number_input("Tolerance for RC_COGs", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_revenue = st.number_input("Tolerance for RC_Revenue", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_mark_up_rate_5 = st.number_input("Tolerance for RC_Mark up rate 5 - Value - Transfer transasaction & gas fee", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_mark_up_rate_4 = st.number_input("Tolerance for RC_Mark up rate 4 - Value - Business risk reserve", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_mark_up_rate_3 = st.number_input("Tolerance for RC_Mark up rate 3 - Value - Crypto to fiat conversion", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_mark_up_rate_2 = st.number_input("Tolerance for RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee", min_value=0.0, format="%e", value=1e-10, step=1e-15)
            tolerance_rc_mark_up_rate_1 = st.number_input("Tolerance for RC_Mark up rate 1 - Value - Gold price fluctuation", min_value=0.0, format="%e", value=1e-10, step=1e-15)

        # Allow user to select additional columns to display
        with st.sidebar.expander("Select Additional Columns to Display", expanded=True):
            all_columns = deposit_df.columns.tolist()
            selected_columns = st.multiselect("Additional Columns", all_columns)

        # Define tolerances dictionary based on user inputs
        custom_tolerances = {
            'RC_CLEO.Lit Sell GDR/USD - Reference': tolerance_rc_cleo_lit_sell,
            'RC_Deposit Amount USD': tolerance_rc_deposit_amount,
            'RC_GDR Client Receive': tolerance_rc_gdr_receive,
            'RC_COGs': tolerance_rc_cogs,
            'RC_Revenue': tolerance_rc_revenue,
            'RC_Mark up rate 5 - Value - Transfer transasaction & gas fee': tolerance_rc_mark_up_rate_5,
            'RC_Mark up rate 4 - Value - Business risk reserve': tolerance_rc_mark_up_rate_4,
            'RC_Mark up rate 3 - Value - Crypto to fiat conversion': tolerance_rc_mark_up_rate_3,
            'RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee': tolerance_rc_mark_up_rate_2,
            'RC_Mark up rate 1 - Value - Gold price fluctuation': tolerance_rc_mark_up_rate_1
        }

        deposit_results = recalculate_and_validate_deposits(deposit_df, tolerances=custom_tolerances)
        
        # Display results
        st.subheader("Validation Results")
        
        # Convert discrepancies list to a readable format for display
        display_results = deposit_results.copy()
        display_results['Discrepancies'] = display_results['Discrepancies'].apply(lambda x: ', '.join([f"{item['Column']}: Expected {item['Expected']}, Actual {item['Actual']}" for item in x]))

        # Include selected additional columns in display
        display_columns = ['Transaction ID', 'Status', 'Discrepancies'] + selected_columns
        display_results = display_results[display_columns]

        st.write(display_results)
        
        # Check for any invalid transactions
        invalid_count = (deposit_results['Status'] != 'Valid').sum()
        if invalid_count > 0:
            st.error(f"There are {invalid_count} invalid transactions. Please check details.")
        else:
            st.success("All transactions are valid.")
    
    except Exception as e:
        st.error(f"Error: {e}")

# Collapsible section for app description
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

# Collapsible section for recalculation logic
with st.expander("Recalculation Logic", expanded=True):
    st.markdown("""
    ### Recalculation Formulas

    - **RC_CLEO.Lit Sell GDR/USD - Reference**:
      ```
      RC_CLEO.Lit Sell GDR/USD - Reference = CLEO.Lit Buy GDR/USD - Reference * (100 + Total Markup - For Referrence) / 100
      ```

    - **RC_Deposit Amount USD**:
      ```
      RC_Deposit Amount USD = Deposit Amount OC * CLEO.lit Buy Token/USD Reference
      ```

    - **RC_GDR Client Receive**:
      ```
      RC_GDR Client Receive = RC_Deposit Amount USD / RC_CLEO.Lit Sell GDR/USD - Reference
      ```

    - **RC_COGs**:
      ```
      RC_COGs = GDR Client Receive * CLEO.Lit Buy GDR/USD - Reference
      ```

    - **RC_Revenue**:
      ```
      RC_Revenue = GDR Client Receive * RC_CLEO.Lit Sell GDR/USD - Reference
      ```

    - **RC_Mark up rate 5 - Value - Transfer transasaction & gas fee**:
      ```
      RC_Mark up rate 5 - Value - Transfer transasaction & gas fee = Mark up rate 5 - Transfer transasaction & gas fee / Total Markup - For Referrence * (Revenue - COGs)
      ```

    - **RC_Mark up rate 4 - Value - Business risk reserve**:
      ```
      RC_Mark up rate 4 - Value - Business risk reserve = Mark up rate 4 - Business risk reserve / Total Markup - For Referrence * (Revenue - COGs)
      ```

    - **RC_Mark up rate 3 - Value - Crypto to fiat conversion**:
      ```
      RC_Mark up rate 3 - Value - Crypto to fiat conversion = Mark up rate 3 - Crypto to fiat conversion / Total Markup - For Referrence * (Revenue - COGs)
      ```

    - **RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee**:
      ```
      RC_Mark up rate 2 - Value - Withdrawal transasaction & gas fee = Mark up rate 2 - Withdrawal transasaction & gas fee / Total Markup - For Referrence * (Revenue - COGs)
      ```

    - **RC_Mark up rate 1 - Value - Gold price fluctuation**:
      ```
      RC_Mark up rate 1 - Value - Gold price fluctuation = Mark up rate 1 - Gold Price Fluctuation / Total Markup - For Referrence * (Revenue - COGs)
      ```
    """)