"""Run five paired seeds concurrently, then combine raw trajectories."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
from pathlib import Path
import subprocess,sys,json,time
import numpy as np
import run_nn as nn
root=Path(__file__).resolve().parent
jobs=[]; start=time.time()
for i in range(5):
    out=root/'long_runs'/f'seed_{20261010+i}'
    out.mkdir(parents=True,exist_ok=True)
    log=(out/'run.log').open('w')
    command=[sys.executable,str(root/'run_nn.py'),'--runs','1','--steps','200000','--seed',str(20261010+i),'--out',str(out)]
    jobs.append((subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT),out,log))
print('Started five independent seeds, seven methods, 200000 updates.',flush=True)
for proc,out,log in jobs:
    code=proc.wait();log.close()
    if code: raise RuntimeError(f'{out} failed; inspect run.log')
    print(f'Completed {out.name}; elapsed {time.time()-start:.1f}s',flush=True)
arrays=[]; summaries=[]
for _,out,_ in jobs:
    with np.load(out/'trajectories.npz') as d: arrays.append({k:d[k].copy() for k in d.files})
    summaries.append(json.loads((out/'summary.json').read_text()))
a=arrays[0]
for key in ['mse','predictions']: a[key]=np.concatenate([x[key] for x in arrays],axis=0)
for other in arrays[1:]:
    if not np.array_equal(a['steps'],other['steps']): raise ValueError('Checkpoint mismatch')
s=summaries[0];s['config']['runs']=5;s['config']['seed']=20261010
s['elapsed_seconds']=time.time()-start
s['failures']=[x['failures'][0] for x in summaries]
s['final_mse_per_run']=[x['final_mse_per_run'][0] for x in summaries]
s['execution_note']='Five independent seeds run concurrently; no clean oracle training.'
out=root/'results';out.mkdir(exist_ok=True)
s['config']['out']=str(out)
np.savez_compressed(out/'trajectories.npz',**a)
(out/'summary.json').write_text(json.dumps(s,indent=2,allow_nan=False))
nn.plot(out,s)
print('Final mean MSE:',dict(zip(nn.METHODS,np.mean(a['mse'][:,:,-1],axis=0))),flush=True)
print('Failure records:',s['failures'],flush=True)
