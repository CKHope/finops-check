import streamlit as st
import pandas as pd
import numpy as np

def load_csv(file):
    return pd.read_csv(file)

def recalculate(df):
    df['Recalculated Transaction Fee Oc'] = df['Transaction Fee - Rate'].astype(float) * df['Transfer Amount DC'].astype(float)
    return df

def compare_results(df):
    df['Transaction Fee Oc Matching'] = np.isclose(df['Transaction Fee Oc'].astype(float), 
                                                   df['Recalculated Transaction Fee Oc'], 
                                                   rtol=1e-5, atol=1e-8)
    df['Transaction Fee Oc Difference'] = df['Transaction Fee Oc'].astype(float) - df['Recalculated Transaction Fee Oc']
    df['Transfer Amount Matching'] = df['Transfer Amount DC'] == df['Destination Amount DC']
    df['Currency Matching'] = df['Original Currency - OC'] == df['Destination Currency - DC']
    df['All Matching'] = df['Transaction Fee Oc Matching'] & df['Transfer Amount Matching'] & df['Currency Matching']
    return df

def main():
    st.title("Check Transfer Transaction")  # Updated title here

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = load_csv(uploaded_file)
        st.write("Original Data:")
        st.dataframe(df)

        recalculated_df = recalculate(df)
        comparison_results = compare_results(recalculated_df)
        
        default_columns = ['Record ID', 
                           'Transaction Fee Oc', 'Recalculated Transaction Fee Oc', 'Transaction Fee Oc Matching', 'Transaction Fee Oc Difference',
                           'Transfer Amount DC', 'Destination Amount DC', 'Transfer Amount Matching',
                           'Original Currency - OC', 'Destination Currency - DC', 'Currency Matching',
                           'All Matching']
        
        additional_columns = st.multiselect(
            "Select additional columns to display in Comparison Results:",
            options=[col for col in df.columns if col not in default_columns],
            default=[]
        )
        
        display_columns = default_columns + additional_columns
        
        st.write("Comparison Results:")
        st.dataframe(comparison_results[display_columns])

        total_records = len(comparison_results)
        all_matching_records = comparison_results['All Matching'].sum()
        non_matching_records = total_records - all_matching_records

        st.write(f"Total Records: {total_records}")
        st.write(f"Fully Matching Records: {all_matching_records}")
        st.write(f"Non-matching Records: {non_matching_records}")

        if non_matching_records > 0:
            st.write("Non-matching Records:")
            st.dataframe(comparison_results[~comparison_results['All Matching']][display_columns])

        st.write("Mismatch Breakdown:")
        st.write(f"Transaction Fee Oc Mismatches: {total_records - comparison_results['Transaction Fee Oc Matching'].sum()}")
        st.write(f"Transfer Amount Mismatches: {total_records - comparison_results['Transfer Amount Matching'].sum()}")
        st.write(f"Currency Mismatches: {total_records - comparison_results['Currency Matching'].sum()}")

if __name__ == "__main__":
    main()