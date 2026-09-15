"""Simple Indian English theory and practical guidance."""


THEORY_SECTIONS = [
    {
        "title": "Theory of the preparation",
        "content": """
<h2 style="color:#0D47A1;">Frog Rectus Abdominis Preparation</h2>
<p>Frog rectus abdominis is a thin paired skeletal muscle present on the front
side of the abdomen. The isolated muscle gives a graded contracture when
acetylcholine is added to the organ bath. A graded response means that the
height of contraction increases with concentration until the maximum response
is reached.</p>

<h3 style="color:#1565C0;">Why this preparation is useful</h3>
<ul>
  <li>The muscle has nicotinic Nm receptors.</li>
  <li>Bath applied acetylcholine produces a slow and measurable contracture.</li>
  <li>The response is suitable for studying concentration response relation.</li>
  <li>The preparation can demonstrate competitive blockade by d tubocurarine.</li>
  <li>Known responses can be used to estimate an unknown ACh concentration.</li>
</ul>

<h3 style="color:#1565C0;">Organ bath conditions</h3>
<p>The tissue is mounted in Frog Ringer solution. One end is fixed and the other
end is connected to a lever or force transducer. The solution is aerated and is
kept near room temperature. The tissue is allowed to equilibrate before the
first dose. The response depends on frog species, tissue condition, temperature,
solution, resting tension and contact time. Therefore the EC50 shown in this
simulator is an educational calibration and not a universal biological value.</p>
""",
    },
    {
        "title": "ACh action and concentration response",
        "content": """
<h2 style="color:#0D47A1;">Action of Acetylcholine</h2>
<p>Acetylcholine binds to nicotinic Nm receptors on the skeletal muscle membrane.
These receptors are ligand gated cation channels. Channel opening allows mainly
sodium entry and produces depolarisation. The muscle develops a sustained
contracture when ACh is present in the bath.</p>

<h3 style="color:#1565C0;">Concentration response relation</h3>
<p>A low ACh concentration gives a small response. Increasing concentration
increases the response. Near the maximum, a further increase produces very
little extra contraction. This is a monotonic and saturable relation.</p>
<p style="background:#EAF4FF; padding:10px; border-radius:6px; text-align:center;">
Response = Emax × D<sup>n</sup> / (EC50<sup>n</sup> + D<sup>n</sup>)
</p>
<p>D is the final bath concentration. EC50 is the concentration which gives half
of Emax. The Hill coefficient n describes the steepness. The simulator uses an
ACh EC50 calibration of 3 micromolar and a Hill coefficient of 1.6. These values
give a clear teaching curve. A real experiment may give different values.</p>

<h3 style="color:#1565C0;">Good working range</h3>
<p>Bioassay standards should preferably give submaximal responses. A practical
range is about 20 to 80 percent of maximum. Very small responses are difficult
to measure. Responses near 100 percent cannot clearly separate two doses.</p>
""",
    },
    {
        "title": "Units and preparation of solutions",
        "content": """
<h2 style="color:#0D47A1;">Concentration Units</h2>
<p>The concentration box accepts decimal numbers and scientific notation. You may
select M, mM, micromolar, nM or pM. Mass units are also available. For mass unit
conversion the simulator treats the material as acetylcholine chloride with a
molecular weight of 181.66 g per mole.</p>

<p><b>Useful relations</b></p>
<ul>
  <li>1 mM is 0.001 M.</li>
  <li>1 micromolar is 0.000001 M.</li>
  <li>1 mg per mL is 1 g per L.</li>
  <li>Molar concentration is mass in g per L divided by molecular weight.</li>
</ul>

<h3 style="color:#1565C0;">Stock and final bath concentration</h3>
<p>The virtual lab asks for the final concentration present in the organ bath. It
does not treat the entered value as a stock bottle concentration. In a real
organ bath, when a small volume is added, the final concentration is calculated
as follows.</p>
<p style="background:#FFF8E1; padding:10px; border-radius:6px; text-align:center;">
Final bath concentration = Stock concentration × Volume added / Bath volume
</p>
<p>Use the same volume unit for volume added and bath volume. Clearly write in the
record whether a value is stock concentration or final bath concentration.</p>
""",
    },
    {
        "title": "Practical 1 Basic ACh response",
        "content": """
<h2 style="color:#0D47A1;">Practical Setting 1: Record a Basic ACh Response</h2>
<p><b>Aim:</b> To observe the contracture produced by acetylcholine on frog rectus
abdominis.</p>

<p><b>Setup:</b> Mount the tissue in aerated Frog Ringer solution. Connect it to the
recording lever. Apply suitable resting tension. Allow adequate equilibration.
Keep bath condition and contact time the same for every dose.</p>

<p><b>Procedure:</b></p>
<ol>
  <li>Open Virtual Experiment Lab.</li>
  <li>Select Acetylcholine.</li>
  <li>Enter a final bath concentration such as 1 micromolar.</li>
  <li>Press Add selected drug to bath.</li>
  <li>Observe the muscle and the kymograph.</li>
  <li>Note dose, response percentage and graph height in millimetres.</li>
  <li>Wash the tissue and allow it to return to baseline.</li>
  <li>Repeat only after a proper wash and recovery period.</li>
</ol>

<p><b>Expected result:</b> ACh produces a contracture. A higher concentration gives
a higher response until the maximum is approached.</p>

<p><b>Important points:</b> Do not give the next agonist before washing. Do not
compare responses recorded with different contact times. The green line is the
5 mm baseline. Graph height means height above this baseline.</p>
""",
    },
    {
        "title": "Practical 2 ACh dose response curve",
        "content": """
<h2 style="color:#0D47A1;">Practical Setting 2: ACh Concentration Response Curve</h2>
<p><b>Aim:</b> To record increasing responses and construct the concentration
response curve of acetylcholine.</p>

<p><b>Procedure:</b></p>
<ol>
  <li>Use a fresh equilibrated tissue and first obtain a stable baseline.</li>
  <li>Select a series of increasing final bath concentrations. A useful teaching
  series is 0.3, 1, 3, 10 and 30 micromolar.</li>
  <li>Give the lowest concentration first.</li>
  <li>Record the response after the same contact time.</li>
  <li>Wash the tissue completely and allow recovery.</li>
  <li>Repeat with the next concentration.</li>
  <li>Plot log concentration on the horizontal axis and response percentage on
  the vertical axis.</li>
</ol>

<p><b>Observation:</b> The semi log curve is sigmoid. EC50 is read at 50 percent of
the maximum response. Emax shows efficacy. A lower EC50 indicates greater
potency when preparations and conditions are comparable.</p>

<p><b>Common errors:</b> Incomplete washing may increase the next response.
Excessive waiting may change tissue sensitivity. Very high concentrations add
little information because the response has already reached the ceiling.</p>
""",
    },
    {
        "title": "Practical 3 Competitive antagonism",
        "content": """
<h2 style="color:#0D47A1;">Practical Setting 3: d Tubocurarine Antagonism</h2>
<p><b>Aim:</b> To demonstrate competitive antagonism of ACh by d tubocurarine on
nicotinic Nm receptors.</p>

<p><b>Control curve:</b> First record an ACh concentration response curve without
antagonist. Maintain equal contact time and complete washing between doses.</p>

<p><b>Antagonist curve:</b></p>
<ol>
  <li>Select d Tubocurarine in the pre incubation section.</li>
  <li>Enter its final bath concentration and apply pre incubation.</li>
  <li>Allow the same pre incubation time before each ACh series.</li>
  <li>Repeat the ACh concentration response curve.</li>
  <li>Compare EC50 and Emax with the control curve.</li>
</ol>

<p><b>Expected result:</b> The ACh curve shifts to the right in a nearly parallel
manner. Emax remains achievable if enough agonist is given. This is surmountable
competitive antagonism. The dose ratio follows 1 plus antagonist concentration
divided by KB in the simple Schild model.</p>

<p><b>Why atropine is not selected:</b> Atropine blocks muscarinic receptors. The
frog rectus skeletal muscle response used here is mediated by nicotinic Nm
receptors. Therefore atropine should not be shown as a meaningful competitive
blocker of this ACh contracture.</p>
""",
    },
    {
        "title": "Practical 4 Unknown ACh bioassay",
        "content": """
<h2 style="color:#0D47A1;">Practical Setting 4: Estimate Unknown ACh Concentration</h2>
<p><b>Aim:</b> To estimate the concentration of a coded acetylcholine chloride
sample by comparing its tissue response with known standards.</p>

<h3 style="color:#1565C0;">Interpolation method</h3>
<ol>
  <li>Record responses to several known standards under identical conditions.</li>
  <li>Give the unknown sample and record its response.</li>
  <li>Find two neighbouring standard responses which bracket the unknown.</li>
  <li>Interpolate between their concentrations on the log concentration scale.</li>
</ol>

<h3 style="color:#1565C0;">Three point bioassay</h3>
<p>Record low standard S1, unknown test T and high standard S2. The response of T
must lie between S1 and S2. Estimate T by log interpolation. This method is
simple but depends strongly on the two selected standards.</p>

<h3 style="color:#1565C0;">Four point bioassay</h3>
<p>Record two standard doses S1 and S2 and two proportional unknown doses T1 and
T2. The dose ratio S2 divided by S1 must equal the test dose ratio T2 divided by
T1. All four responses should lie in the approximately linear submaximal part of
the log concentration response curve. The standard and test lines should be
approximately parallel. The parallel line calculation then estimates the
concentration represented by T1.</p>

<p><b>Good sequence:</b> Use alternating standard and test doses, wash after every
response and keep the recovery period constant. Repeat readings when required.
Do not reveal the coded concentration until the student has entered an estimate.</p>

<p><b>Result:</b> Report the estimated concentration with unit, the coded value and
absolute percentage error. The simulator accepts an estimate within 15 percent
for practice. This limit is a teaching rule and not a laboratory validation
criterion.</p>
""",
    },
    {
        "title": "Reading and saving the result",
        "content": """
<h2 style="color:#0D47A1;">How to Read the Kymograph</h2>
<p>The horizontal direction represents recording time. The vertical axis shows
kymograph height in millimetres. Drug markers show what was added. The recording
does not stop after four observations. It becomes wider and the horizontal bar
can be moved to inspect every earlier response.</p>

<p>Use Follow latest while recording. Clear it when you want to examine an old
response. Save recording as PNG stores the complete trace, not only the visible
screen. The image also contains a table with dose or sample, response percentage,
graph height and note. In an unknown exercise the coded concentration is added to
the result note only after it is revealed.</p>

<h3 style="color:#1565C0;">Ethical use</h3>
<p>This computer assisted exercise supports replacement and reduction in animal
teaching. It helps the student understand the method and practise calculations.
It is an educational simulation and should not be used as measured laboratory or
clinical data.</p>
""",
    },
]


def get_theory_titles():
    return [section["title"] for section in THEORY_SECTIONS]


def get_theory_content(index):
    if 0 <= index < len(THEORY_SECTIONS):
        return THEORY_SECTIONS[index]["content"]
    return "<p>Section not found.</p>"


def get_all_theory_html():
    return "<hr>".join(section["content"] for section in THEORY_SECTIONS)
