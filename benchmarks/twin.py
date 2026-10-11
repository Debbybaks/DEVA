"""Repeatable wall-clock calibration, cascade and bounded-tool measurements."""
import json,platform,resource,time
from pathlib import Path
import numpy as np, scipy
from deva.digital_twin import benchmark_data
from deva.calibration import calibrate,sensor_placement
from deva.rupture import policies,cascade
from deva.engineering_agent import investigate
raw=json.loads(Path('examples/emergency_water_hydraulic.json').read_text());d=[.125]*6
data=benchmark_data(raw,d);measurements={}
functions={'calibration':lambda:calibrate(raw,d,data['parameters'],data['splits']['calibration'],data['splits']['validation'],starts=3),'sensor_placement':lambda:sensor_placement(raw,d,data['parameters'],data['ground_truth'],data['splits']['calibration'],budget=2),'cascade':lambda:cascade(raw,d,dict(closed=['east-trunk']),policies(raw)),'engineering_agent':lambda:investigate(raw,d,dict(component='hospital',maximum_failure_probability=.02,maximum_cost_increase=.12,training_samples=12,validation_samples=40,maximum_candidates=7,maximum_tool_calls=10,seed=20261050))}
for name,fn in functions.items():
    times=[]
    for _ in range(5):
        t=time.perf_counter();fn();times.append(time.perf_counter()-t)
    measurements[name]=dict(samples_seconds=times,mean_seconds=float(np.mean(times)),p95_seconds=float(np.quantile(times,.95)))
report=dict(environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),measurements=measurements,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,scope='Local six-node synthetic warm benchmark; five repeats, host-specific wall clock. Agent benchmark omits optional calibration tools. No Rust/WASM or surrogate justified by these workload sizes.')
Path('artifacts/twin-science-performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
