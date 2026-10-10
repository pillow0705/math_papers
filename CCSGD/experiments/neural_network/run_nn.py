"""Single-hidden-layer sine MLP; analytic complex backpropagation, real parameters."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
import argparse
import json
from pathlib import Path
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
METHODS = ['Naive SGD', 'CCSGD', 'Taylor order 2', 'Taylor order 4', 'SIMEX quadratic', 'Woolsey-Huang Eq. (5)', 'Regression calibration']

def teacher(z):
    return np.exp(-z*z)*np.sin(3*z) + .3*z*z

def initialize(rng):
    sizes = [1,32,1]
    params = []
    for layer, (a,b) in enumerate(zip(sizes[:-1],sizes[1:])):
        w = rng.normal(0, 1/np.sqrt(a), (a,b))
        bias = rng.uniform(-.5,.5,(b,)) if layer<1 else np.zeros(b)
        params.extend([w,bias])
    return params

def forward(p, x):
    a=x
    for k in range((len(p)//2)-1):
        a=np.sin(a@p[2*k]+p[2*k+1])
    return a@p[-2]+p[-1]

def score(p, x, y):
    # Holomorphic loss is (h-y)**2/2, never abs(h-y)**2/2.
    # Thus analytic chain rule uses transpose, never conjugate transpose.
    activations=[x]
    pre=[]
    a=x
    for k in range((len(p)//2)-1):
        s=a@p[2*k]+p[2*k+1]
        pre.append(s)
        a=np.sin(s)
        activations.append(a)
    residual=a@p[-2]+p[-1]-y
    delta=residual/len(x)
    g=[None]*len(p)
    g[-2]=(a.T@delta).real
    g[-1]=delta.sum(axis=0).real
    delta=delta@p[-2].T
    for k in range(len(pre)-1,-1,-1):
        delta=delta*np.cos(pre[k])
        g[2*k]=(activations[k].T@delta).real
        g[2*k+1]=delta.sum(axis=0).real
        if k:
            delta=delta@p[2*k].T
    return g

def taylor_score(p, x, y, sigma, order):
    # Taylor coefficients in a real input increment, holding response fixed.
    # Each coefficient is derivative/k!, so inverse heat weights are
    # [1, -sigma**2, 3*sigma**4] at degrees [0,2,4].
    import math
    b,d,a,c=p
    phase=x@b+d
    sn=np.sin(phase); cs=np.cos(phase)
    sc=[]; cc=[]
    for k in range(order+1):
        sc.append([sn,cs,-sn,-cs][k%4]*b**k/math.factorial(k))
        cc.append([cs,-sn,-cs,sn][k%4]*b**k/math.factorial(k))
    r=[v@a for v in sc]; r[0]=r[0]+c-y
    weights={0:1.,2:-sigma*sigma,4:3*sigma**4}
    ga=np.zeros_like(a); gd=np.zeros_like(d); gb=np.zeros_like(b); gc=np.zeros_like(c)
    for n in range(0,order+1,2):
        rs=sum(r[k]*sc[n-k] for k in range(n+1))
        rc=sum(r[k]*cc[n-k] for k in range(n+1))*a.T
        prev=sum(r[k]*cc[n-1-k] for k in range(n))*a.T if n else 0.
        ga+=weights[n]*rs.mean(axis=0)[:,None]
        gd+=weights[n]*rc.mean(axis=0)
        gb+=weights[n]*(rc*x+prev).mean(axis=0)[None,:]
        gc+=weights[n]*r[n].mean(axis=0)
    return [gb,gd,ga,gc]


def calibration_mean(w, sigma):
    from scipy.special import ndtr
    a=(-2-w)/sigma; b=(2-w)/sigma
    # Use survival-function differences in the positive tail.
    mass=np.where(a>0,ndtr(-a)-ndtr(-b),ndtr(b)-ndtr(a))
    shift=(np.exp(-a*a/2)-np.exp(-b*b/2))/np.sqrt(2*np.pi)
    return w+sigma*shift/mass


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--steps',type=int,default=200000)
    ap.add_argument('--runs',type=int,default=5)
    ap.add_argument('--sigma',type=float,default=.3)
    ap.add_argument('--batch',type=int,default=128)
    ap.add_argument('--train',type=int,default=8192)
    ap.add_argument('--prediction',type=int,default=4096)
    ap.add_argument('--eta',type=float,default=.01)
    ap.add_argument('--seed',type=int,default=20261010)
    ap.add_argument('--out',type=Path,default=ROOT/'results')
    args=ap.parse_args()
    out=args.out
    out.mkdir(exist_ok=True)
    checkpoints=np.unique(np.r_[0,np.geomspace(1,args.steps,180).astype(int),args.steps])
    mse=np.full((args.runs,len(METHODS),len(checkpoints)),np.nan)
    status=[]
    prediction_grid=np.linspace(-2,2,801)[:,None]
    final_predictions=np.full((args.runs,len(METHODS),len(prediction_grid)),np.nan)
    start=time.time()
    np.seterr(over='ignore',invalid='ignore',divide='ignore')
    for run in range(args.runs):
        rng=np.random.default_rng(args.seed+run)
        sim_rng=np.random.default_rng(args.seed+100000+run)
        obs_rng=np.random.default_rng(args.seed+200000+run)
        z=rng.uniform(-2,2,(args.train,1)); y=teacher(z)
        rng.normal(0,args.sigma,z.shape) # Preserve the previous initialization and prediction-set RNG stream; this draw is discarded.
        zp=rng.uniform(-2,2,(args.prediction,1)); yp=teacher(zp)
        initial=initialize(rng)
        models=[[v.copy() for v in initial] for _ in METHODS]
        sim_aux=[[v.copy() for v in initial] for _ in range(2)]
        def predict(k,x):
            if k==4:
                return 3*forward(models[k],x)-3*forward(sim_aux[0],x)+forward(sim_aux[1],x)
            return forward(models[k],x)
        live=np.ones(len(METHODS),dtype=bool)
        failures=[None]*len(METHODS)
        for k,p in enumerate(models):
            mse[run,k,0]=np.mean((forward(p,zp)-yp)**2)
        ci=1
        for t in range(1,args.steps+1):
            ix=rng.integers(args.train,size=args.batch)
            w_batch=z[ix]+obs_rng.normal(0,args.sigma,(args.batch,1))
            calibrated_batch=calibration_mean(w_batch,args.sigma)
            v=rng.normal(0,args.sigma,(args.batch,1))
            inputs=[w_batch,w_batch+1j*v,w_batch,w_batch,w_batch,w_batch+1j*args.sigma,calibrated_batch]
            sim_noise=sim_rng.normal(0,args.sigma,(2,args.batch,1))
            eta=args.eta/(1+t/2000)**.6
            for k,p in enumerate(models):
                if not live[k]: continue
                if k in (2,3):
                    g=taylor_score(p,inputs[k],y[ix],args.sigma,2 if k==2 else 4)
                else:
                    g=score(p,inputs[k],y[ix])
                if k==4:
                    aux_grad=[score(q,w_batch+np.sqrt(level)*sim_noise[level-1],y[ix]) for level,q in enumerate(sim_aux,1)]
                    if not all(np.all(np.isfinite(a)) for grad in aux_grad for a in grad):
                        live[k]=False; failures[k]={'step':t,'reason':'nonfinite SIMEX gradient'}
                        continue
                    for q,grad in zip(sim_aux,aux_grad):
                        for a,da in zip(q,grad): a-=eta*da
                if not all(np.all(np.isfinite(q)) for q in g):
                    live[k]=False; failures[k]={'step':t,'reason':'nonfinite complex gradient'}
                    continue
                for q,dq in zip(p,g): q-=eta*dq
                if not all(np.all(np.isfinite(q)) for q in p):
                    live[k]=False; failures[k]={'step':t,'reason':'nonfinite parameter'}
            if ci<len(checkpoints) and t==checkpoints[ci]:
                for k,p in enumerate(models):
                    if live[k]:
                        val=np.mean((predict(k,zp)-yp)**2)
                        if np.isfinite(val): mse[run,k,ci]=val
                        else:
                            live[k]=False; failures[k]={'step':t,'reason':'nonfinite prediction MSE'}
                ci+=1
            if t%5000==0:
                print(f'run {run+1}/{args.runs}, step {t}/{args.steps}, seconds {time.time()-start:.1f}',flush=True)
        for k,p in enumerate(models):
            if live[k]: final_predictions[run,k]=predict(k,prediction_grid)[:,0]
        status.append(dict(zip(METHODS,failures)))
        np.savez_compressed(out/'trajectories.npz',steps=checkpoints,mse=mse,grid=prediction_grid[:,0],truth=teacher(prediction_grid)[:,0],predictions=final_predictions,methods=METHODS)
        print('final MSE',dict(zip(METHODS,mse[run,:,-1].tolist())),flush=True)
    summary={'config':vars(args) | {'out':str(args.out)},'architecture':[1,32,1],
             'learning_rate':'eta0 / (1+t/2000)^0.6','response':'exp(-z^2) sin(3z) + 0.3 z^2',
             'failures':status,'final_mse_per_run':[[float(x) if np.isfinite(x) else None for x in row] for row in mse[:,:,-1]],
             'elapsed_seconds':time.time()-start,
             'methods':METHODS,
             'simex_note':'Independent SGD at lambda=0,1,2; prediction extrapolation 3h0-3h1+h2. Added Gaussian noises sampled per minibatch.',
             'rc_note':'Exact conditional mean under uniform[-2,2] latent input and known Gaussian noise.',
             'theory_note':'For each fixed finite real parameter vector, a single-hidden-layer sine score has exponential growth (up to polynomial factors) in the input and finite Gaussian moments. Uniform bounds along training require additional control on parameters; no global nonconvex convergence guarantee is asserted.',
             'data_note':'Fresh Gaussian measurement noise at every minibatch presentation, shared by all observed methods; independent correction noise; independent clean prediction inputs; prediction set never used for tuning. No clipping, projection, rejected updates, or V truncation.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    plot(out,summary)

def plot(out, summary):
    data=np.load(out/'trajectories.npz')
    cfg=summary['config']
    plot_end=min(110000,cfg['steps'])
    mask=data['steps']<=plot_end
    t=data['steps'][mask]; mse=data['mse'][:,:,mask]
    colors=['#e68613','black','#4daf4a','#e41a1c','#a65628','#984ea3','#17becf']
    fig,ax=plt.subplots(figsize=(10.8,5.4))
    for k,name in enumerate(METHODS):
        values=mse[:,k,:]
        # Require all runs at each checkpoint; never hide failed runs in an average.
        valid=np.all(np.isfinite(values),axis=0)
        mean=np.full(len(t),np.nan); low=mean.copy(); high=mean.copy()
        mean[valid]=values[:,valid].mean(axis=0)
        low[valid]=np.quantile(values[:,valid],.2,axis=0)
        high[valid]=np.quantile(values[:,valid],.8,axis=0)
        failures=sum(row[name] is not None for row in summary['failures'])
        label=name+(f' ({failures}/{cfg["runs"]} failed)' if failures else '')
        ax.plot(t,mean,color=colors[k],lw=2,label=label)
        if name=='CCSGD': ax.fill_between(t,low,high,color=colors[k],alpha=.12)
        if not np.all(valid):
            last=np.flatnonzero(valid)[-1]
            ax.plot(t[last],mean[last],'x',color=colors[k],ms=9)
    ax.set_xscale('symlog',linthresh=100)
    ax.set_yscale('log'); ax.set_xlim(0,plot_end)
    ax.set_xlabel('SGD updates'); ax.set_ylabel('Clean prediction MSE')
    ax.set_title(r'$f_0(z)=e^{-z^2}\sin(3z)+0.3z^2$'+'\nSine MLP: 1 → 32 → 1')
    ax.grid(True,which='both',alpha=.18)
    ax.legend(loc='upper right')
    ax.text(.02,.03,rf'SGD: $\eta_t={cfg["eta"]}/(1+t/2000)^{{0.6}}$'+'\n'+f'Batch {cfg["batch"]}; noise σ={cfg["sigma"]}; {cfg["runs"]} paired runs\nCCSGD band: 20–80% empirical quantiles',transform=ax.transAxes,fontsize=9,va='bottom',bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
    fig.tight_layout()
    for ext in ['png','pdf']: fig.savefig(out/f'prediction_mse.{ext}',dpi=200)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.5))
    ax.plot(data['grid'],data['truth'],color='red',ls='--',lw=2,label='True function')
    for k,name in enumerate(METHODS):
        p=data['predictions'][:,k,:]
        if np.all(np.isfinite(p)):
            ax.plot(data['grid'],p.mean(axis=0),color=colors[k],label=name,lw=1.7)
    ax.set_xlabel('Clean input z'); ax.set_ylabel('Prediction')
    ax.set_title('Final predictions, averaged across runs'); ax.legend(); ax.grid(alpha=.2)
    fig.tight_layout()
    for ext in ['png','pdf']: fig.savefig(out/f'prediction_fit.{ext}',dpi=200)
    plt.close(fig)

if __name__=='__main__': main()
