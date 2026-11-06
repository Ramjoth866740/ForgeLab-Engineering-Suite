# ForgeLab — Streamlit Mechanical Engineering Suite

ForgeLab is an educational and preliminary design toolkit covering a broad set of undergraduate mechanical-engineering topics and introductory EV system calculations.

## Included domains

- **Strength of materials:** axial stress/strain, Young's modulus, material reference table/FOS, Mohr's circle, principal stress, thin-wall cylindrical pressure vessels, Goodman fatigue estimate.
- **Structural mechanics:** central point-load simply supported beam reactions, shear-force and bending-moment diagrams, elastic deflection, flexure stress and Euler column buckling.
- **Machine design:** circular shaft torsion, shaft power/torque, spur gear ratio/output and helical compression spring sizing.
- **Dynamics:** single-degree-of-freedom natural frequency, damping ratio and free-response plot.
- **Manufacturing:** turning spindle/feed/time/MRR, Chvorinov casting solidification estimate, sheet-metal blanking force and welding heat input.
- **Thermodynamics:** ideal-gas properties, closed-system First Law balance, air-standard Otto/Diesel/Brayton cycle estimates, enthalpy-based Rankine balance, Carnot efficiency and refrigeration/heat-pump COP.
- **Heat transfer:** plane-wall conduction, convection and thermal radiation.
- **Fluid mechanics:** pipe continuity, Reynolds number, laminar/turbulent Darcy-Weisbach head loss, pump power, continuity/Bernoulli and hydrostatics/buoyancy.
- **Aerodynamics:** dynamic pressure, drag, drag power and lift/downforce estimate with a conceptual wind-tunnel animation.
- **EV engineering:** battery series/parallel design, motor performance, reduction drive, road-load estimate, motor/battery matching and regenerative-braking energy.
- **Interactive visualizations:** battery pack, EV motion, pipe flow, aerodynamic wind tunnel, Otto cycle, Mohr circle, beam diagrams and vibration response.
- **Exports:** session history CSV and PDF.

## Important scope and validation limits

This is a **broad undergraduate toolkit**, not an exhaustive professional mechanical-engineering CAE suite. In particular, it does not provide a general-purpose 3D CAD system, finite-element solver, verified structural code design, turbulence-resolving CFD, detailed combustion chemistry, real-fluid/steam property database, full HVAC/refrigeration component model, rotor-bearing critical-speed analysis, or certified fatigue-life prediction. Animation canvases are educational representations; they do not solve the underlying Navier–Stokes equations or battery electrochemistry.

Many models are deliberately idealized. Check every formula's stated assumptions, units, material data, boundary conditions, component limits, safety factors, design standards and manufacturer datasheets before using results in an actual design. Material strengths in the built-in list are illustrative reference values, not certified allowables.

## Run locally

Use Python 3.12 (recommended for matching Streamlit Community Cloud's current default), then:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux/Termux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`).

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository for this project.
2. Upload the project files and folders, preserving the layout shown below. Do not upload secrets, private data or personal history databases.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/) and connect your GitHub account.
4. Choose **Create app**, select your repository and branch, and set the main file path to `streamlit_app.py`.
5. In Advanced settings, choose Python 3.12 if the version selector is shown, then deploy.
6. After deployment, test every module using representative inputs and inspect the app logs for errors.

Community Cloud installs packages from `requirements.txt` in the repository root. The entrypoint and dependency file are at the root of this project. See the official Streamlit docs linked below.

## Project structure

```text
forgelab_streamlit/
├── streamlit_app.py
├── engineering.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── tests/
    └── test_engineering.py
```

## Run calculation tests

```bash
python -m unittest discover -s tests -v
```

## Cloud data behavior

Calculation history is currently held in Streamlit session state and can be downloaded as CSV/PDF. Streamlit Community Cloud can restart an app and its local filesystem is not a durable database. For reliable cross-session history, connect a managed database (for example, PostgreSQL/Supabase) in a later iteration and store credentials in Streamlit secrets.

## Official deployment documentation

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
