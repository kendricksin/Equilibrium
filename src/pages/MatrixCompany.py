# src/pages/CompanyAnalysis.py

import streamlit as st
import pandas as pd
import numpy as np
from special_functions.context_util import get_analysis_data, show_context_info

def calculate_company_matrix(df: pd.DataFrame):
    """Calculate matrix data for top 10 companies"""
    # Calculate total value per company to get top 10
    company_totals = df.groupby('winner')['sum_price_agree'].sum().sort_values(ascending=False)
    top_10_companies = company_totals.head(10).index.tolist()
    
    # Filter for top 10 companies
    top_companies_df = df[df['winner'].isin(top_10_companies)].copy()
    
    # Calculate price reduction percentage
    top_companies_df['price_reduction'] = ((top_companies_df['price_build'] - top_companies_df['sum_price_agree']) / 
                                         top_companies_df['price_build'] * 100)
    
    print("\nSample data for verification:")
    print(top_companies_df[['winner', 'sum_price_agree', 'price_build', 'price_reduction']].head())
    
    # Define ranges - note these are in millions since data is already in millions
    ranges = [
        ('10-50 M', 10, 50),
        ('50-100 M', 50, 100),
        ('>100 M', 100, float('inf'))
    ]
    
    # Initialize result lists for DataFrame construction
    companies = []
    data_dict = {
        ('10-50 M', 'count'): [], ('10-50 M', 'mean'): [],
        ('50-100 M', 'count'): [], ('50-100 M', 'mean'): [],
        ('>100 M', 'count'): [], ('>100 M', 'mean'): []
    }
    
    for company in top_10_companies:
        companies.append(company)
        company_df = top_companies_df[top_companies_df['winner'] == company]
        
        print(f"\nProcessing {company}")
        
        for range_name, min_val, max_val in ranges:
            range_df = company_df[
                (company_df['sum_price_agree'] >= min_val) & 
                (company_df['sum_price_agree'] < max_val)
            ]
            
            count = len(range_df)
            if count > 0:
                mean_reduction = range_df['price_reduction'].mean()
                data_dict[(range_name, 'count')].append(count)
                data_dict[(range_name, 'mean')].append(mean_reduction)
                print(f"Range {range_name}: count={count}, mean={mean_reduction:.2f}%")
            else:
                data_dict[(range_name, 'count')].append('')
                data_dict[(range_name, 'mean')].append('')
                print(f"Range {range_name}: No projects")
    
    # Create DataFrame
    result_df = pd.DataFrame({
        'Winner': companies,
        **data_dict
    })
    
    # Convert to MultiIndex columns
    result_df.columns = pd.MultiIndex.from_tuples([('Winner', '')] + 
                                                [(name, col) for name, col in data_dict.keys()])
    
    print("\nFinal Matrix DataFrame:")
    print(result_df)
    
    return result_df

def style_matrix(df):
    """Style the matrix dataframe"""
    def highlight_reduction(val):
        try:
            if isinstance(val, (float, np.floating)) and not pd.isna(val):
                return 'background-color: #FFF9C4' if val > 10 else ''
        except:
            pass
        return ''
    
    # Format count values
    count_format = lambda x: f'{int(x)}' if pd.notnull(x) and x != '' else ''
    
    # Format mean values with percentage
    mean_format = lambda x: f'{x:.2f}%' if pd.notnull(x) and x != '' else ''
    
    # Create formatter dictionary
    formatter = {
        ('10-50 M', 'count'): count_format,
        ('50-100 M', 'count'): count_format,
        ('>100 M', 'count'): count_format,
        ('10-50 M', 'mean'): mean_format,
        ('50-100 M', 'mean'): mean_format,
        ('>100 M', 'mean'): mean_format
    }
    
    # Apply formatting and highlighting
    styled = df.style.format(formatter)
    
    # Apply highlighting to mean columns
    mean_cols = [col for col in df.columns if col[1] == 'mean']
    styled = styled.map(highlight_reduction, subset=mean_cols)
    
    return styled

def CompanyAnalysis():
    """Company matrix analysis page displaying comparative metrics"""
    st.set_page_config(layout="wide")
    
    st.title("📊 Company Matrix Analysis")
    
    # Get context data
    df, context_source = get_analysis_data()
    
    # Show context information
    show_context_info()
    
    if df is not None and not df.empty:
        st.markdown("### Top 10 Companies Comparison")
        st.markdown("""
        This analysis shows a matrix comparison of the top 10 companies by total project value. 
        The matrix breaks down projects into three value ranges:
        - 10-50M Baht
        - 50-100M Baht
        - >100M Baht
        
        For each range, we show:
        - **count**: Number of projects in that range
        - **mean**: Average price reduction percentage
        
        Highlighted cells indicate significant price reductions (>10%).
        """)

        # Calculate and display matrix
        matrix_df = calculate_company_matrix(df)
        
        st.markdown("#### Company Matrix")
        st.dataframe(
            style_matrix(matrix_df),
            use_container_width=True,
            height=400
        )
        
        # Add export functionality
        st.download_button(
            "📥 Export Analysis Data",
            matrix_df.to_csv(index=False),
            "company_matrix_analysis.csv",
            "text/csv",
            key="export_matrix"
        )
        
    else:
        st.info("Please add some collections to the context to perform analysis.")

if __name__ == "__main__":
    CompanyAnalysis()