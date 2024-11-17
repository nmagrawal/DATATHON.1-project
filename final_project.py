import streamlit as st
import requests
from transformers import pipeline
import pandas as pd
import plotly.express as px

# Function to fetch actual Free Cash Flows (FCF)
def fetch_actual_free_cash_flows(api_key, ticker):
    url = f"https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/{ticker}?apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    # Extract cash flow data
    statements = data.get("financials", [])
    free_cash_flows = []
    
    for item in statements:
        try:
            operating_cash_flow = float(item.get("Operating Cash Flow", 0))
            capex = float(item.get("Capital Expenditure", 0))
            fcf = operating_cash_flow - capex
            free_cash_flows.append(fcf)
        except ValueError:
            # Handle missing or non-numeric data
            free_cash_flows.append(0.0)
    
    return free_cash_flows

# Function to fetch outstanding shares
def fetch_outstanding_shares(api_key, ticker):
    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    # Extract outstanding shares
    if data and isinstance(data, list):
        try:
            market_cap = float(data[0].get("mktCap", 0))
            price = float(data[0].get("price", 1))
            outstanding_shares = market_cap / price  # Market Cap / Share Price
            return outstanding_shares
        except (ValueError, ZeroDivisionError):
            return None
    return None

# Function to fetch historic share prices
def fetch_historic_share_prices(api_key, ticker):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    # Extract historical prices
    if "historical" in data:
        prices = [
            {"date": item["date"], "close": item["close"]}
            for item in data["historical"]
        ]
        return prices
    return None

# AI-Powered Future Cash Flow Estimator
def predict_future_cash_flows(historical_cash_flows, growth_forecast):
#    sentiment_analysis = pipeline(
#       "sentiment-analysis", 
#        model="distilbert/distilbert-base-uncased-finetuned-sst-2-english"
#    )
#    sentiment = sentiment_analysis(growth_forecast)[0]

    growth_rate = 0.05  # Default growth rate
#    if sentiment['label'] == "POSITIVE":
#        growth_rate += 0.02  # Increase growth rate for positive sentiment
#    elif sentiment['label'] == "NEGATIVE":
#        growth_rate -= 0.02  # Decrease growth rate for negative sentiment

    future_cash_flows = []
    last_cash_flow = historical_cash_flows[-1]

    for year in range(5):  # Predict for 5 years
        next_cash_flow = last_cash_flow * (1 + growth_rate)
        future_cash_flows.append(next_cash_flow)
        last_cash_flow = next_cash_flow

    return [round(cf, 2) for cf in future_cash_flows]

# DCF Analysis
def dcf_analysis(free_cash_flows, discount_rate, terminal_growth_rate):
    # Calculate discounted free cash flows
    discounted_cash_flows = sum(fcf / (1 + discount_rate)**i for i, fcf in enumerate(free_cash_flows, 1))
    
    # Calculate terminal value
    terminal_value = free_cash_flows[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    discounted_terminal_value = terminal_value / (1 + discount_rate)**len(free_cash_flows)

    # Total DCF valuation
    total_valuation = discounted_cash_flows + discounted_terminal_value
    return total_valuation

# Streamlit App
def main():
    st.title("Financial Analysis and Valuation Tool")

    # Sidebar inputs
    st.sidebar.title("User Input")
    api_key = st.sidebar.text_input("Enter your API Key", value="")  # API Key as user input
    ticker = st.sidebar.text_input("Enter the company's ticker symbol (e.g., AAPL, META):", value="META").upper()

    if st.sidebar.button("Analyze"):
        # Validate API key
        if not api_key:
            st.error("Please enter a valid API key.")
            return

        # Fetch data
        st.write("Fetching financial data...")
        historical_cash_flows = fetch_actual_free_cash_flows(api_key, ticker)
        outstanding_shares = fetch_outstanding_shares(api_key, ticker)
        historic_prices = fetch_historic_share_prices(api_key, ticker)

        # Validate data
        if not historical_cash_flows or all(cf == 0 for cf in historical_cash_flows):
            st.error("Error: Unable to fetch valid Free Cash Flow data. Check the ticker or API response.")
            return
        if not outstanding_shares:
            st.error("Error: Unable to fetch valid outstanding shares data.")
            return
        if not historic_prices:
            st.error("Error: Unable to fetch historical share price data.")
            return

        st.write(f"Free Cash Flows (last 5 years): {historical_cash_flows}")
        st.write(f"Outstanding Shares: {outstanding_shares}")

        # Predict future cash flows
        growth_forecast = "The company is expected to grow significantly over the next 5 years."
        future_cash_flows = predict_future_cash_flows(historical_cash_flows, growth_forecast)
        st.write(f"Predicted Future Cash Flows (5 years): {future_cash_flows}")

        # Perform DCF Analysis
        discount_rate = 0.07
        terminal_growth_rate = 0.04
        valuation = dcf_analysis(future_cash_flows, discount_rate, terminal_growth_rate)
        st.write(f"AI-Augmented Business Valuation (DCF Method): ${valuation:,.2f}")

        # Calculate Share Price
        share_price = valuation / outstanding_shares
        st.write(f"Estimated Share Price: ${share_price:.2f}")

        # Display historical share prices as a time series graph
        st.subheader("Historical Share Prices")
        historic_prices_df = pd.DataFrame(historic_prices)
        fig = px.line(historic_prices_df, x="date", y="close", title="Historic Share Prices Over Time", labels={"date": "Date", "close": "Close Price"})
        st.plotly_chart(fig)

# Run the app
if __name__ == "__main__":
    main()
