"""Independent Decimal RK4 arithmetic; the caller supplies a reviewed RHS."""
from decimal import Decimal,localcontext


def integrate(*,state,dt,steps,rhs):
    with localcontext()as context:
        context.prec=120
        d=Decimal.from_float;h=d(float(dt));y=tuple(float(v)for v in state)
        k1,f1=rhs(y);totals=(0.0,)*len(f1);samples=[{'state':y,'transfers':totals}]
        def shifted(values,rates,factor):
            return tuple(float(d(value)+h*factor*d(rate))for value,rate in zip(values,rates,strict=True))
        def weighted(a,b,c,e):
            return tuple((d(w)+Decimal(2)*d(x)+Decimal(2)*d(z)+d(t))/Decimal(6)
                for w,x,z,t in zip(a,b,c,e,strict=True))
        for _ in range(steps):
            k2,f2=rhs(shifted(y,k1,Decimal(1)/2))
            k3,f3=rhs(shifted(y,k2,Decimal(1)/2))
            k4,f4=rhs(shifted(y,k3,Decimal(1)))
            y=tuple(float(d(old)+h*rate)for old,rate in zip(y,weighted(k1,k2,k3,k4),strict=True))
            totals=tuple(float(d(old)+h*rate)for old,rate in zip(totals,weighted(f1,f2,f3,f4),strict=True))
            samples.append({'state':y,'transfers':totals});k1,f1=rhs(y)
        return samples
