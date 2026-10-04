"""Independent Decimal source-equation oracle; does not import product code.

GreenLight/Vanthoor basis and BSD notice: crop-growth-reference-parameters-v1.json
and LICENSES/GreenLight-BSD-3-Clause-Clear.txt. Outputs are synthetic math only.
"""
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ("buffer", "leaf", "stem_root", "fruit", "temperature_filtered_24h", "temperature_sum")
FLUX = ("photosynthesis", "growth_respiration", "maintenance_leaf", "maintenance_stem_root",
        "maintenance_fruit", "removal_leaf", "removal_stem_root", "removal_fruit")


def decimal_rhs(y, forcing, removal, p):
    one, two = Decimal(1), Decimal(2)
    s = dict(zip(STATE, y[:6])); t = forcing["canopy_temperature"]; tm = s["temperature_filtered_24h"]
    lai = p["sla"] * s["leaf"]; tk = t + p["kelvin_offset"]; gas = p["R"] / 1000
    if forcing["par_above_canopy"] == 0:
        assimilation = Decimal(0)
    else:
        absorption = forcing["par_above_canopy"] * (one-p["rhoCanPar"]) * (
            one-(-p["k1Par"]*lai).exp() + p["rhoFlrPar"]*(-p["k1Par"]*lai).exp() * (one-(-p["k2Par"]*lai).exp()))
        potential = lai*p["j25LeafMax"] * (p["eJ"]*(tk-p["t25k"])/(gas*tk*p["t25k"])).exp() * (
            one+((p["S"]*p["t25k"]-p["H"])/(gas*p["t25k"])).exp()) / (one+((p["S"]*tk-p["H"])/(gas*tk)).exp())
        light = p["alpha"] * absorption
        transport = (potential+light-((potential+light)**2-4*p["theta"]*potential*light).sqrt()) / (two*p["theta"])
        gamma = p["cGamma"] * (p["compensation_pivot_c"] + (t-p["compensation_pivot_c"])/lai)
        ci = p["etaCo2AirStom"]*forcing["co2"]; assert 0 <= gamma <= ci
        photo = transport*(ci-gamma)/(4*(ci+two*gamma)); respiration = photo*gamma/ci
        full = one/(one+(p["buffer_full_slope"]*(s["buffer"]-p["cBufMax"])).exp())
        assimilation = p["mCh2o"]*full*(photo-respiration)
    buffer_factor = one/(one+(-p["buffer_empty_slope"]*(s["buffer"]-p["cBufMin"])).exp())
    instant = one/(one+(-p["instant_low_slope"]*(t-p["tCanMin"])).exp()) / (one+(p["instant_high_slope"]*(t-p["tCanMax"])).exp())
    filtered = one/(one+(-p["filtered_low_slope"]*(tm-p["tCan24Min"])).exp()) / (one+(p["filtered_high_slope"]*(tm-p["tCan24Max"])).exp())
    x=s["temperature_sum"]/p["tEndSum"]; smooth=p["development_smoothing_squared"]
    development=(x+(x*x+smooth).sqrt())/two - (x-one+((x-one)**2+smooth).sqrt())/two
    common=buffer_factor*filtered*(p["allocation_temperature_slope"]*tm+p["allocation_temperature_intercept"])
    allocation={"leaf":common*p["rgLeaf"], "stem_root":common*p["rgStem"], "fruit":common*instant*development*p["rgFruit"]}
    growth=sum(p[k]*allocation[o] for o,k in (("leaf","cLeafG"),("stem_root","cStemG"),("fruit","cFruitG")))
    maintenance_factor=(one-(-p["cRgr"]*p["rgr"]).exp()) * (p["q10m"].ln()*(tm-p["maintenance_temperature_reference_c"])/p["q10_temperature_interval_c"]).exp()
    maintenance={o:maintenance_factor*s[o]*p[k] for o,k in (("leaf","cLeafM"),("stem_root","cStemM"),("fruit","cFruitM"))}
    derivatives=[assimilation-sum(allocation.values())-growth,
                 *[allocation[o]-maintenance[o]-removal[o] for o in ("leaf","stem_root","fruit")],
                 (t-tm)/p["seconds_per_day"], t/p["seconds_per_day"]]
    return derivatives+[assimilation,growth,*[maintenance[o] for o in ("leaf","stem_root","fruit")],
                        *[removal[o] for o in ("leaf","stem_root","fruit")]]


def solve_reference(program, p, step):
    start=datetime.fromisoformat(program["segments"][0]["start"].replace("Z","+00:00"))
    seconds=lambda stamp: Decimal(str((datetime.fromisoformat(stamp.replace("Z","+00:00"))-start).total_seconds()))
    segments=[(seconds(s["start"]),seconds(s["end"]),
               {k:Decimal(str(v["value"])) for k,v in s["forcing"]["values"].items()},
               {k:Decimal(str(v["value"])) for k,v in s["removals"]["values"].items()}) for s in program["segments"]]
    event_by_time={seconds(e["at"]):e for e in program["events"]}
    output_by_time={seconds(t):t for t in program["output_times"]}
    boundaries=sorted(set([s[1] for s in segments]+list(event_by_time)+list(output_by_time)))
    y=[Decimal(str(program["initial_state"]["values"][k]["value"])) for k in STATE]+[Decimal(0)]*8
    initial_total=sum(y[:4]); t=Decimal(0); index=0; frames=[]
    for target in boundaries:
        while t<target:
            h=min(step,target-t); _,_,forcing,removal=segments[index]
            k1=decimal_rhs(y,forcing,removal,p)
            k2=decimal_rhs([v+h*d/2 for v,d in zip(y,k1)],forcing,removal,p)
            k3=decimal_rhs([v+h*d/2 for v,d in zip(y,k2)],forcing,removal,p)
            k4=decimal_rhs([v+h*d for v,d in zip(y,k3)],forcing,removal,p)
            y=[v+h*(a+2*b+2*c+d)/6 for v,a,b,c,d in zip(y,k1,k2,k3,k4)]; t+=h
        if t in event_by_time:
            e=event_by_time[t]
            for organ in ("leaf","stem_root","fruit"):
                mass=Decimal(str(e["removals"]["values"][organ]["value"]))
                y[STATE.index(organ)]-=mass; y[6+FLUX.index("removal_"+organ)]+=mass
        if index+1<len(segments) and t==segments[index][1]: index+=1
        if t in output_by_time:
            residual=sum(y[:4])-initial_total-y[6]+sum(y[7:])
            frames.append({"at":output_by_time[t],"state":{k:str(v) for k,v in zip(STATE,y[:6])},
                           "cumulative":{k:str(v) for k,v in zip(FLUX,y[6:])},
                           "lai":str(p["sla"]*y[1]),"carbon_residual":str(residual)})
    return frames


def main():
    profile_path=ROOT/"fixtures/crop-growth-reference-parameters-v1.json"; raw=profile_path.read_bytes()
    assert sha256(raw).hexdigest()=="d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca"
    rate_path=ROOT/"fixtures/crop-growth-reference-cases-v1.json"; cases=json.loads(rate_path.read_bytes())["cases"]
    stamp=lambda second: (datetime(2026,1,1)+timedelta(seconds=second)).isoformat()+"Z"
    initial=deepcopy(cases[0]["state"]); initial["input_id"]="integration-synthetic-initial-v1"
    segments=[]
    for number,(begin,end,source) in enumerate(((0,120,0),(120,240,3),(240,300,1))):
        forcing=deepcopy(cases[source]["forcing"]); forcing["input_id"]="integration-forcing-"+str(number)
        if number==2:forcing["values"]["canopy_temperature"]["value"]=17
        removal=deepcopy(cases[0]["removals"]); removal["input_id"]="integration-continuous-removal-"+str(number)
        if number==1:removal["values"]["leaf"]["value"]=0.01
        if number==2:removal["values"]["fruit"]["value"]=0.05
        segments.append({"start":stamp(begin),"end":stamp(end),"forcing":forcing,"removals":removal})
    events=[]
    for second,organ,mass in ((180,"leaf",100),(300,"fruit",20)):
        removal=deepcopy(cases[0]["removals"]); removal["input_id"]="integration-pulse-"+str(second)
        for k,q in removal["values"].items():q.update(value=mass if k==organ else 0,unit="mg_CH2O/m2_floor")
        events.append({"at":stamp(second),"removals":removal})
    program={"initial_state":initial,"segments":segments,"events":events,
             "output_times":[stamp(s) for s in range(0,301,60)],
             "solver":{"method":"rk4-fixed-v1","max_step_seconds":10,"max_steps":10000,"roundoff_rule":"64-ulp-per-operation-v1"}}
    def reference_pair(candidate, p, step):
        fine=solve_reference(candidate,p,step); coarse=solve_reference(candidate,p,step*2)
        differences={group:{k:{"value":str(max(abs(Decimal(a[group][k])-Decimal(b[group][k])) for a,b in zip(fine,coarse))),
                               "unit":candidate["initial_state"]["values"][k]["unit"] if group=="state" else "mg_CH2O/m2_floor"}
                           for k in fine[0][group]} for group in ("state","cumulative")}
        return fine,differences
    night=deepcopy(program); night["initial_state"]=deepcopy(cases[1]["state"])
    night["initial_state"]["input_id"]="convergence-synthetic-night-state-v1"
    night["initial_state"]["values"]["buffer"]["value"]=json.loads(raw)["parameters"]["cBufMin"]["value"]
    night["segments"]=[{"start":stamp(0),"end":stamp(3600),"forcing":deepcopy(cases[1]["forcing"]),"removals":deepcopy(cases[1]["removals"])}]
    night["events"]=[]; night["output_times"]=[stamp(s) for s in range(0,3601,900)]
    with localcontext() as context:
        context.prec=60; p={k:Decimal(str(v["value"])) for k,v in json.loads(raw)["parameters"].items()}
        fine,differences=reference_pair(program,p,Decimal("0.25"))
        night_fine,night_differences=reference_pair(night,p,Decimal("0.5"))
    document={"fixture_version":"crop-integration-reference-v1","scope":"synthetic software math; no cultivar measurements or gate acceptance",
              "profile_sha256":sha256(raw).hexdigest(),"source_case_sha256":sha256(rate_path.read_bytes()).hexdigest(),
              "generator_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
              "reference_method":"60-digit Decimal original source RHS with independent RK4 at 0.25s; refinement checked against 0.5s; no product imports",
              "refinement_max_absolute_difference_by_quantity":differences,
              "program":program,"expected":fine,
              "convergence_case":{"reference_method":"60-digit Decimal original source RHS, independent RK4 at 0.5s with 1s refinement comparison",
                                  "program":night,"expected":night_fine,"refinement_max_absolute_difference_by_quantity":night_differences}}
    (ROOT/"fixtures/crop-integration-reference-v1.json").write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"samples":len(fine),"refinement_max_absolute_difference_by_quantity":differences}))


if __name__=="__main__":main()
