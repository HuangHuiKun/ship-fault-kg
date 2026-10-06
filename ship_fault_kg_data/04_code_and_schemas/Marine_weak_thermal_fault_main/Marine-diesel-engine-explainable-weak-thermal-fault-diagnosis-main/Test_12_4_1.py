import numpy as np


class CRIME:
    """
    CRIME (CRIME Optimization Algorithm) Implementation.

    A meta-heuristic optimization algorithm inspired by the physical phenomenon of rime formation.
    """

    def __init__(self, fitness_func, dim, pop_size=30, max_iter=100, lb=None, ub=None):
        """
        Initialize the CRIME optimizer.

        Args:
            fitness_func (callable): The objective function to minimize.
                                     Input: vector (dim,), Output: scalar fitness.
            dim (int): Dimension of the search space (number of parameters).
            pop_size (int): Size of the population (number of agents).
            max_iter (int): Maximum number of iterations.
            lb (float or array-like): Lower bound(s) of the search space.
            ub (float or array-like): Upper bound(s) of the search space.
        """
        self.fitness_func = fitness_func
        self.dim = dim
        self.pop_size = pop_size
        self.max_iter = max_iter

        # Handle boundaries: ensure they are numpy arrays
        self.lb = np.array(lb) if lb is not None else np.zeros(dim)
        self.ub = np.array(ub) if ub is not None else np.ones(dim)

        # --- 1. Initialization ---
        # Initialize population with random uniform distribution within bounds
        # X ~ U(lb, ub)
        self.population = self.lb + (self.ub - self.lb) * np.random.rand(pop_size, dim)

        # Evaluate initial fitness
        self.fitness = np.array([self.fitness_func(ind) for ind in self.population])

        # Record the global best solution found so far
        self.best_idx = np.argmin(self.fitness)
        self.best_pos = self.population[self.best_idx].copy()
        self.best_fit = self.fitness[self.best_idx]

    def optimize(self):
        """
        Execute the optimization loop.

        Returns:
            tuple: (best_position, best_fitness)
        """
        for iter in range(self.max_iter):
            # --- RIME Search Mechanism (Simplified Demonstration) ---
            # Note: The standard RIME includes 'Soft-rime' and 'Hard-rime' search strategies
            # based on a rime factor. The code below is a simplified exploration/exploitation logic.

            for i in range(self.pop_size):
                # 1. Generate a candidate position
                # Logic: Current Position + Random Perturbation + Trend towards Best
                noise = np.random.randn(self.dim) * 0.1
                trend = 0.5 * (self.best_pos - self.population[i])
                new_pos = self.population[i] + noise + trend

                # 2. Boundary Constraint Handling
                # Clip the values to ensure they stay within [lb, ub]
                new_pos = np.clip(new_pos, self.lb, self.ub)

                # 3. Evaluation
                new_fit = self.fitness_func(new_pos)

                # 4. Greedy Selection (Update Mechanism)
                # If the new position is better, update the individual
                if new_fit < self.fitness[i]:
                    self.population[i] = new_pos
                    self.fitness[i] = new_fit

                    # 5. Update Global Best
                    if new_fit < self.best_fit:
                        self.best_fit = new_fit
                        self.best_pos = new_pos.copy()

            # Log progress
            print(f"Iteration {iter + 1}/{self.max_iter}, Best Fitness: {self.best_fit:.4f}")

        return self.best_pos, self.best_fit


# --- Testing Example --- #
if __name__ == "__main__":
    # Define a simple benchmark function (Sphere Function)
    # Global minimum is 0 at [0, 0, ..., 0]
    def sphere(x):
        return np.sum(x ** 2)


    # Instantiate and run RIME
    print("--- Starting CRIME Optimization (Sphere Function) ---")
    rime = CRIME(fitness_func=sphere, dim=5, pop_size=20, max_iter=50, lb=-5, ub=5)
    best_pos, best_fit = rime.optimize()

    print("\n--- Optimization Result ---")
    print(f"Best Solution (Position): {best_pos}")
    print(f"Best Fitness (Value): {best_fit:.6f}")