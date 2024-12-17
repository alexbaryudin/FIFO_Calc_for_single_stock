import argparse
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, Extra
from typing import List, Optional
import pandas as pd
import yfinance as yf

app = FastAPI()

# Updated Input Model for API
# version history - removed "/" from "/calculate_fifo"
##### 
class Transaction(BaseModel):
    Stock_Name: str = Field(alias="stock_name_t")
    Number_of_Shares: float = Field(alias="number_of_shares")
    Stock_Price: Optional[float] = Field(alias="stock_price")
    
    class Config:
        extra = Extra.allow  # Allows additional fields in the input

class TransactionsInput(BaseModel):
    transactions: List[Transaction]
    current_price: Optional[float] = None

    class Config:
        populate_by_name = True  # For Pydantic v2 compatibility

# Utility functions
def get_current_stock_price(stock_name=None, manual_price=None):
    """
    Fetch the current stock price using yfinance or use the manually provided price.
    """
    if manual_price is not None:
        return manual_price
    elif stock_name:
        try:
            stock = yf.Ticker(stock_name)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            return current_price
        except Exception as e:
            raise ValueError(f"Failed to fetch stock price for {stock_name}: {e}")
    else:
        raise ValueError("Either stock_name or manual_price must be provided.")

def process_fifo_transactions(transactions, current_price):
    """
    Process buy and sell transactions using FIFO and calculate potential gain/loss for remaining inventory.
    """
    inventory = []

    for transaction in transactions:
        stock_name = transaction.Stock_Name
        num_shares = transaction.Number_of_Shares
        purchase_price = transaction.Stock_Price

        if num_shares > 0:
            inventory.append({
                "quantity": num_shares,
                "price_per_unit": purchase_price
            })
        elif num_shares < 0:
            sell_quantity = abs(num_shares)
            while sell_quantity > 0:
                if not inventory:
                    raise ValueError("Not enough stock to sell the requested quantity.")
                batch = inventory[0]
                if batch["quantity"] <= sell_quantity:
                    sell_quantity -= batch["quantity"]
                    inventory.pop(0)
                else:
                    batch["quantity"] -= sell_quantity
                    sell_quantity = 0

    total_inventory_cost = sum(batch["quantity"] * batch["price_per_unit"] for batch in inventory)
    total_inventory_quantity = sum(batch["quantity"] for batch in inventory)
    total_inventory_value = total_inventory_quantity * current_price
    gain_loss = total_inventory_value - total_inventory_cost

    return {
        "remaining_inventory": inventory,
        "total_inventory_cost": total_inventory_cost,
        "total_inventory_value": total_inventory_value,
        "potential_gain_loss": gain_loss
    }

@app.post("/calculate_fifo")
def calculate_fifo(input_data: TransactionsInput):
    """
    API Endpoint for calculating potential gain/loss for remaining inventory using FIFO.
    """
    try:
        transactions = input_data.transactions
        stock_name = transactions[0].Stock_Name if transactions else None

        if input_data.current_price is None:
            if stock_name is None:
                raise HTTPException(status_code=400, detail="Stock name not found in input data.")
            current_price = get_current_stock_price(stock_name=stock_name)
        else:
            current_price = input_data.current_price

        result = process_fifo_transactions(transactions, current_price)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def run_interactively():
    """
    Interactive mode for running the FIFO stock calculator.
    """
    print("Running in interactive mode...")
    input_method = input("Enter 'file' to provide a JSON file or 'direct' to enter JSON directly: ").strip().lower()

    if input_method == "file":
        file_path = input("Enter the path to the JSON file: ").strip()
        try:
            with open(file_path, "r") as f:
                transactions_data = json.load(f)
        except FileNotFoundError:
            print("File not found. Please check the file path and try again.")
            return
        except json.JSONDecodeError:
            print("Invalid JSON in the file. Please check the file content.")
            return
    elif input_method == "direct":
        try:
            transactions_data = input("Enter transaction data in JSON format: ").strip()
            transactions_data = json.loads(transactions_data)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
            return
    else:
        print("Invalid option. Exiting.")
        return

    if not transactions_data or not isinstance(transactions_data, list):
        print("Invalid or empty transactions data. Please provide a list of transactions.")
        return

    # Convert raw dictionaries into Pydantic Transaction objects
    try:
        transactions = [Transaction.parse_obj(tx) for tx in transactions_data]
    except Exception as e:
        print(f"Error parsing transactions: {e}")
        return

    stock_name = transactions[0].Stock_Name if transactions else None
    if not stock_name:
        print("Stock name could not be determined from input data. Exiting.")
        return

    current_price = input("Enter the current stock price (or press Enter to fetch it automatically): ").strip()
    current_price = float(current_price) if current_price else get_current_stock_price(stock_name)

    try:
        result = process_fifo_transactions(transactions, current_price)
        print(f"\nRemaining Inventory: {result['remaining_inventory']}")
        print(f"Total Inventory Cost: ${result['total_inventory_cost']:.2f}")
        print(f"Total Inventory Value: ${result['total_inventory_value']:.2f}")
        print(f"Potential Gain/Loss: ${result['potential_gain_loss']:.2f}")
    except Exception as e:
        print(f"An error occurred during processing: {e}")


def main():
    """
    Main function to run the script in either API or interactive mode.
    """
    parser = argparse.ArgumentParser(description="Run the FIFO stock inventory calculator.")
    parser.add_argument("--mode", choices=["api", "interactive"], default="interactive",
                        help="Choose the mode: 'api' to run as a web server or 'interactive' to run interactively.")
    args = parser.parse_args()

    if args.mode == "api":
        import uvicorn
        print("Starting API server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.mode == "interactive":
        run_interactively()

if __name__ == "__main__":
    main()
