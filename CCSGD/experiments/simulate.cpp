// Fast paired-stream simulation. CCSGD evaluates the full score at W+iV.
#include <array>
#include <cmath>
#include <complex>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Vec = std::array<double, 3>;
using CVec = std::array<std::complex<double>, 3>;
constexpr int METHODS = 9;

double dot(const Vec& a, const Vec& b) {
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
}

Vec feature(double q, double f) {
    return {std::sin(q), std::cos(f*q), q*q};
}

CVec feature(std::complex<double> q, double f) {
    return {std::sin(q), std::cos(f*q), q*q};
}

Vec score(const Vec& theta, double q, double f, double y) {
    Vec p = feature(q, f);
    double a = dot(theta, p)-y;
    return {a*p[0], a*p[1], a*p[2]};
}

Vec complex_score(const Vec& theta, std::complex<double> q, double f, double y) {
    CVec p = feature(q, f);
    std::complex<double> a = theta[0]*p[0]+theta[1]*p[1]+theta[2]*p[2]-y;
    return {std::real(a*p[0]), std::real(a*p[1]), std::real(a*p[2])};
}

Vec moment_score(const Vec& theta, double w, double s, double f, double y) {
    double sw=std::sin(w), cw=std::cos(w);
    double sf=std::sin(f*w), cf=std::cos(f*w);
    double es=std::exp(-s/2), ec=std::exp(-f*f*s/2);
    double r0=es*sw, r1=ec*cf, r2=w*w+s;
    double a00=(1-std::exp(-2*s)*std::cos(2*w))/2;
    double a11=(1+std::exp(-2*f*f*s)*std::cos(2*f*w))/2;
    double a01=(std::exp(-(1+f)*(1+f)*s/2)*std::sin((1+f)*w)
               +std::exp(-(1-f)*(1-f)*s/2)*std::sin((1-f)*w))/2;
    double a02=es*((w*w+s-s*s)*sw+2*w*s*cw);
    double a12=ec*((w*w+s-f*f*s*s)*cf-2*w*f*s*sf);
    double a22=w*w*w*w+6*w*w*s+3*s*s;
    return {theta[0]*a00+theta[1]*a01+theta[2]*a02-y*r0,
            theta[0]*a01+theta[1]*a11+theta[2]*a12-y*r1,
            theta[0]*a02+theta[1]*a12+theta[2]*a22-y*r2};
}

void taylor_scores(const Vec& theta2, const Vec& theta4, double w,
                   double v, double f, double y, Vec& out2, Vec& out4) {
    Vec d[5] = {
        feature(w, f),
        {std::cos(w), -f*std::sin(f*w), 2*w},
        {-std::sin(w), -f*f*std::cos(f*w), 2},
        {-std::cos(w), f*f*f*std::sin(f*w), 0},
        {std::sin(w), std::pow(f, 4)*std::cos(f*w), 0}
    };
    auto expansion = [&](const Vec& theta, bool fourth) {
        double a[5] = {dot(theta,d[0])-y, dot(theta,d[1]), dot(theta,d[2]),
                       dot(theta,d[3]), dot(theta,d[4])};
        Vec value{};
        for (int i=0; i<3; ++i) {
            double g0=a[0]*d[0][i];
            double g2=a[2]*d[0][i]+2*a[1]*d[1][i]+a[0]*d[2][i];
            value[i]=g0-v*g2/2;
            if (fourth) {
                double g4=a[4]*d[0][i]+4*a[3]*d[1][i]+6*a[2]*d[2][i]
                         +4*a[1]*d[3][i]+a[0]*d[4][i];
                value[i]+=v*v*g4/8;
            }
        }
        return value;
    };
    out2=expansion(theta2, false);
    out4=expansion(theta4, true);
}

double posterior_mean(double w, double low, double high, double prob,
                      double jitter, double sigma) {
    double var=jitter*jitter+sigma*sigma;
    double a=std::log(prob)-(w-low)*(w-low)/(2*var);
    double b=std::log1p(-prob)-(w-high)*(w-high)/(2*var);
    double delta=std::max(-700.0,std::min(700.0,b-a));
    double p=1/(1+std::exp(delta));
    double gain=jitter*jitter/var;
    return p*(low+gain*(w-low))+(1-p)*(high+gain*(w-high));
}

int main(int argc, char** argv) {
    try {
        if (argc != 16) throw std::runtime_error("expected 15 arguments");
        int runs=std::stoi(argv[1]);
        int iterations=std::stoi(argv[2]);
        std::uint64_t seed=std::stoull(argv[3]);
        double mix=std::stod(argv[4]), low=std::stod(argv[5]), high=std::stod(argv[6]);
        double jitter=std::stod(argv[7]), sigma=std::stod(argv[8]);
        double f=std::stod(argv[9]);
        double c=std::stod(argv[10]), shift=std::stod(argv[11]);
        Vec star={std::stod(argv[12]),std::stod(argv[13]),std::stod(argv[14])};
        std::ifstream check_file(argv[15]);
        if (!check_file) throw std::runtime_error("could not read checkpoint file");
        std::vector<int> checks;
        int checkpoint;
        while (check_file>>checkpoint) checks.push_back(checkpoint);
        if (checks.empty() || checks.front()!=0 || checks.back()!=iterations)
            throw std::runtime_error("invalid checkpoints");
        std::vector<std::array<Vec,METHODS>> states(runs);
        std::vector<std::array<Vec,2>> simex_aux(runs);
        std::mt19937_64 rng(seed);
        std::uniform_real_distribution<double> uniform(0,1);
        std::normal_distribution<double> normal(0,1);
        const double v=sigma*sigma;
        std::size_t next_check=0;
        auto record = [&](int t) {
            std::array<double,METHODS> mse{};
            for (int run=0; run<runs; ++run) {
                const auto& stream=states[run];
                for (int method=0; method<METHODS; ++method) {
                    for (int k=0;k<3;++k) {
                        double value=stream[method][k];
                        if (method==3)
                            value=3*stream[3][k]-3*simex_aux[run][0][k]
                                  +simex_aux[run][1][k];
                        double e=value-star[k];
                        mse[method]+=e*e;
                    }
                }
            }
            std::cout<<t;
            for (double value : mse) std::cout<<','<<value/runs;
            std::cout<<'\n';
            ++next_check;
        };
        std::cout<<std::setprecision(17);
        record(0);
        for (int t=1;t<=iterations;++t) {
            double eta=c/(t+shift);
            for (int run=0; run<runs; ++run) {
                auto& stream=states[run];
                double z=(uniform(rng)<mix ? low : high)+jitter*normal(rng);
                double y=dot(star,feature(z,f));
                double w=z+sigma*normal(rng);
                double V=sigma*normal(rng);
                std::array<Vec,METHODS> g;
                g[0]=score(stream[0], z, f, y);
                g[1]=score(stream[1], w, f, y);
                taylor_scores(stream[2],stream[8],w,v,f,y,g[2],g[8]);
                g[3]=score(stream[3],w,f,y);
                Vec m1=moment_score(simex_aux[run][0],w,v,f,y);
                Vec m2=moment_score(simex_aux[run][1],w,2*v,f,y);
                g[4]=complex_score(stream[4],{w,sigma},f,y);
                double zhat=posterior_mean(w,low,high,mix,jitter,sigma);
                g[5]=score(stream[5],zhat,f,y);
                g[6]=complex_score(stream[6],{w,V},f,y);
                g[7]=moment_score(stream[7],w,-v,f,y);
                for(int method=0;method<METHODS;++method)
                    for(int k=0;k<3;++k)
                        stream[method][k]-=eta*g[method][k];
                for(int k=0;k<3;++k) {
                    simex_aux[run][0][k]-=eta*m1[k];
                    simex_aux[run][1][k]-=eta*m2[k];
                }
            }
            if (next_check<checks.size() && t==checks[next_check]) record(t);
            if (t%100000==0) std::cerr<<"iteration "<<t<<'/'<<iterations<<'\n';
        }
    } catch (const std::exception& e) {
        std::cerr<<"simulation error: "<<e.what()<<'\n';
        return 1;
    }
    return 0;
}
