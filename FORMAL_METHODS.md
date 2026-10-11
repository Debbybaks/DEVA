# Bounded formal method selection

Z3 fits the finite Boolean connectivity requirement directly. An open/closed Boolean is assigned to each pipe. A pseudo-Boolean constraint bounds the outage count. Reachability is unrolled for |nodes|−1 rounds from the explicit active sources using undirected adjacency. The solver searches for an allowed assignment disconnecting any positive-demand node.

UNSAT means no such counterexample exists in this model; SAT provides the actual closed-pipe assignment. UNKNOWN remains unknown. A ten-second solver limit is explicit. The code uses proof-enabled Z3 contexts and stores SMT-LIB plus proof SHA-256 and text on UNSAT. Inputs include pipe endpoints, source and target node lists; evidence is replayable without application state. Dependency `z3-solver==4.16.0.0` is pinned in the `formal` and `test` extras; ordinary historical scientific commands do not require it.

This method was selected for a concrete bounded safety property, not to prove nonlinear physical reality. Floating-point Darcy solves, empirical reliability estimates and source operating constraints do not inherit a formal badge. Exhaustive enumeration tests independently check the graph encoding, and SMT-LIB replay tests check portability within the pinned solver.
