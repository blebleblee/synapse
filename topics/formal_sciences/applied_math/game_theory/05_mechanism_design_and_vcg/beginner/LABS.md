# Beginner Hands-On Lab: Game Theory 05 Mechanism Design And VCG
## Objective & Prerequisites
### Objective
The objective of this lab is to introduce you to the basics of Mechanism Design and the VCG (Vickrey-Clarke-Groves) mechanism. You will set up a basic environment, run your first experiment, and inspect the results to understand how these concepts are implemented in practice.

### Prerequisites
- Basic understanding of Game Theory.
- Familiarity with Python programming.
- Installation of Python 3.x on your system.
- Familiarity with command-line interface (CLI).

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
1. **Install Python and pip** (if not already installed):
   - For Windows, download the installer from the [official Python website](https://www.python.org/downloads/).
   - For macOS and Linux, you can use the package manager:
     ```bash
     sudo apt-get install python3 python3-pip  # For Ubuntu/Debian
     brew install python  # For macOS
     ```

2. **Install necessary Python packages**:
   Open your terminal or command prompt and run:
   ```bash
   pip install numpy matplotlib
   ```

3. **Verify the installation**:
   Run the following commands to verify that Python and the installed packages are correctly set up:
   ```bash
   python --version
   pip show numpy
   pip show matplotlib
   ```

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
1. **Create a new Python script**:
   Open your favorite text editor or IDE and create a new file named `vcg_mechanism.py`.

2. **Write a simple VCG mechanism implementation**:
   Copy and paste the following code into your `vcg_mechanism.py` file:
   ```python
   import numpy as np

   def vcg_mechanism(bids):
       """
       Implements the VCG mechanism for a single-item auction.
       :param bids: A dictionary where keys are agent names and values are their bids.
       :return: A dictionary with the allocation and payments for each agent.
       """
       # Sort bids in descending order
       sorted_bids = sorted(bids.items(), key=lambda x: x[1], reverse=True)
       winner = sorted_bids[0][0]
       winning_bid = sorted_bids[0][1]
       second_highest_bid = sorted_bids[1][1] if len(sorted_bids) > 1 else 0

       # Calculate payments
       payments = {agent: 0 for agent in bids}
       payments[winner] = second_highest_bid

       return {winner: winning_bid}, payments

   # Example usage
   bids = {'Alice': 10, 'Bob': 15, 'Charlie': 12}
   allocation, payments = vcg_mechanism(bids)
   print("Allocation:", allocation)
   print("Payments:", payments)
   ```

3. **Run the script**:
   Save the file and run it using the following command in your terminal or command prompt:
   ```bash
   python vcg_mechanism.py
   ```

4. **Expected output**:
   ```
   Allocation: {'Bob': 15}
   Payments: {'Alice': 0, 'Bob': 12, 'Charlie': 0}
   ```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
1. **Inspect the output**:
   The output shows that Bob wins the auction with a bid of 15. He pays the second-highest bid, which is 12. Alice and Charlie do not win and pay nothing.

2. **Modify the bids**:
   Change the bids in the `bids` dictionary to see how the allocation and payments change. For example, try:
   ```python
   bids = {'Alice': 20, 'Bob': 15, 'Charlie': 12}
   ```

3. **Run the modified script**:
   Save the changes and run the script again to see the new results.

## Challenge Exercise (Simple self-test for beginners)
1. **Add a fourth agent**:
   Add a fourth agent, 'David', with a bid of 18. Modify the `bids` dictionary accordingly.

2. **Run the script**:
   Execute the script and observe the new allocation and payments.

3. **Verify the results**:
   Ensure that the allocation and payments are calculated correctly according to the VCG mechanism rules. The expected output should be:
   ```
   Allocation: {'Alice': 20}
   Payments: {'Alice': 18, 'Bob': 0, 'Charlie': 0, 'David': 0}
   ```

This concludes the beginner hands-on lab for Game Theory 05 Mechanism Design And VCG. You have successfully set up your environment, run your first experiment, and inspected the results.
