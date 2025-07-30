from shiny.express import input, ui, render
from shiny import reactive, req
import pandas as pd
import numpy as np
from datetime import datetime, date
import calendar
import io
import os

# Budget categories
BUDGET_CATEGORIES = [
    "Housing", "Food", "Clothing", "Education", "Transportation", 
    "Communications", "Health", "Recreation", "Other", "Debt", 
    "Fast Offering", "Tithing", "Income"
]

# Initialize sample data (in a real app, this would come from Google Drive)
def get_sample_data():
    df = pd.DataFrame({
        'Date': [
            date(2024, 1, 15), date(2024, 1, 20), date(2024, 1, 25),
            date(2024, 2, 5), date(2024, 2, 10), date(2024, 2, 15)
        ],
        'Description': [
            'Rent Payment', 'Grocery Store', 'Gas Station',
            'Internet Bill', 'Restaurant', 'Salary'
        ],
        'Amount': [-1200.00, -85.50, -45.00, -75.00, -32.00, 3500.00],
        'Vendor': [
            'Property Management', 'Safeway', 'Shell',
            'Comcast', 'Local Diner', 'Company'
        ],
        'Budget_Category': [
            'Housing', 'Food', 'Transportation',
            'Communications', 'Food', 'Income'
        ],
        'Buyer': ['John', 'Jane', 'John', 'John', 'Jane', 'John'],
        'Notes': [
            'Monthly rent for apartment', 'Weekly grocery shopping', 'Fill up tank',
            'Monthly internet service', 'Dinner with friends', 'Bi-weekly paycheck'
        ]
    })
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# Reactive value to store our data
budget_data = reactive.value(get_sample_data())

ui.h1("JnK Budget Tracking Tool")

with ui.layout_sidebar():
    with ui.sidebar():
        ui.h3("Add New Transaction")
        ui.input_date("date", "Date", value=date.today())
        ui.input_text("description", "Description", placeholder="Enter description")
        ui.input_numeric("amount", "Amount", value=0, step=0.01)
        ui.input_text("vendor", "Vendor", placeholder="Enter vendor name")
        ui.input_select("category", "Budget Category", choices=BUDGET_CATEGORIES)
        ui.input_text("buyer", "Buyer", placeholder="Enter buyer name")
        ui.input_text_area("notes", "Notes", placeholder="Enter any additional notes (optional)", rows=3)
        ui.input_action_button("add_transaction", "Add Transaction", class_="btn-primary")
        ui.hr()
        ui.h4("Data Management")
        ui.p("Note: In production, this would sync with Google Drive")
        ui.input_action_button("clear_data", "Clear All Data", class_="btn-warning")
    
    with ui.layout_columns(col_widths=[6, 6]):
        with ui.card():
            ui.card_header("Monthly Category Totals")
            
            @render.ui
            def month_selector():
                data = budget_data()
                if len(data) == 0:
                    return ui.p("No data available")
                
                # Get unique year-month combinations
                data['YearMonth'] = data['Date'].dt.to_period('M')
                unique_months = sorted(data['YearMonth'].unique(), reverse=True)
                
                if len(unique_months) == 0:
                    return ui.p("No data available")
                
                month_choices = {str(month): f"{calendar.month_name[month.month]} {month.year}" 
                                for month in unique_months}
                
                return ui.input_select(
                    "selected_month", 
                    "Select Month", 
                    choices=month_choices,
                    selected=str(unique_months[0]) if unique_months else None
                )
            
            @render.data_frame
            def monthly_totals():
                data = budget_data()
                
                if len(data) == 0 or input.selected_month() is None:
                    return pd.DataFrame(columns=['Category', 'Total', 'Transaction Count'])
                
                # Filter data for selected month
                selected_period = pd.Period(input.selected_month())
                data['YearMonth'] = data['Date'].dt.to_period('M')
                monthly_data = data[data['YearMonth'] == selected_period]
                
                if len(monthly_data) == 0:
                    return pd.DataFrame(columns=['Category', 'Total', 'Transaction Count'])
                
                # Calculate totals by category
                category_totals = monthly_data.groupby('Budget_Category').agg({
                    'Amount': ['sum', 'count']
                }).round(2)
                
                category_totals.columns = ['Total', 'Transaction Count']
                category_totals = category_totals.reset_index()
                category_totals.columns = ['Category', 'Total', 'Transaction Count']
                
                # Format the Total column as currency
                category_totals['Total'] = category_totals['Total'].apply(lambda x: f"${x:,.2f}")
                
                return category_totals.sort_values('Category')
        
        with ui.card():
            ui.card_header("All Transactions")
            
            @render.data_frame
            def all_transactions():
                data = budget_data()
                if len(data) == 0:
                    return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Vendor', 'Category', 'Buyer', 'Notes'])
                
                # Format for display
                display_data = data.copy()
                display_data['Amount'] = display_data['Amount'].apply(lambda x: f"${x:,.2f}")
                display_data['Date'] = display_data['Date'].dt.strftime('%Y-%m-%d')
                display_data = display_data.rename(columns={'Budget_Category': 'Category'})
                
                # Reorder columns to put Notes at the end
                column_order = ['Date', 'Description', 'Amount', 'Vendor', 'Category', 'Buyer', 'Notes']
                display_data = display_data[column_order]
                
                return display_data.sort_values('Date', ascending=False)

@reactive.effect
@reactive.event(input.add_transaction)
def add_new_transaction():
    req(input.description(), input.vendor(), input.buyer())
    
    # Create new transaction
    new_transaction = pd.DataFrame({
        'Date': [pd.to_datetime(input.date())],  # Convert to datetime
        'Description': [input.description()],
        'Amount': [input.amount()],
        'Vendor': [input.vendor()],
        'Budget_Category': [input.category()],
        'Buyer': [input.buyer()],
        'Notes': [input.notes() if input.notes() else ""]  # Handle empty notes
    })
    
    # Add to existing data
    current_data = budget_data()
    updated_data = pd.concat([current_data, new_transaction], ignore_index=True)
    budget_data.set(updated_data)

@reactive.effect
@reactive.event(input.clear_data)
def clear_all_data():
    empty_df = pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Vendor', 'Budget_Category', 'Buyer', 'Notes'])
    empty_df['Date'] = pd.to_datetime(empty_df['Date'])  # Ensure Date column is datetime type
    budget_data.set(empty_df)
