import matplotlib.pyplot as plt
import numpy as np
import time

#the next function will calculate P(n) which is the number of primes less than or equal to n
def is_prime(num):
    """
    This function checks if a number is prime.
    
    Parameters:
    num (int): The number to check.
    
    Returns:
    bool: True if the number is prime, False otherwise.
    """
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def P(n):
    """
    This function calculates the number of prime numbers less than or equal to n.
    
    Parameters:
    n (int): The upper limit.
    
    Returns:
    int: The count of prime numbers less than or equal to n.
    """
    count = 0
    for i in range(2, n + 1):
        if is_prime(i):
            count += 1
    return count    

def plot_runtime():
    """
    This function plots the runtime of the P function for n from 1 to 1000.
    """
    n_values = range(1, 1001)
    p_times = []

    for n in n_values:      
        # Measure time for P(n)
        start_time = time.time()
        P(n)
        p_times.append(time.time() - start_time)

    # Plot the runtime
    plt.plot(n_values, p_times, label="Runtime of P(n)")
    plt.xlabel("n")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime of P(n) for n from 1 to 1000")
    plt.legend()
    plt.grid()
    plt.show()    

def plot_primes():
    """
    This function plots the number of primes P(n) for n from 1 to 1000.
    """
    n_values = range(1, 10001)
    p_values = [P(n) for n in n_values]  # Calculate P(n) for each n

    # Plot P(n)
    plt.plot(n_values, p_values, label="P(n) (Number of primes ≤ n)")
    plt.xlabel("n")
    plt.ylabel("P(n)")
    plt.title("Number of Primes P(n) for n from 1 to 1000")
    plt.legend()
    plt.grid()
    plt.show()

def main():
    """
    Main function to execute the plot_primes function.
    """
    plot_primes()

if __name__ == "__main__":
    main()
