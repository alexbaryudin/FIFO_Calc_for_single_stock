import pandas as pd

# Example transaction data (buy and sell transactions)
transactions = [
    {'type': 'buy', 'quantity': 100, 'price_per_unit': 50},  # Buy 100 units at $50
    {'type': 'buy', 'quantity': 200, 'price_per_unit': 55},  # Buy 200 units at $55
    {'type': 'sell', 'quantity': 150},                      # Sell 150 units
    {'type': 'buy', 'quantity': 150, 'price_per_unit': 60},  # Buy 150 units at $60
    {'type': 'sell', 'quantity': 100},                      # Sell 100 units
]

# Convert to DataFrame
transactions_df = pd.DataFrame(transactions)

def process_transactions(transactions):
    """
    Process a list of buy and sell transactions with FIFO inventory management.
    
    :param transactions: DataFrame with columns ['type', 'quantity', 'price_per_unit' (optional)]
    :return: Total cost of sold stocks and updated inventory
    """
    inventory = []  # List to hold the inventory in FIFO order
    total_cost_of_sales = 0  # Track the cost of sales

    for _, transaction in transactions.iterrows():
        if transaction['type'] == 'buy':
            # Add the purchased stocks to the inventory
            inventory.append({
                'quantity': transaction['quantity'],
                'price_per_unit': transaction['price_per_unit']
            })
        elif transaction['type'] == 'sell':
            sell_quantity = transaction['quantity']
            sell_cost = 0  # Cost of the current sell transaction

            # Apply FIFO logic for sales
            while sell_quantity > 0:
                if not inventory:
                    raise ValueError("Not enough stock to sell the requested quantity.")

                batch = inventory[0]  # Get the oldest batch
                if batch['quantity'] <= sell_quantity:
                    # Use up the entire batch
                    sell_cost += batch['quantity'] * batch['price_per_unit']
                    sell_quantity -= batch['quantity']
                    inventory.pop(0)  # Remove the batch from inventory
                else:
                    # Partially use the batch
                    sell_cost += sell_quantity * batch['price_per_unit']
                    batch['quantity'] -= sell_quantity
                    sell_quantity = 0

            total_cost_of_sales += sell_cost
            print(f"Cost of selling {transaction['quantity']} units: ${sell_cost}")

    return total_cost_of_sales, inventory

# Process the transactions
total_cost, final_inventory = process_transactions(transactions_df)

# Output results
print(f"Total cost of sold stocks: ${total_cost}")
print("Final inventory state:")
for item in final_inventory:
    print(item)
