import re
import calendar
import datetime
import tkinter
import customtkinter
import matplotlib.pyplot as plt
from Finance import Finance
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Global Flag ---
app_closing = False

# --- Suppress Tkinter bgerror to avoid some errors after app is destroyed ---
def silent_bgerror(*args, **kwargs):
    pass
tkinter.Tk.report_callback_exception = silent_bgerror

# --- Settings ---
customtkinter.set_appearance_mode("Dark")  # Dark mode for sleek UI
customtkinter.set_default_color_theme("dark-blue")

expense_file_path = "Finances.csv"
budget_file_path = "Budget.txt"

categories = [
    "Food", "Pets", "Travel", "Home", "Transportation",
    "Work", "Healthcare", "Fun", "Misc"
]

# --- Patch CustomTkinter internals to no-op on closing to avoid callbacks after destroy ---
def patch_customtkinter_callbacks():
    def safe_noop(*args, **kwargs):
        if app_closing:
            return
    # Try patching known internal update methods that cause the errors
    try:
        customtkinter.CTkBaseClass.check_dpi_scaling = safe_noop
    except AttributeError:
        pass
    try:
        customtkinter.CTkButton._click_animation = safe_noop
    except AttributeError:
        pass

# --- Functions ---
def load_budget():
    try:
        with open(budget_file_path, "r") as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 2000.0  # default budget

def save_budget(new_budget):
    if app_closing or not app.winfo_exists():
        return
    with open(budget_file_path, "w") as f:
        f.write(str(new_budget))

def update_budget():
    if app_closing or not app.winfo_exists():
        return
    try:
        new_budget = float(budget_input_var.get())
        global budget
        budget = new_budget
        save_budget(new_budget)
        budget_label.configure(text=f"Monthly Budget: ${budget:.2f}")
        status_label.configure(text="✅ Budget updated!", text_color="green")
        budget_input_var.set("")
        summarize_expenses()  # refresh summary/chart
    except ValueError:
        status_label.configure(text="❌ Invalid budget amount", text_color="red")

def update_spending_history():
    if app_closing or not app.winfo_exists():
        return
    try:
        with open(expense_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        history_box.configure(state="normal")
        history_box.delete("1.0", "end")
        history_box.insert("1.0", "No expenses recorded yet.")
        history_box.configure(state="disabled")
        return

    history_box.configure(state="normal")
    history_box.delete("1.0", "end")
    # Show last 10 entries, most recent at top
    for line in reversed(lines[-10:]):
        history_box.insert("1.0", line)
    history_box.configure(state="disabled")

def is_valid_name(name):
    # Allow letters, numbers, spaces, hyphens, apostrophes, and periods
    pattern = r"^[\w\s\-\.'']+$"
    return bool(re.match(pattern, name))

def is_valid_amount(amount_str):
    # Matches the following amount formats:
    #  - .99
    #  - 0.99
    #  - 99
    #  - 99.9
    #  - 99.99
    pattern = r"^(\d+)?(\.\d{1,2})?$"
    return bool(re.match(pattern, amount_str))

def add_expense():
    if app_closing or not app.winfo_exists():
        return
    name = name_var.get()
    amount_str = amount_var.get()
    category = category_var.get()

    if not is_valid_name(name):
        status_label.configure(text="❌ Invalid name format", text_color="red")
        return

    if not is_valid_amount(amount_str):
        status_label.configure(text="❌ Invalid amount format", text_color="red")
        return

    try:
        amount = float(amount_str)
        expense = Finance(name=name, amount=amount, category=category)
        with open(expense_file_path, "a", encoding="utf-8") as f:
            f.write(f"{expense.name}, {expense.amount}, {expense.category}\n")
        status_label.configure(text="✅ Expense added successfully!", text_color="green")
        update_spending_history()
        name_var.set("")
        amount_var.set("")
        category_dropdown.set("Food")
        summarize_expenses()
    except ValueError:
        status_label.configure(text="❌ Invalid amount", text_color="red")

def remove_last_expense():
    if app_closing or not app.winfo_exists():
        return
    try:
        with open(expense_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            status_label.configure(text="❌ No expenses to remove.", text_color="red")
            return
        # Remove last line
        lines = lines[:-1]
        with open(expense_file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        status_label.configure(text="🗑️ Last expense removed.", text_color="orange")
        update_spending_history()
        summarize_expenses()
    except Exception as e:
        status_label.configure(text=f"❌ Error: {e}", text_color="red")

def summarize_expenses():
    if app_closing or not app.winfo_exists():
        return
    # Clear previous widgets in summary container
    for widget in summary_container.winfo_children():
        widget.destroy()

    try:
        with open(expense_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        status_label.configure(text="❌ No expenses found", text_color="red")
        return

    expenses = []
    for line in lines:
        if line.strip():
            parts = line.strip().split(",")
            if len(parts) == 3:
                name, amount_str, category = parts
                try:
                    amount = float(amount_str)
                    expenses.append(Finance(name=name, amount=amount, category=category))
                except ValueError:
                    continue

    total_spent = sum(x.amount for x in expenses)
    remaining_budget = budget - total_spent
    now = datetime.datetime.now()
    days_left = calendar.monthrange(now.year, now.month)[1] - now.day
    daily_budget = remaining_budget / days_left if days_left > 0 else 0

    # Create the summary text lines
    summary_lines = [
        f"Total Spent: ${total_spent:.2f}",
        f"Remaining Budget: ${remaining_budget:.2f}",
        f"Remaining Days: {days_left}",
        f"Daily Budget: ${daily_budget:.2f}",
        "",  # blank line
    ]

    categorized = {}
    for exp in expenses:
        categorized[exp.category] = categorized.get(exp.category, 0) + exp.amount
    for category, amt in categorized.items():
        summary_lines.append(f"{category}: ${amt:.2f}")

    # Top summary box
    # Clear existing widgets in the top summary container
    for widget in summary_container.grid_slaves(row=0, column=0):
        widget.destroy()

    # Create a frame inside summary_container for the top summary
    summary_top_frame = customtkinter.CTkFrame(summary_container)
    summary_top_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")

    # Configure grid inside the frame
    summary_top_frame.grid_columnconfigure(0, weight=1)

    # Create labels for each line with different colors
    labels_texts_colors = [
        (f"Total Spent: ${total_spent:.2f}", "#FFC0CB"),    # light pink
        (f"Remaining Budget: ${remaining_budget:.2f}", "#90EE90"),  # light green
        (f"Remaining Days: {days_left}", "#5DADE2"),    # light blue
        (f"Daily Budget: ${daily_budget:.2f}", "#FFCC99"),  # light orange
    ]

    for i, (text, color) in enumerate(labels_texts_colors):
        lbl = customtkinter.CTkLabel(summary_top_frame, text=text, text_color=color, anchor="w", font=("Arial", 14))
        lbl.grid(row=i, column=0, sticky="w", pady=10)

    # Bottom category box
    summary_bottom_text = customtkinter.CTkTextbox(summary_container, width=360, height=100)
    summary_bottom_text.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")

    category_summary = ""
    for category, amt in categorized.items():
        category_summary += f"{category}: ${amt:.2f}\n"
    summary_bottom_text.insert("1.0", category_summary)
    summary_bottom_text.configure(state="disabled")

    show_expense_bar_chart(categorized, summary_container)

def show_expense_bar_chart(data, parent_frame):
    if app_closing or not app.winfo_exists():
        return
    if not data:
        return

    categories = list(data.keys())
    amounts = list(data.values())

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = plt.get_cmap("tab20").colors

    bars = ax.barh(categories, amounts, color=colors[:len(categories)])
    ax.set_title("Expenses by Category", fontsize=14, weight='bold')
    ax.set_xlabel("Amount ($)", fontsize=14)

    for bar, amount in zip(bars, amounts):
        ax.text(bar.get_width() + max(amounts)*0.01, bar.get_y() + bar.get_height()/2,
                f"${amount:.2f}", va="center", fontsize=10, color="black")

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

def on_closing():
    global app_closing
    app_closing = True  # Signal that app is closing

    try:
        plt.close('all')
    except Exception:
        pass

    try:
        app.quit()
        app.destroy()
    except:
        pass

# --- Main App ---

budget = load_budget()

app = customtkinter.CTk()
app.geometry("1000x700")
app.title("💰 Financial Dashboard")

# Patch CustomTkinter callbacks right after creating the app:
patch_customtkinter_callbacks()

app.protocol("WM_DELETE_WINDOW", on_closing)

# Variables
name_var = tkinter.StringVar()
amount_var = tkinter.StringVar()
category_var = tkinter.StringVar()
budget_input_var = tkinter.StringVar()

# Grid configuration
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, minsize=375)
app.grid_columnconfigure(1, weight=1)     # Main content grows/fills

frame_sidebar = customtkinter.CTkFrame(app, width=400, corner_radius=0, fg_color="white")
frame_sidebar.grid(row=0, column=0, sticky="ns")
frame_sidebar.grid_rowconfigure(10, weight=1)

frame_main = customtkinter.CTkFrame(app)
frame_main.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)
frame_main.grid_rowconfigure(3, weight=1)
frame_main.grid_columnconfigure(0, weight=1)

# Sidebar Widgets
sidebar_title = customtkinter.CTkLabel(frame_sidebar, text="Edit...", font=("Arial", 20, "bold"), text_color="#1F6AA5")
sidebar_title.pack(pady=20, padx=(20, 10))

budget_label = customtkinter.CTkLabel(frame_sidebar, text=f"Monthly Budget: ${budget:.2f}", font=("Arial", 14, "bold"), text_color="black")
budget_label.pack(pady=(0, 5), padx=(10, 10))

budget_input = customtkinter.CTkEntry(frame_sidebar, placeholder_text="Set new budget", textvariable=budget_input_var)
budget_input.pack(pady=5, padx=(10, 10))

budget_button = customtkinter.CTkButton(frame_sidebar, text="💾 Save Budget", command=update_budget)
budget_button.pack(pady=5, padx=(10, 10))

customtkinter.CTkLabel(frame_sidebar, text="Add Expense:", font=("Arial", 14, "bold"), text_color="black").pack(pady=(30, 5))

name_entry = customtkinter.CTkEntry(frame_sidebar, placeholder_text="Name", textvariable=name_var)
name_entry.pack(pady=3, padx=(10, 10))

amount_entry = customtkinter.CTkEntry(frame_sidebar, placeholder_text="Amount", textvariable=amount_var)
amount_entry.pack(pady=3, padx=(10, 10))

category_dropdown = customtkinter.CTkComboBox(frame_sidebar, values=categories, variable=category_var)
category_dropdown.set("Food")
category_dropdown.pack(pady=3, padx=(10, 10))

add_button = customtkinter.CTkButton(frame_sidebar, text="➕ Add Expense", command=add_expense)
add_button.pack(pady=10, padx=(10, 10))

remove_button = customtkinter.CTkButton(
    frame_sidebar,
    text="🗑️ Remove Last Expense",
    command=remove_last_expense,
    fg_color="darkred",
    hover_color="red"
)

remove_button.pack(pady=5, padx=(10, 10))

exit_button = customtkinter.CTkButton(frame_sidebar, text="❌ Exit", command=on_closing)
exit_button.pack(side="bottom", pady=20, padx=(10, 10))

# Middle Widgets
status_label = customtkinter.CTkLabel(frame_main, text="", text_color="green")
status_label.grid(row=0, column=0, sticky="w", pady=(10, 10))

history_label = customtkinter.CTkLabel(frame_main, text="Spending History:", font=("Arial", 14, "bold"))
history_label.grid(row=1, column=0, sticky="w", padx=(10, 10))

history_box = customtkinter.CTkTextbox(frame_main, height=150)
history_box.grid(row=2, column=0, sticky="ew", padx=(10, 10), pady=(10, 10))

summary_container = customtkinter.CTkFrame(frame_main)
summary_container.grid(row=3, column=0, sticky="nsew", padx=10)
summary_container.grid_columnconfigure(0, weight=1)
summary_container.grid_columnconfigure(1, weight=1)
summary_container.grid_rowconfigure(0, weight=1)
summary_container.grid_rowconfigure(1, weight=1)

update_spending_history()
summarize_expenses()

app.mainloop()
