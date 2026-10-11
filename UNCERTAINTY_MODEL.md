# Uncertainty and sensitivity

The original distribution is retained unchanged: independent per-pipe loss p=.03, corridor event p=.08, supply U(.75,1), demand U(.9,1.35). Fresh diagnosis sensitivity uses seed 20261012, separate from the historical 200 scenarios. Availability records do not reveal the original event trigger; new experiments store scenario IDs and distribution parameters.

Failure probability estimates and 95% Wilson intervals are conditional on IID draws from this synthetic distribution. They are not field reliability estimates. Simultaneous inference, selected candidates and correlated candidate comparisons require care. Final held-out intervals use a recommendation frozen from training before held-out results exist.

`deva.analysis.sensitivity` implements a full outage × demand × supply factorial sweep and paired common-random-number interventions: demand +5%, supply −5%, each installed edge capacity −10%. Report failure-rate differences, asymptotic paired mean-difference standard errors/intervals, unmet demand and common service. These are finite changes, not differential derivatives or Sobol indices. Interactions are visible in the factorial records and diagnosed by controlled restoration. Small samples/discrete response can yield zero asymptotic standard error; it does not establish zero uncertainty. Wilson intervals remain attached to each intervention. Recovery is untested because the model has no time dimension.

No distribution has field calibration. Source/demand correlations are assumptions of the synthetic generator, not discovered real-world relationships. Averages, quantiles and confidence must keep their scenario family and sample count attached.
