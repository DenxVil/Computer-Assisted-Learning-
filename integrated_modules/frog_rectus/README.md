# Frog Rectus Abdominis CAL Simulator

This folder contains source code for an offline experimental pharmacology
teaching simulator. No executable needs to be built while the source is being
reviewed.

## Main learning sections

* Theory and practical guidance with four complete experiment settings
* Responsive virtual organ bath on laptop, desktop and projection displays
* Manual final bath concentration entry with molar and mass units
* Retained kymograph which continues beyond four recordings
* Horizontal review of every old response
* Annotated PNG export with dose, response percentage, height and y axis
* ACh dose response curve using a monotonic saturable Hill model
* Competitive nicotinic blockade by d tubocurarine
* Unknown ACh concentration by interpolation, three point and four point assay

## Scientific calibration

The simulator uses an ACh EC50 calibration of 3 micromolar and Hill coefficient
of 1.6. These are teaching values, not universal biological constants. Frog
species, tissue condition, solution, temperature, resting tension and contact
time can change a real response.

Mass concentration conversion for ACh uses acetylcholine chloride molecular
weight 181.66 g/mol. Concentrations entered in the virtual lab are final organ
bath concentrations. They are not stock bottle concentrations.

Atropine is not offered as the antagonist in the frog rectus practical because
the response is mediated by skeletal muscle nicotinic Nm receptors. d
Tubocurarine is used for the competitive antagonism experiment.

## Run from source

### Windows 10 and Windows 11

Use a supported current Python version and install the requirements.

```text
python -m pip install -r requirements.txt
python main.py
```

### Windows 7

Qt 6 and current Python releases do not support Windows 7. Use 64 bit Python
3.8 and PySide2 5.15.2.1. The compatibility layer selects PySide2 when PySide6
is not installed. All custom screens use Qt 5 compatible APIs.

```text
py -3.8 -m pip install PySide2==5.15.2.1
py -3.8 main.py
```

The availability of Python 3.8 and PySide2 on a particular Windows 7 machine
still depends on its service pack, graphics driver and Microsoft runtime. Test
the source on a clean Windows 7 SP1 computer before final distribution.

## Unknown concentration methods

Interpolation records five standards and locates the unknown response between
neighbouring points on the log concentration scale. The three point method uses
two bracketing standards and one test response. The four point method uses S1,
S2, T1 and T2 with equal standard and test dose ratios. Four point responses
should remain in the approximately linear submaximal range and show reasonable
parallelism.

## Source only status

The source can be checked by running the model tests and the Qt offscreen smoke
test. Executable packaging should be done only after final source approval.
