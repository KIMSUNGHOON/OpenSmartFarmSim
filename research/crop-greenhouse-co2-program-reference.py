"""App-free Decimal80 piecewise outdoor153-vector RK and independent removal."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
INPUTS = {
    "research/crop-greenhouse-co2-integration-reference.py": "6f592d4cecc4c7e1048fae05d9b6b7bb92fb16787210fcd4caeb85315274714e",
    "research/crop-climate-joint-management-reference.py": "7982b0af6adc72a894255db06e7b4b3db2088a4fe58c84830a87b37235ed0fa4",
    "fixtures/crop-greenhouse-solar-program-reference-cases-v1.json": "47a4ade9baf98e1a274168618362fb145291ade744a60dd7fdfd89bdf1f5a700",
    "fixtures/crop-greenhouse-co2-integration-reference-cases-v1.json": "f52f2ecf9bbf5d10f1c7b5573c4db0985dd67945be15fdebb2dcb3424b7061b3"}


def trajectory(case, dt, ref, env, management):
    s = case["scenario"]; prior = env["env"]["base"]["prior"]; core_env = env["env"]["base"]["env"]
    def index(i):
        scaled = D(i) * D(str(case["step_seconds"])) / dt
        assert scaled == int(scaled)
        return int(scaled)
    count = index(case["step_count"])
    weather = {index(row["step_index"]): row for row in case["forcing_program"]}
    schedule = {index(row["step_index"]): row["event"] for row in case["events"]}
    outputs = {index(i) for i in case["output_steps"]}
    y = prior["initial"](s) + (D(str(s["climate_state"]["air_co2_mass"]["value"])),) + (D(0),) * len(env["flows"])
    totals = {k: D(0) for k in management["EVENT_FIELDS"]}; samples, journal = [], []
    def derived():
        return {**management["derived"](s, y, core_env), "crop_co2_ppm": str(ref["ppm"](s, active["co2"], y, env))}
    for i in range(count + 1):
        if i:
            rhs = lambda z: ref["rhs"](s, active["solar"], active["ventilation"], active["co2"], z, env)
            a = rhs(y); b = rhs(tuple(v+dt*k/2 for v,k in zip(y,a,strict=True)))
            c = rhs(tuple(v+dt*k/2 for v,k in zip(y,b,strict=True)))
            d = rhs(tuple(v+dt*k for v,k in zip(y,c,strict=True)))
            y = tuple(v+dt*(p+2*q+2*r+t)/6 for v,p,q,r,t in zip(y,a,b,c,d,strict=True))
        if i in weather: active = weather[i]
        if i in schedule:
            before = list(map(str,y[:109])); before_derived = derived()
            current = prior["trial"](s,y[:108])
            _, removed = management["removal"](current,schedule[i],prior,core_env)
            increments = {k: sum(map(D,v)) if isinstance(v,list) else D(v) for k,v in removed["removed"].items()}
            totals = {k: totals[k]+increments[k] for k in totals}
            y = tuple(map(D,removed["state"])) + y[108:]
            journal.append({"step_index":i,"elapsed_seconds":str(i*dt),"before":before,
                "after":list(map(str,y[:109])),"removed_totals":{k:str(v) for k,v in increments.items()},
                "derived_before":before_derived,"derived_after":derived()})
        if i in outputs:
            samples.append({"step_index":i,"elapsed_seconds":str(i*dt),"forcing_step_index":index(active["step_index"]),
                "state":list(map(str,y[:109])),"integrated_transfers":dict(zip(env["flows"],map(str,y[109:]),strict=True)),
                "event_totals":{k:str(v) for k,v in totals.items()},"event_count":len(journal),"derived":derived()})
    return {"samples":samples,"events":journal}


def references():
    for name,digest in INPUTS.items(): assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    ref = runpy.run_path(str(ROOT/"research/crop-greenhouse-co2-integration-reference.py"))
    management = runpy.run_path(str(ROOT/"research/crop-climate-joint-management-reference.py"))
    source = {c["case_id"]:c for c in json.loads((ROOT/"fixtures/crop-greenhouse-solar-program-reference-cases-v1.json").read_bytes())["cases"]}
    boundary = json.loads((ROOT/"fixtures/crop-greenhouse-co2-integration-reference-cases-v1.json").read_bytes())["cases"][0]["co2"]
    cases = []
    with localcontext() as context:
        context.prec=80;env=ref["environment"]()
        for position,name in enumerate(("no-events","warm-mid","initial","final","multiple","negative-reference",
                                       "zero-reference","weather-mid","weather-multiple","weather-no-events")):
            original = source[name if name in source else {"weather-mid":"warm-mid","weather-multiple":"multiple","weather-no-events":"no-events"}[name]]
            c=deepcopy({k:original[k] for k in ("scenario","events","output_steps","step_seconds","step_count")})
            c["case_id"]=name;del c["scenario"]["forcing"]["co2"]
            c["scenario"]["climate_state"]["air_co2_mass"]={"value":2500.0,"unit":"mg_CO2/m2_floor"}
            co2=deepcopy(boundary);co2["basis"]="wet" if position%2==0 else "dry"
            c["forcing_program"]=[{"step_index":0,"solar":deepcopy(original["solar"]),
                "ventilation":deepcopy(original["ventilation"]),"co2":co2}]
            if name.startswith("weather-"):
                indices=[4,8,16] if name=="weather-multiple" else [8]
                c["output_steps"]=[0,4,8,12,16]
                for j,i in enumerate(indices):
                    row=deepcopy(c["forcing_program"][0]);row["step_index"]=i
                    for key in ("solar","ventilation","co2"):row[key]["input_id"]+='-change-'+str(i)
                    row["solar"]["values"]["outdoor_global_radiation"]["value"]=0 if j%2==0 else 450
                    row["ventilation"]["forcing"]["outdoor_air_temperature"]["value"]=28 if j%2==0 else 10
                    row["ventilation"]["forcing"]["outdoor_vapor_pressure"]["value"]=2800 if j%2==0 else 700
                    row["ventilation"]["forcing"]["volume_exchange_per_floor_area"]["value"]=0 if j==1 else 0.02
                    row["co2"]["forcing"]["outdoor_co2_density"]["value"]=400 if j%2==0 else 800
                    row["co2"]["forcing"]["external_co2_flux"]["value"]=-0.2 if j%2==0 else 2
                    if i==16:row["co2"]["parameters"]["air_pressure"]["value"]=100000
                    c["forcing_program"].append(row)
            c["expected_decimal"]=trajectory(c,D(2),ref,env,management)
            if name.startswith("weather-"):c["fine_32s_dt0_25_decimal"]=trajectory(c,D('.25'),ref,env,management)
            cases.append(c)
    return {"version":"crop-greenhouse-co2-program-reference-cases-v1",
        "generator_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),"input_sha256":INPUTS,
        "oracle":"Decimal80_app_free153_vector_piecewise_old_interval_then_new_boundary_then_removal",
        "scope":"self_authored_synthetic_math_only","G0_G4":"not_assessed","cases":cases}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    with args.output.open('x') as output:output.write(json.dumps(references(),indent=2,sort_keys=True,allow_nan=False)+'\n')
