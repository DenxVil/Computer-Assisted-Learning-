"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Drug = { name: string; ec50_molar: number; emax_pct: number; hill_n: number; material_name: string };
type Point = { time: number; height_mm: number };
type Reading = { drug: string; concentration_molar: number; response_pct: number; height_mm: number; trace: Point[]; isWash?: boolean };
type DrcCurve={drug:string;ec50_molar:number;emax_pct:number;hill_n:number;antagonist_kb_molar:number;antagonist_um:number;points:{concentration_molar:number;response_pct:number;height_mm:number}[]};
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [drug, setDrug] = useState("Acetylcholine");
  const [concentration, setConcentration] = useState("3");
  const [unit, setUnit] = useState("µM");
  const [antagonist, setAntagonist] = useState("0");
  const [readings, setReadings] = useState<Reading[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [washed,setWashed]=useState(true);
  const [view,setView]=useState<"bath"|"drc"|"antagonism">("bath");
  const [drc,setDrc]=useState<DrcCurve[]>([]);
  const [drcError,setDrcError]=useState("");
  const [showEc50,setShowEc50]=useState(true);
  const [showEmax,setShowEmax]=useState(true);
  const [shiftNn,setShiftNn]=useState("100");

  useEffect(() => { fetch(`${API}/api/frog-rectus/drugs`).then(r => r.json()).then(setDrugs).catch(() => setError("Could not connect to the simulation server.")); }, []);

  async function administer(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch(`${API}/api/frog-rectus/response`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ drug, concentration: Number(concentration), unit,
          antagonist_concentration: Number(antagonist), antagonist_unit: "µM" }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Unable to administer dose.");
      setReadings(prev => [...prev, result]);
      setWashed(false);
    } catch (e) { setError(e instanceof Error ? e.message : "Request failed."); }
    finally { setBusy(false); }
  }

  async function washTissue(){
    const last=[...readings].reverse().find(r=>!r.isWash);
    if(!last||washed)return;
    setError("");
    try{const response=await fetch(`${API}/api/frog-rectus/wash`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({current_height_mm:last.height_mm})});const result=await response.json();if(!response.ok)throw new Error(result.detail??"Wash could not be recorded.");setReadings(previous=>[...previous,{drug:"Wash",concentration_molar:0,response_pct:0,height_mm:5,trace:result.trace,isWash:true}]);setWashed(true);}catch(e){setError(e instanceof Error?e.message:"Wash request failed.");}
  }

  async function plotDrc(antagonistConcentrations:number[],append=false){
    setDrcError("");
    if(append&&view==="drc"&&drc.some(c=>c.drug===drug)){setDrcError("This drug is already plotted. Clear the curves or choose another agonist.");return;}
    try{const response=await fetch(`${API}/api/frog-rectus/dose-response`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({drug,antagonist_concentrations_um:antagonistConcentrations})});const result=await response.json();if(!response.ok)throw new Error(result.detail??"Could not calculate the dose-response curve.");const curves=result.curves.map((curve:DrcCurve)=>({...curve,drug:result.drug,ec50_molar:result.ec50_molar,emax_pct:result.emax_pct,hill_n:result.hill_n,antagonist_kb_molar:result.antagonist_kb_molar}));setDrc(previous=>append?[...previous,...curves]:curves);}catch(e){setDrcError(e instanceof Error?e.message:"Could not connect to the simulation server.");}
  }

  const chartData = readings.flatMap((r, index) => r.trace.map(p => ({
    time: index * 1.15 + p.time, height_mm: p.height_mm,
    series: `${r.drug} ${r.concentration_molar.toExponential(2)} M`,
  })));

  return <main className="lab-shell">
    <header className="lab-header"><Link href="/" className="back-link">← All experiments</Link><div className="lab-brand"><span className="eyebrow">PRACTICAL 03 · MAMC</span><h1>Frog Rectus Abdominis</h1></div><span className="badge">ORGAN BATH</span></header>
    <section className="intro"><div><span className="eyebrow">PRACTICAL 01</span><h2>Frog Rectus Abdominis</h2><p>Explore agonist concentration response and competitive nicotinic blockade.</p></div><div className="model-note"><strong>Scientific model</strong><span>Hill response · EC₅₀ 3 µM for ACh · Hill coefficient 1.6</span></div></section>
    <nav className="experiment-tabs"><button className={view==="bath"?"active":""} onClick={()=>setView("bath")}>Virtual practical</button><button className={view==="drc"?"active":""} onClick={()=>{setView("drc");void plotDrc([0]);}}>Dose-response curve</button><button className={view==="antagonism"?"active":""} onClick={()=>{setView("antagonism");void plotDrc([0,0.1,1,10]);}}>Competitive antagonism</button><Link href="/experiments/bioassay">Unknown concentration practical ↗</Link></nav>
    {view==="bath"&&<><div className="workspace">
      <form className="panel controls" onSubmit={administer}>
        <h3>Administer a drug</h3><label>Agonist<select value={drug} onChange={e => setDrug(e.target.value)}>{drugs.map(d => <option key={d.name}>{d.name}</option>)}</select></label>
        <label>Final bath concentration<div className="input-row"><input type="number" min="0" step="any" value={concentration} onChange={e => setConcentration(e.target.value)} required/><select value={unit} onChange={e => setUnit(e.target.value)}>{["M","mM","µM","nM","pM","g/L","mg/mL","mg/L","µg/mL","µg/L"].map(u => <option key={u}>{u}</option>)}</select></div></label>
        <label>d-Tubocurarine in bath (µM)<input type="number" min="0" step="any" value={antagonist} onChange={e => setAntagonist(e.target.value)}/></label>
        <button disabled={busy || !drugs.length || !washed}>{busy ? "Recording…" : "Add dose to organ bath"}</button>
        <button type="button" className="secondary" onClick={washTissue} disabled={washed}>Wash tissue · restore baseline</button>
        {!washed&&<small>Wash the tissue before adding another agonist dose.</small>}
        {error && <p className="error" role="alert">{error}</p>}
        <small>Concentrations are final bath values. ACh mass units use acetylcholine chloride (181.66 g/mol).</small>
      </form>
      <section className="panel graph-panel"><div className="panel-title"><div><h3>Organ bath tracing</h3><p>Contraction in millimetres · baseline 5 mm</p></div><button className="secondary" onClick={() => {setReadings([]);setWashed(true);}} disabled={!readings.length}>Reset experiment</button></div>
        <div className="chart">{chartData.length ? <ResponsiveContainer width="100%" height="100%"><LineChart data={chartData}><CartesianGrid strokeDasharray="3 5"/><XAxis dataKey="time" type="number" domain={[0,"dataMax"]} tickFormatter={v => `${Math.round(v * 10)}s`} label={{value:"Time",position:"insideBottom",offset:-5}}/><YAxis domain={[0,55]} label={{value:"Height (mm)",angle:-90,position:"insideLeft"}}/><Tooltip formatter={(value: number) => [`${value.toFixed(1)} mm`, "Contraction"]}/>{readings.map((r,i)=><Line key={`${i}-${r.drug}`} data={chartData.filter(p=>p.series===`${r.drug} ${r.concentration_molar.toExponential(2)} M`)} dataKey="height_mm" name={`${r.drug} · ${r.concentration_molar.toExponential(2)} M`} stroke={["#136f63","#3467aa","#c06035","#835ab7"][i%4]} strokeWidth={2.5} dot={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer> : <div className="empty"><span className="bath-icon">⌁</span><strong>Your organ bath is ready</strong><span>Choose a concentration and administer a dose to record a contraction.</span></div>}</div>
      </section>
    </div>
    <section className="panel observations"><div className="panel-title"><div><h3>Observations</h3><p>{readings.filter(r=>!r.isWash).length} administered dose(s) recorded this session</p></div></div>
      {readings.length ? <div className="table-wrap"><table><thead><tr><th>Trial</th><th>Drug</th><th>Final bath concentration</th><th>Response</th><th>Peak height</th><th>Cycle</th></tr></thead><tbody>{readings.map((r,i)=><tr key={i}><td>{r.isWash?"—":readings.slice(0,i).filter(v=>!v.isWash).length+1}</td><td>{r.drug}</td><td>{r.isWash?"Fresh Ringer":r.concentration_molar.toExponential(3)+" M"}</td><td>{r.isWash?"Wash":""+r.response_pct.toFixed(1)+"%"}</td><td>{r.height_mm.toFixed(1)} mm</td><td>{r.isWash?"Washed":"In bath"}</td></tr>)}</tbody></table></div> : <p className="quiet">Dose observations will appear here.</p>}
    </section></>}
    {view!=="bath"&&<section className="panel drc-panel">
      <div className="panel-title"><div><h3>{view==="antagonism"?"Competitive nicotinic blockade":"Concentration–response relationship"}</h3><p>{drug} · log concentration on x-axis · response as percent maximum</p></div><button className="secondary" disabled={!drc.length} onClick={()=>setDrc([])}>Clear all curves</button></div>
      <div className="drc-toolbar"><label>Agonist<select value={drug} onChange={e=>setDrug(e.target.value)}>{drugs.map(d=><option key={d.name}>{d.name}</option>)}</select></label>
        {view==="antagonism"?<><label>Antagonist concentration (nM)<input type="number" min="1" max="100000" value={shiftNn} onChange={e=>setShiftNn(e.target.value)}/></label><p>d-Tubocurarine competitively shifts the agonist curve rightward without reducing Emax.</p></>:<div className="drc-options"><label><input type="checkbox" checked={showEc50} onChange={e=>setShowEc50(e.target.checked)}/> Show EC₅₀ lines</label><label><input type="checkbox" checked={showEmax} onChange={e=>setShowEmax(e.target.checked)}/> Show Emax lines</label></div>}
      </div>
      <div className="drc-chart">{drc.length?<ResponsiveContainer width="100%" height="100%"><LineChart><CartesianGrid strokeDasharray="3 5"/><XAxis dataKey="concentration_molar" type="number" scale="log" domain={[1e-8,1e-3]} ticks={[1e-8,1e-7,1e-6,1e-5,1e-4,1e-3]} tickFormatter={v=>Number(v).toExponential(0)} label={{value:"Final bath concentration (M, log scale)",position:"insideBottom",offset:-5}}/><YAxis domain={[0,105]} label={{value:"Response (%)",angle:-90,position:"insideLeft"}}/><Tooltip labelFormatter={v=>`${Number(v).toExponential(2)} M`}/>{drc.map((curve,i)=><Line key={`${curve.drug}-${curve.antagonist_um}`} data={curve.points} dataKey="response_pct" name={view==="drc"?curve.drug:curve.antagonist_um?`${curve.drug} + d-TC ${curve.antagonist_um} µM`:`${curve.drug} control`} type="monotone" stroke={["#136f63","#3467aa","#c06035","#835ab7"][i%4]} strokeWidth={2.5} dot={false} isAnimationActive={false}/>)}{view==="drc"&&drc.map(curve=><>{showEmax&&<ReferenceLine key={`emax-${curve.drug}`} y={curve.emax_pct} stroke="#87958d" strokeDasharray="4 4"/>}{showEc50&&<ReferenceLine key={`ec50-${curve.drug}`} x={curve.ec50_molar} stroke="#87958d" strokeDasharray="4 4"/>}</>)}</LineChart></ResponsiveContainer>:<div className="empty"><strong>Generate a curve</strong><span>Curves use the underlying Frog Rectus teaching model.</span></div>}</div>
      <div className="drc-actions"><button className="primary-button" onClick={()=>plotDrc(view==="antagonism"?[0,0.1,0.5,2]:[0])}>{view==="antagonism"?"Auto: show control and 3 shifts":"Plot dose-response curve"}</button>{view==="drc"?<button className="secondary" onClick={()=>plotDrc([0],true)}>Add another drug</button>:<button className="secondary" onClick={()=>plotDrc([Number(shiftNn)/1000],true)}>Add shifted curve</button>}<span>EC₅₀ {drugs.find(d=>d.name===drug)?.ec50_molar.toExponential(2)} M · Emax {drugs.find(d=>d.name===drug)?.emax_pct}% · Hill n {drugs.find(d=>d.name===drug)?.hill_n}{view==="antagonism"?` · Dose ratio ${(1+(Number(shiftNn)*1e-9)/(drc[0]?.antagonist_kb_molar??2e-7)).toFixed(1)}×`:""}</span></div>
      {drcError&&<p className="error">{drcError}</p>}
    </section>}
    <footer>Educational calibration; real tissue responses vary with species, preparation, temperature and experimental conditions.</footer>
  </main>;
}

