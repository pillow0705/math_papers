"""Paired MSE comparison for corrected SGD in nonlinear-feature regression."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from numpy.polynomial.hermite import hermgauss

NAMES = (
    "Clean oracle", "Naive", "Taylor (order 2)", "SIMEX (quadratic)",
    "Woolsey-Huang Eq. (5)", "Regression calibration", "CCSGD",
    "CCSGD (integrated V)", "Taylor (order 4)",
)
SLUGS = (
    "oracle", "naive", "taylor2", "simex", "woolsey_huang",
    "regression_calibration", "ccsgd", "ccsgd_integrated", "taylor4",
)
BASELINES = (1, 2, 8, 3, 4, 5)
CCSGD = 6


def features(q, frequency):
    """Holomorphic extension of (sin z, cos(f z), z^2)."""
    return np.stack((np.sin(q), np.cos(frequency*q), q*q), axis=-1)


def feature_derivatives(w, frequency):
    f = frequency
    zero = np.zeros_like(w)
    return (
        features(w, f),
        np.stack((np.cos(w), -f*np.sin(f*w), 2*w), axis=-1),
        np.stack((-np.sin(w), -f*f*np.cos(f*w), zero+2), axis=-1),
        np.stack((-np.cos(w), f**3*np.sin(f*w), zero), axis=-1),
        np.stack((np.sin(w), f**4*np.cos(f*w), zero), axis=-1),
    )


def score(theta, q, frequency, response):
    """Analytically extended score; q may be genuinely complex."""
    x = features(q, frequency)
    return (np.sum(theta*x, axis=-1) - response)[..., None]*x


def taylor_scores(theta2, theta4, w, variance, frequency, response):
    p0, p1, p2, p3, p4 = feature_derivatives(w, frequency)
    def terms(theta):
        a0 = np.sum(theta*p0, axis=-1) - response
        a1 = np.sum(theta*p1, axis=-1)
        a2 = np.sum(theta*p2, axis=-1)
        a3 = np.sum(theta*p3, axis=-1)
        a4 = np.sum(theta*p4, axis=-1)
        g0 = a0[..., None]*p0
        g2 = a2[..., None]*p0 + 2*a1[..., None]*p1 + a0[..., None]*p2
        g4 = (a4[..., None]*p0 + 4*a3[..., None]*p1
              + 6*a2[..., None]*p2 + 4*a1[..., None]*p3
              + a0[..., None]*p4)
        return g0, g2, g4
    g0, g2, _ = terms(theta2)
    k0, k2, k4 = terms(theta4)
    return g0 - variance*g2/2, k0 - variance*k2/2 + variance**2*k4/8


def gaussian_moments(w, variance, frequency):
    """E[psi(Q)psi(Q)^T], E[psi(Q)] for Q~N(w,variance).

    The same entire formulas at negative variance give E_V psi(w+iV) products.
    """
    s = variance
    f = frequency
    es = np.exp(-s/2)
    ec = np.exp(-f*f*s/2)
    sinw, cosfw = np.sin(w), np.cos(f*w)
    r = np.stack((es*sinw, ec*cosfw, w*w+s), axis=-1)
    A = np.empty(w.shape+(3, 3), dtype=float)
    A[..., 0, 0] = (1-np.exp(-2*s)*np.cos(2*w))/2
    A[..., 1, 1] = (1+np.exp(-2*f*f*s)*np.cos(2*f*w))/2
    A[..., 0, 1] = A[..., 1, 0] = (
        np.exp(-(1+f)**2*s/2)*np.sin((1+f)*w)
        + np.exp(-(1-f)**2*s/2)*np.sin((1-f)*w)
    )/2
    A[..., 0, 2] = A[..., 2, 0] = es*((w*w+s-s*s)*sinw+2*w*s*np.cos(w))
    A[..., 1, 2] = A[..., 2, 1] = ec*(
        (w*w+s-f*f*s*s)*cosfw-2*w*f*s*np.sin(f*w)
    )
    A[..., 2, 2] = w**4+6*w*w*s+3*s*s
    return A, r


def moment_score(theta, w, variance, frequency, response):
    A, r = gaussian_moments(w, variance, frequency)
    return np.einsum("...ij,...j->...i", A, theta)-response*r


def posterior_mean(w, args):
    var = args.jitter**2+args.sigma**2
    low, high = args.low_mean, args.high_mean
    a = np.log(args.mix_prob)-(w-low)**2/(2*var)
    b = np.log1p(-args.mix_prob)-(w-high)**2/(2*var)
    prob = 1/(1+np.exp(np.clip(b-a, -700, 700)))
    gain = args.jitter**2/var
    return prob*(low+gain*(w-low))+(1-prob)*(high+gain*(w-high))


def taylor_maps(w, variance, frequency, order):
    d = feature_derivatives(w, frequency)
    outer = lambda a, b: np.einsum("...i,...j->...ij", a, b)
    A, r = outer(d[0], d[0]), d[0]
    if order >= 2:
        A = A-variance/2*(outer(d[2], d[0])+2*outer(d[1], d[1])+outer(d[0], d[2]))
        r = r-variance/2*d[2]
    if order >= 4:
        A = A+variance**2/8*(
            outer(d[4], d[0])+4*outer(d[3], d[1])+6*outer(d[2], d[2])
            +4*outer(d[1], d[3])+outer(d[0], d[4])
        )
        r = r+variance**2/8*d[4]
    return A, r


def map_at_w(w, method, args):
    f, v = args.frequency, args.sigma**2
    if method == 1:
        x = features(w, f)
        return np.einsum("...i,...j->...ij", x, x), x
    if method in (2, 8):
        return taylor_maps(w, v, f, 2 if method == 2 else 4)
    if method == 4:
        x = features(w+1j*args.sigma, f)
        return np.real(np.einsum("...i,...j->...ij", x, x)), np.real(x)
    if method == 5:
        x = features(posterior_mean(w, args), f)
        return np.einsum("...i,...j->...ij", x, x), x
    if method == 7:
        return gaussian_moments(w, -v, f)
    raise ValueError(method)


def mixture_expectation(fn, args, noisy=False):
    nodes, weights = hermgauss(160)
    weights = weights/np.sqrt(np.pi)
    scale = np.sqrt(args.jitter**2+(args.sigma**2 if noisy else 0))
    result = None
    for prob, mean in ((args.mix_prob, args.low_mean),
                       (1-args.mix_prob, args.high_mean)):
        q = mean+np.sqrt(2)*scale*nodes
        values = fn(q)
        if result is None:
            result = [np.zeros_like(value[0]) for value in values]
        for out, value in zip(result, values):
            out += prob*np.tensordot(weights, value, axes=(0, 0))
    return result


def response_rhs(args, feature_map):
    # Joint expectation is essential: Y depends on Z and is correlated with W.
    nodes, weights = hermgauss(128)
    weights = weights/np.sqrt(np.pi)
    u = np.sqrt(2)*args.sigma*nodes[None, :]
    rhs = np.zeros(3)
    for prob, mean in ((args.mix_prob, args.low_mean),
                       (1-args.mix_prob, args.high_mean)):
        z = mean+np.sqrt(2)*args.jitter*nodes[:, None]
        y = features(z, args.frequency) @ np.asarray(args.theta_true)
        w = z+u
        rhs += prob*np.einsum("i,j,ij,ijk->k", weights, weights,
                              np.broadcast_to(y, w.shape), feature_map(w))
    return rhs


def population_targets(args):
    f = args.frequency
    H, r = mixture_expectation(
        lambda z: (np.einsum("...i,...j->...ij", features(z, f), features(z, f)),
                   features(z, f)), args,
    )
    star = np.asarray(args.theta_true, dtype=float)
    targets = np.empty((len(NAMES), 3))
    targets[[0, CCSGD, 7]] = star
    eigenvalues = np.empty((len(NAMES), 3))
    eigenvalues[[0, CCSGD, 7]] = np.linalg.eigvalsh(H)
    simex_level_eigenvalues = []
    for j in BASELINES:
        if j == 3:
            level_targets = []
            for added_variance in (0, args.sigma**2, 2*args.sigma**2):
                A, b = mixture_expectation(
                    lambda w: gaussian_moments(w, added_variance, f), args, noisy=True,
                )
                level_eigenvalues = np.linalg.eigvalsh(A)
                if level_eigenvalues[0] <= 0:
                    raise ValueError("SIMEX population update is not stable")
                simex_level_eigenvalues.append(level_eigenvalues)
                rhs = response_rhs(args, lambda w: gaussian_moments(w, added_variance, f)[1])
                level_targets.append(np.linalg.solve(A, rhs))
            targets[j] = 3*level_targets[0]-3*level_targets[1]+level_targets[2]
            eigenvalues[j] = simex_level_eigenvalues[0]
            continue
        A, b = mixture_expectation(lambda w: map_at_w(w, j, args), args, noisy=True)
        eigenvalues[j] = np.linalg.eigvalsh(A)
        if eigenvalues[j, 0] <= 0:
            raise ValueError(f"Population update for {NAMES[j]} is not stable")
        rhs = response_rhs(args, lambda w: map_at_w(w, j, args)[1])
        targets[j] = np.linalg.solve(A, rhs)
    floors = np.sum((targets-star)**2, axis=1)
    return star, targets, floors, eigenvalues, np.asarray(simex_level_eigenvalues)


def study(args):
    star, targets, floors, eigenvalues, simex_level_eigenvalues = population_targets(args)
    checks = np.unique(np.r_[
        np.arange(0, min(args.iterations, 1000)+1, 10),
        np.geomspace(1, args.iterations, 300).round().astype(int),
        np.linspace(1, args.iterations, 501).round().astype(int),
    ])
    source = Path(__file__).with_name("simulate.cpp")
    with tempfile.TemporaryDirectory(prefix="ccsgd-simulation-") as folder:
        folder = Path(folder)
        binary, checkpoint_file, output_file = (folder/name for name in
                                                 ("simulate", "checkpoints.txt", "trajectory.csv"))
        checkpoint_file.write_text("\n".join(map(str, checks))+"\n")
        subprocess.run([os.environ.get("CXX", "c++"), "-std=c++17", "-O3",
                        str(source), "-o", str(binary)], check=True)
        command = [binary, args.runs, args.iterations, args.seed, args.mix_prob,
                   args.low_mean, args.high_mean, args.jitter, args.sigma,
                   args.frequency, args.step_numerator,
                   args.step_shift, *star, checkpoint_file]
        with output_file.open("w") as output:
            subprocess.run(list(map(str, command)), stdout=output, check=True)
        trajectory = np.loadtxt(output_file, delimiter=",")
    if not np.array_equal(trajectory[:, 0].astype(int), checks):
        raise RuntimeError("Simulator returned unexpected checkpoints")
    mse = trajectory[:, 1:].T
    if not np.isfinite(mse).all():
        raise RuntimeError("Non-finite MSE: reduce the initial step size")
    return dict(checkpoints=checks, mse=mse, asymptotic_floors=floors,
                theta_star=star, method_targets=targets, population_eigenvalues=eigenvalues,
                simex_level_eigenvalues=simex_level_eigenvalues)


def plot_single(out, t, mse, floors, j, T):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.semilogy(t, mse[j], color="#bd573f", lw=2.3, label=NAMES[j])
    ax.semilogy(t, mse[CCSGD], color="#152f39", lw=2.5, label="CCSGD")
    ax.axhline(floors[j], color="#202020", ls="--", lw=1.8,
               label=rf"Asymptotic floor: {floors[j]:.3g}")
    ax.set(xlim=(0, T), xlabel="Iteration $t$", ylabel=r"$\mathbb{E}\|\theta_t-\theta^\star\|^2$")
    ax.grid(True, which="both", alpha=.18)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    name = f"mse_vs_{SLUGS[j]}"
    fig.savefig(out/f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(out/f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_overview(out, t, mse, floors, T, args):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ("#d55e00", "#0072b2", "#cc79a7", "#009e73", "#e69f00", "#7b61a8")
    for j, color in zip(BASELINES, colors):
        ax.axhline(floors[j], color=color, ls="--", lw=1.25, alpha=.82, zorder=1)
        ax.plot(t, mse[j], color=color, lw=2, zorder=3,
                label=rf"{NAMES[j]} (floor {floors[j]:.2g})")
    ax.plot(t, mse[CCSGD], color="#152f39", lw=2.8, zorder=4, label="CCSGD (floor 0)")
    late = (t >= 50000) & (t <= T)
    if late.sum() >= 3:
        slope, intercept = np.polyfit(np.log(t[late]), np.log(mse[CCSGD, late]), 1)
        ax.plot(t[late], .6*np.exp(intercept+slope*np.log(t[late])),
                color="#152f39", ls=":", lw=2.2, zorder=2,
                label=rf"CCSGD log-log slope: {slope:.2f}")
    ax.set_xscale("symlog", linthresh=100)
    ax.set_yscale("log")
    ax.set_xlim(0, T)
    ax.set_xticks(tuple(x for x in (0, 100, 1000, 10000, 100000, 1000000, T) if x <= T))
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda x, _: "0" if x == 0 else (
            f"{x/1e6:g}M" if x >= 1e6 else (f"{x/1000:g}k" if x >= 1000 else f"{x:g}")
        )
    ))
    ax.set_title(
        rf"$\ell(\theta;z,y)=\frac{{1}}{{2}}[\theta_1\sin z+\theta_2\cos({args.frequency:g}z)"
        r"+\theta_3 z^2-y]^2$" "\n"
        rf"$y={args.theta_true[0]:g}\sin Z{args.theta_true[1]:+g}\cos({args.frequency:g}Z){args.theta_true[2]:+g}Z^2$",
        fontsize=11, pad=12,
    )
    ax.set_xlabel("Iteration $t$ (early iterations expanded)")
    ax.set_ylabel(r"$\mathbb{E}\|\theta_t-\theta^\star\|^2$")
    ax.grid(True, which="both", alpha=.16)
    ax.text(1.02, .98,
            "Training: SGD\n"
            r"$\theta_t=\theta_{t-1}-\eta_t G_t$" "\n"
            rf"$\eta_t={args.step_numerator:g}/(t+{args.step_shift:g})$" "\n"
            rf"$\theta_0=0$; {args.runs} paired runs",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor=".8"))
    ax.legend(loc="center left", bbox_to_anchor=(1.01, .5), fontsize=9,
              title="Solid: MSE; dashed: asymptotic floor")
    fig.tight_layout()
    fig.savefig(out/"mse_overview.png", dpi=240, bbox_inches="tight")
    fig.savefig(out/"mse_overview.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent/"results")
    parser.add_argument("--runs", type=int, default=256)
    parser.add_argument("--iterations", type=int, default=10000000)
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--mix-prob", type=float, default=.8)
    parser.add_argument("--low-mean", type=float, default=-.5)
    parser.add_argument("--high-mean", type=float, default=2.)
    parser.add_argument("--jitter", type=float, default=.8)
    parser.add_argument("--sigma", type=float, default=1.2)
    parser.add_argument("--frequency", type=float, default=.7)
    parser.add_argument("--theta-true", type=float, nargs=3, default=(0.8, -0.6, 0.2))
    parser.add_argument("--step-numerator", type=float, default=2.6)
    parser.add_argument("--step-shift", type=float, default=3000.)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    result = study(args)
    np.savez_compressed(args.out/"mse_data.npz", **result)
    for j in BASELINES:
        plot_single(args.out, result["checkpoints"], result["mse"],
                    result["asymptotic_floors"], j, args.iterations)
    plot_overview(args.out, result["checkpoints"], result["mse"],
                  result["asymptotic_floors"], args.iterations, args)
    summary = dict(config=vars(args) | {"out": str(args.out)}, methods=NAMES,
                   theta_star=result["theta_star"].tolist(),
                   final_mse=result["mse"][:, -1].tolist(),
                   asymptotic_floors=result["asymptotic_floors"].tolist(),
                   population_eigenvalues=result["population_eigenvalues"].tolist(),
                   simex_level_eigenvalues=result["simex_level_eigenvalues"].tolist())
    (args.out/"summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"methods": NAMES, "final_mse": summary["final_mse"],
                      "floors": summary["asymptotic_floors"]}, indent=2))


if __name__ == "__main__":
    main()
