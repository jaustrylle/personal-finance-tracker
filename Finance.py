#This application allows users to track and categorize monthly expenses.

#Functions include...
#User sets a monthly budget
#User adds expenses one by one
#User can delete latest expense if typo
#Program automatically saves expense to CSV file
#Program summarizes expense totals and shows spending history
#Program recommends a daily budget depending on remaining days in the month
#Program shows remaining days of month and remaining budget in text and bar graph

class Finance:
    def __init__(self, name, category, amount) -> None:
        self.name = name
        self.category = category
        self.amount = amount

    def __repr__(self):
        return f"<Expense: {self.name}, {self.category}, ${float(self.amount):.2f}>"
