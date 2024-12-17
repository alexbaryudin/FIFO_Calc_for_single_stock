from collections import deque

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.purchases = deque()
        self.total_shares = 0

    def buy(self, shares, price):
        self.purchases.append((shares, price))
        self.total_shares += shares

    def sell(self, shares):
        shares_sold = shares
        total_cost = 0
        while shares_sold > 0:
            if not self.purchases:
                raise ValueError("Not enough shares to sell")
            oldest_purchase = self.purchases[0]
            if oldest_purchase[0] <= shares_sold:
                shares_sold -= oldest_purchase[0]
                total_cost += oldest_purchase[0] * oldest_purchase[1]
                self.purchases.popleft()
            else:
                total_cost += shares_sold * oldest_purchase[1]
                self.purchases[0] = (oldest_purchase[0] - shares_sold, oldest_purchase[1])
                shares_sold = 0
        self.total_shares -= shares
        return total_cost / shares

    def get_average_price(self):
        if self.total_shares == 0:
            return 0
        return sum(shares * price for shares, price in self.purchases) / self.total_shares

# Example usage
aapl = Stock("AAPL")
aapl.buy(100, 150)  # Buy 100 shares at $150
aapl.buy(50, 160)   # Buy 50 shares at $160
print(f"Average purchase price: ${aapl.get_average_price():.2f}")
sell_price = aapl.sell(75)  # Sell 75 shares
print(f"FIFO sell price: ${sell_price:.2f}")
print(f"Remaining average purchase price: ${aapl.get_average_price():.2f}")