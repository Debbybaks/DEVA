# DEVA visual specification

Calm scientific workstation: graphite background #12191D, warm paper text #E5E1D7, subdued grid #28343A, teal flow #66B8AC, amber uncertainty #D1AA62, vermilion failure #D37B6D. Colours encode meaning; geometry and labels repeat that meaning. Verification does not use a decorative glow.

Typography: readable sans serif for navigation, monospace for units, equations and experiment IDs. Minimum 14px labels, generous negative space, thin structural rules, no gradients as a substitute for hierarchy. Real spatial depth only where it expresses graph geometry or layered model relationships.

Edges encode installed capacity by width, flow by internal stroke, outage by broken line. Source limits and demand deficits appear attached to nodes. Uncertainty shows interval ribbons only when computed. Evolution is a branching graph with legible parentage and rejection causes. Mutations morph only when capacities actually change. Motion respects reduced-motion settings.

Future prototype acceptance: locate an overloaded edge in ≤10 seconds, correctly identify model limitations, navigate evidence without a pointer, and keep responsive selection during background solves. These are targets, not completed user-study findings. No UI is implemented in Phase 1.

## Phase-2 implementation status

The implemented environment uses restrained graphite/teal/amber styling, self-hosted Manrope/IBM Plex Mono, Three.js geometry and GLSL flux/uncertainty encoding. SVG ancestry retains rejected branches. Software-renderer limitations and quantitative legends are visible; all data is supplied by Python rather than decorative simulation.
