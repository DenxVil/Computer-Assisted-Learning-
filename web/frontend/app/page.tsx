"use client";

import { FormEvent, useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Drug = { name: string; ec50_molar: number; emax_pct: number; hill_n: number; material_name: string };
type Point = { time: number; height_mm: number };
type Reading = { drug: string; concentration_molar: number; response_pct: number; height_mm: number; trace: Point[] };
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
    } catch (e) { setError(e instanceof Error ? e.message : "Request failed."); }
    finally { setBusy(false); }
  }

  const chartData = readings.flatMap((r, index) => r.trace.map(p => ({
    time: index * 1.15 + p.time, height_mm: p.height_mm,
    series: `${r.drug} ${r.concentration_molar.toExponential(2)} M`,
  })));

  return <main className="shell">
    <header><div><span className="eyebrow">MAMC · NEW DELHI</span><h1>Virtual Pharmacology Laboratory</h1><p>Frog rectus abdominis · Organ bath</p></div><span className="badge">TEACHING SIMULATION</span></header>
    <section className="intro"><div><span className="eyebrow">PRACTICAL 01</span><h2>Frog Rectus Abdominis</h2><p>Explore agonist concentration response and competitive nicotinic blockade.</p></div><div className="model-note"><strong>Scientific model</strong><span>Hill response · EC₅₀ 3 µM for ACh · Hill coefficient 1.6</span></div></section>
    <div className="workspace">
      <form className="panel controls" onSubmit={administer}>
        <h3>Administer a drug</h3><label>Agonist<select value={drug} onChange={e => setDrug(e.target.value)}>{drugs.map(d => <option key={d.name}>{d.name}</option>)}</select></label>
        <label>Final bath concentration<div className="input-row"><input type="number" min="0" step="any" value={concentration} onChange={e => setConcentration(e.target.value)} required/><select value={unit} onChange={e => setUnit(e.target.value)}>{["M","mM","µM","nM","pM","g/L","mg/mL","mg/L","µg/mL","µg/L"].map(u => <option key={u}>{u}</option>)}</select></div></label>
        <label>d-Tubocurarine in bath (µM)<input type="number" min="0" step="any" value={antagonist} onChange={e => setAntagonist(e.target.value)}/></label>
        <button disabled={busy || !drugs.length}>{busy ? "Recording…" : "Add dose to organ bath"}</button>
        {error && <p className="error" role="alert">{error}</p>}
        <small>Concentrations are final bath values. ACh mass units use acetylcholine chloride (181.66 g/mol).</small>
      </form>
      <section className="panel graph-panel"><div className="panel-title"><div><h3>Organ bath tracing</h3><p>Contraction in millimetres</p></div><button className="secondary" onClick={() => setReadings([])} disabled={!readings.length}>Clear trace</button></div>
        <div className="chart">{chartData.length ? <ResponsiveContainer width="100%" height="100%"><LineChart data={chartData}><CartesianGrid strokeDasharray="3 5"/><XAxis dataKey="time" type="number" domain={[0,"dataMax"]} tickFormatter={v => `${Math.round(v * 10)}s`} label={{value:"Time",position:"insideBottom",offset:-5}}/><YAxis domain={[0,55]} label={{value:"Height (mm)",angle:-90,position:"insideLeft"}}/><Tooltip formatter={(value: number) => [`${value.toFixed(1)} mm`, "Contraction"]}/>{readings.map((r,i)=><Line key={`${i}-${r.drug}`} data={chartData.filter(p=>p.series===`${r.drug} ${r.concentration_molar.toExponential(2)} M`)} dataKey="height_mm" name={`${r.drug} · ${r.concentration_molar.toExponential(2)} M`} stroke={["#136f63","#3467aa","#c06035","#835ab7"][i%4]} strokeWidth={2.5} dot={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer> : <div className="empty"><span className="bath-icon">⌁</span><strong>Your organ bath is ready</strong><span>Choose a concentration and administer a dose to record a contraction.</span></div>}</div>
      </section>
    </div>
    <section className="panel observations"><div className="panel-title"><div><h3>Observations</h3><p>{readings.length} {readings.length === 1 ? "dose" : "doses"} recorded this session</p></div></div>
      {readings.length ? <div className="table-wrap"><table><thead><tr><th>Drug</th><th>Final bath concentration</th><th>Response</th><th>Peak height</th></tr></thead><tbody>{readings.map((r,i)=><tr key={i}><td>{r.drug}</td><td>{r.concentration_molar.toExponential(3)} M</td><td>{r.response_pct.toFixed(1)}%</td><td>{r.height_mm.toFixed(1)} mm</td></tr>)}</tbody></table></div> : <p className="quiet">Dose observations will appear here.</p>}
    </section>
    <footer>Educational calibration; real tissue responses vary with species, preparation, temperature and experimental conditions.</footer>
  </main>;
}
