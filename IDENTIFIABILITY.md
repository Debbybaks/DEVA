# Identifiability

Before fitting and at the fitted point, DEVA computes finite-difference sensitivity to each bounded parameter. Columns are scaled by parameter range and rows by measurement standard deviation. SVD rank uses max(10^-8, 10^-6 times the largest singular value); singular values, condition number and column cosines are retained.

Full rank means locally distinguishable numerical directions under the given excitation, noise and model. It does not establish structural identifiability, global uniqueness, adequate sensor precision or physical validity. Under-observed problems produce estimates with an explicit rank-deficiency warning and no finite parameter covariance. Tests demonstrate that one scalar measurement cannot identify three parameters.

Boundary sensitivities use one-sided differences. Interior differences use 10^-4 of the declared parameter range. Finite-difference sensitivity is approximate; differentiability at pressure-service regime boundaries is not guaranteed.
