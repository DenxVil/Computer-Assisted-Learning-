import Link from "next/link";

const experiments = [
  { id: "dog-bp", number: "01", title: "Dog Blood Pressure", subtitle: "Autonomic drugs, arterial pressure and heart rate", description: "Give known drugs in sequence, study receptor blockade, compare pressure and pulse traces, and observe tachyphylaxis.", color: "blue", tags: ["Continuous tracing", "Blocker studies", "Observation log"] },
  { id: "rabbit-eye", number: "02", title: "Rabbit Eye", subtitle: "Paired-eye examination practical", description: "Treat one eye, retain saline as the control, and examine pupil size, reflexes, conjunctiva and ocular tone.", color: "amber", tags: ["Ruler", "Torch", "Cotton swab"] },
  { id: "frog-rectus", number: "03", title: "Frog Rectus Abdominis", subtitle: "Organ bath and concentration response", description: "Record graded contractions, wash the tissue, plot dose-response curves and study competitive blockade.", color: "green", tags: ["Organ bath", "Live tracing", "Dose response"] },
  { id: "bioassay", number: "04", title: "Acetylcholine Bioassay", subtitle: "Estimate an unknown by biological response", description: "Compare standard and unknown acetylcholine doses with interpolation and three-point or four-point assay methods.", color: "purple", tags: ["Hidden unknown", "Assay methods", "Result calculation"] },
];

export default function Home() {
  return <main className="home-shell">
    <nav className="home-nav"><Link href="/" className="brand-mark">CAL<span>LAB</span></Link><span className="nav-caption">MAMC · NEW DELHI</span></nav>
    <section className="hero"><div className="hero-copy"><span className="eyebrow">COMPUTER ASSISTED LEARNING</span><h1>Virtual Pharmacology<br/><em>Laboratory</em></h1><p>Explore classic pharmacology practicals through interactive, mechanism-based teaching simulations.</p><a className="primary-link" href="#experiments">Explore experiments <span>↓</span></a></div><div className="hero-visual" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="hero-core">Rx</div><span className="float-tag tag-a">Dose response</span><span className="float-tag tag-b">Receptor action</span><span className="float-tag tag-c">Virtual practical</span></div></section>
    <section className="experiment-section" id="experiments"><div className="section-heading"><div><span className="eyebrow">THE PRACTICALS</span><h2>Choose an experiment</h2></div><span className="section-count">04 MODULES</span></div><div className="experiment-grid">{experiments.map(item=><Link className={`experiment-card ${item.color}`} href={`/experiments/${item.id}`} key={item.id}><div className="card-top"><span className="card-number">{item.number} / 04</span><span className="card-arrow">↗</span></div><div className="card-icon" aria-hidden="true">{item.id === "dog-bp" ? "〽" : item.id === "rabbit-eye" ? "◉" : item.id === "frog-rectus" ? "⌁" : "∿"}</div><h3>{item.title}</h3><span className="card-subtitle">{item.subtitle}</span><p>{item.description}</p><div className="tag-row">{item.tags.map(tag=><span key={tag}>{tag}</span>)}</div><div className="card-action">Open practical <span>→</span></div></Link>)}</div></section>
    <section className="home-note"><span className="note-mark">i</span><p><strong>For learning and demonstration.</strong> Simulation curves are educational models; experimental responses vary with preparation and conditions.</p></section>
    <footer className="home-footer"><span>Virtual Pharmacology Laboratory</span><span>Department of Pharmacology · MAMC, New Delhi</span></footer>
  </main>;
}

