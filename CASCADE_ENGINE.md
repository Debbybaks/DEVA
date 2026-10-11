# Emergent research cascades

The existing protective-valve cascade remains intact. A separate `deva.rupture.cascade` model computes hydraulic redistribution after an initiating outage, evaluates state-dependent hazard, records draws and failures, closes failed pipes and resolves the next hydraulic state. The pipe order, seed, policies, timestep and initiating condition are recorded.

Every frame stores scenario, actual solved state, hazards, event references and simulation time. Every failure stores pre-event endpoint pressure/velocity, coefficients, probability, draw and resulting state. Causal graph edges point to stored frames and hazards. Counterfactual hazard changes compare with a separately solved no-initial-outage state under the same operating inputs. This is conditional model evidence, not a uniquely identified real-world causal effect. Simultaneous failures have jointly computed consequences.

Hazards are held constant within each interval and sampled at its end. Δt is a modelling resolution; animation does not invent intermediate physical states. Step-size dependence is an explicit limitation. Conservation/energy audits run for all frames. Fixed seeds replay exactly; independent SeedSequence streams support ensemble percentiles and retained trajectories.

Optional scheduled repairs reopen declared components at specified interval ends. These are explicit exogenous maintenance actions, not spontaneous healing. Passive hydraulic redistribution and active maintenance are labelled separately. Resource-constrained repair planning and physically modelled rupture/leak propagation remain incomplete.
