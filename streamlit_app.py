from __future__ import annotations
import csv, io, json, math
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as pgo

import engineering as eng

st.set_page_config(page_title="ForgeLab | Mechanical Engineering Suite", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --------------------------- Theme and shared helpers ---------------------------
st.markdown("""
<style>
:root { color-scheme: dark; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at 8% 0%, #102a3d 0, #091522 34%, #07101b 75%); }
[data-testid="stHeader"] { background: rgba(3,12,21,.72); }

.block-container { padding-top: 1rem; max-width: 1450px; padding-left: clamp(1rem, 3vw, 2.5rem); padding-right: clamp(1rem, 3vw, 2.5rem); }
.hero-panel { padding: clamp(1.2rem, 4vw, 2.4rem); margin: .5rem 0 1.5rem; border: 1px solid #24516a; border-radius: 22px; background: linear-gradient(120deg,rgba(14,54,76,.96),rgba(9,22,37,.98) 65%,rgba(10,38,55,.96)); box-shadow: 0 18px 50px rgba(0,0,0,.18); }
.hero-kicker { color: #69dff6; letter-spacing: .16em; font-size: .72rem; font-weight: 700; }
.hero-title { color: #f1f7fb; font-size: clamp(2rem, 5vw, 3.6rem); line-height: 1.08; font-weight: 800; margin: .65rem 0; }
.hero-title span { color: #65dff6; }
.hero-copy { color: #a8c1d1; font-size: clamp(.95rem, 2vw, 1.12rem); max-width: 48rem; }
.module-group-title { color: #75dff3; font-size: .78rem; font-weight: 800; letter-spacing: .12em; margin: 1.5rem 0 .6rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: #21445a; background: linear-gradient(145deg,rgba(16,40,59,.82),rgba(8,22,35,.9)); border-radius: 14px; }
.stButton button { min-height: 2.7rem; font-weight: 650; }
@media (max-width: 640px) {
 .block-container { padding-top: .65rem; padding-left: .8rem; padding-right: .8rem; }
 .hero-panel { border-radius: 16px; padding: 1.15rem; margin-top: .2rem; }
 .hero-title { font-size: 2rem; }
 [data-testid="stMetric"] { padding: 9px; }
 [data-testid="stMetricLabel"] { font-size: .72rem; }
 [data-testid="stMetricValue"] { font-size: 1.15rem; }
 h1 { font-size: 1.65rem !important; } h2 { font-size: 1.35rem !important; } h3 { font-size: 1.1rem !important; }
}

[data-testid="stMetric"] { background: linear-gradient(145deg,#10283b,#0b1928); border: 1px solid #20506a; padding: 12px 14px; border-radius: 12px; }
[data-testid="stMetricValue"] { color: #75e5ff; }
.stButton button, .stDownloadButton button { border-radius: 9px; border: 1px solid #247b99; }
section[data-testid="stSidebar"] { background: #081522; border-right: 1px solid #1c4962; }
.formula-note { background: #0c2030; border-left: 3px solid #41d9f7; padding: 10px 14px; border-radius: 7px; }
.small-note { color: #9bb6c9; font-size: .86rem; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []


def record(module: str, summary: str, formulas: list[str]):
    entry = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "module": module,
             "summary": summary, "formulas": " | ".join(formulas)}
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:500]


def show_formula(formulas: list[str], assumptions: str | None = None):
    with st.expander("Governing formulas and assumptions", expanded=True):
        for f in formulas:
            st.latex(f)
        if assumptions:
            st.caption("Assumptions: " + assumptions)


def metrics(items: list[tuple[str, str]]):
    cols = st.columns(min(4, len(items)))
    for i, (label, value) in enumerate(items):
        with cols[i % len(cols)]:
            st.metric(label, value)


def result_panel(module: str, summary: str, formulas: list[str], metric_items=None, assumptions=None):
    st.success("Calculation completed")
    if metric_items:
        metrics(metric_items)
    with st.expander("Detailed result", expanded=True):
        st.code(summary, language="text")
    show_formula(formulas, assumptions)
    record(module, summary, formulas)


def help_text(text: str):
    st.caption(text)


def canvas_component(html: str, height: int = 390):
    components.html(html, height=height, scrolling=False)


def battery_animation(series: int, parallel: int, voltage: float, capacity: float, energy: float):
    data = json.dumps({"s": int(series), "p": int(parallel), "v": voltage, "ah": capacity, "kwh": energy})
    html = r'''<!doctype html><html><head><style>body{margin:0;background:#071522;color:#e8f7ff;font:14px system-ui}canvas{width:100%;height:320px;border:1px solid #1e536b;border-radius:12px;background:#081927}.caption{color:#8fb5c9;padding:7px}</style></head><body><canvas id="c" height="320"></canvas><div class="caption" id="cap"></div><script>
const D=__DATA__,c=document.getElementById('c'),x=c.getContext('2d');let t=0;function draw(){let w=c.clientWidth||700,h=320,d=window.devicePixelRatio||1;c.width=w*d;c.height=h*d;x.setTransform(d,0,0,d,0,0);x.fillStyle='#081927';x.fillRect(0,0,w,h);x.fillStyle='#dbf4ff';x.font='bold 15px system-ui';x.fillText('BATTERY PACK · '+D.s+'S '+D.p+'P',16,24);x.fillStyle='#91b3c5';x.font='12px system-ui';x.fillText('Series groups · cells inside each group are parallel-connected',16,43);let n=Math.min(D.s,48),cols=Math.min(6,n),rows=Math.ceil(n/cols),gap=8,left=16,top=58,tw=(w-32-gap*(cols-1))/cols,th=Math.min(48,(h-80-gap*(rows-1))/rows);for(let i=0;i<n;i++){let r=Math.floor(i/cols),q=i%cols,xx=left+q*(tw+gap),yy=top+r*(th+gap);x.fillStyle='#102f45';x.strokeStyle='#26718a';x.beginPath();x.roundRect(xx,yy,tw,th,7);x.fill();x.stroke();let visible=Math.min(D.p,5),cw=Math.max(5,Math.min(12,(tw-15-(visible-1)*3)/visible));for(let j=0;j<visible;j++){let cx=xx+7+j*(cw+3);x.fillStyle='#1684a5';x.beginPath();x.roundRect(cx,yy+7,cw,Math.max(9,th-22),3);x.fill();x.fillStyle='#a6f1ff';x.fillRect(cx+2,yy+10,Math.max(2,cw-4),2)}x.fillStyle='#d6f0f8';x.font='10px system-ui';x.fillText('S'+(i+1),xx+7,yy+th-5)}let pulse=(t*.03)%Math.max(1,n),idx=Math.floor(pulse),r=Math.floor(idx/cols),q=idx%cols,xx=left+q*(tw+gap),yy=top+r*(th+gap);x.strokeStyle='#ffcf70';x.lineWidth=3;x.beginPath();x.roundRect(xx-2,yy-2,tw+4,th+4,8);x.stroke();document.getElementById('cap').textContent='Pack: '+D.v.toFixed(1)+' V · '+D.ah.toFixed(1)+' Ah · '+D.kwh.toFixed(2)+' kWh · animated outline indicates conceptual current progression. Cells shown are schematic, not a physical pack design.';t++;requestAnimationFrame(draw)}draw();</script></body></html>'''.replace("__DATA__", data)
    canvas_component(html, 370)


def vehicle_animation(speed_kmh: float, force_n: float, power_kw: float, range_km: float):
    data = json.dumps({"speed": speed_kmh, "force": force_n, "power": power_kw, "range": range_km})
    html = r'''<!doctype html><html><head><style>body{margin:0;background:#071522;color:#eaf7ff;font:14px system-ui}canvas{width:100%;height:300px;border:1px solid #1e536b;border-radius:12px}button{background:#087da2;color:#fff;border:0;border-radius:7px;padding:7px 13px;margin:7px 6px 0 0}p{color:#9ab7ca}</style></head><body><canvas id="c" height="300"></canvas><button id="start">Start</button><button id="pause">Pause</button><button id="reset">Reset</button><p id="read"></p><script>
const D=__DATA__,c=document.getElementById('c'),x=c.getContext('2d');let t=0,run=false,dist=0;function frame(){let w=c.clientWidth||700,h=300,d=devicePixelRatio||1;c.width=w*d;c.height=h*d;x.setTransform(d,0,0,d,0,0);x.fillStyle='#081927';x.fillRect(0,0,w,h);let road=h*.72;x.fillStyle='#263a49';x.fillRect(0,road,w,h-road);x.strokeStyle='#b7d2df';x.setLineDash([25,18]);x.lineWidth=3;x.beginPath();x.moveTo(0,road+35);x.lineTo(w,road+35);x.stroke();x.setLineDash([]);let carX=w*.43,cy=road-35;x.save();x.translate(carX,cy);x.fillStyle='#0e779c';x.strokeStyle='#70eaff';x.lineWidth=3;x.beginPath();x.moveTo(-90,0);x.lineTo(-68,-28);x.quadraticCurveTo(-40,-54,5,-48);x.lineTo(55,-45);x.lineTo(84,-8);x.lineTo(94,0);x.closePath();x.fill();x.stroke();x.fillStyle='#9ad6e9';x.fillRect(-48,-36,43,18);x.fillRect(8,-38,36,20);for(let wx of [-55,58]){x.fillStyle='#050b12';x.beginPath();x.arc(wx,4,17,0,7);x.fill();x.strokeStyle='#8beaff';x.stroke();x.save();x.translate(wx,4);x.rotate(t*.07);for(let i=0;i<6;i++){x.rotate(Math.PI/3);x.beginPath();x.moveTo(0,0);x.lineTo(0,13);x.stroke()}x.restore()}x.restore();x.fillStyle='#d9f4ff';x.font='bold 14px system-ui';x.fillText('BATTERY',16,23);x.fillStyle='#14394d';x.fillRect(88,11,130,16);x.fillStyle='#5de0aa';x.fillRect(88,11,130*Math.max(0,1-dist/Math.max(D.range,1)),16);x.strokeStyle='#73eaff';x.strokeRect(88,11,130,16);x.fillStyle='#d7edf9';x.fillText('MOTOR → INVERTER → WHEELS',245,23);x.strokeStyle='#38dafa';x.lineWidth=4;x.beginPath();x.moveTo(250,38);x.lineTo(420,38);x.stroke();x.fillStyle='#91b6c9';x.font='12px system-ui';x.fillText('Conceptual level-road EV simulation visual · not a real-time vehicle dynamics solver',16,h-12);document.getElementById('read').textContent='Speed setting: '+D.speed.toFixed(1)+' km/h · tractive force estimate '+D.force.toFixed(0)+' N · motor demand '+D.power.toFixed(2)+' kW · illustrative range '+D.range.toFixed(1)+' km · animation distance '+dist.toFixed(2)+' km';if(run){t++;dist+=D.speed/3600/60;if(dist>=D.range)dist=0}requestAnimationFrame(frame)}document.getElementById('start').onclick=()=>run=true;document.getElementById('pause').onclick=()=>run=false;document.getElementById('reset').onclick=()=>{run=false;dist=0;t=0};frame();</script></body></html>'''.replace("__DATA__", data)
    canvas_component(html, 365)


def pipe_animation(diameter_ratio: float, velocity: float, reynolds: float):
    data = json.dumps({"ratio": diameter_ratio, "velocity": velocity, "re": reynolds})
    html = r'''<!doctype html><html><head><style>body{margin:0;background:#071522;color:#eaf7ff;font:13px system-ui}canvas{width:100%;height:270px;border:1px solid #1e536b;border-radius:12px}</style></head><body><canvas id="c" height="270"></canvas><script>const D=__DATA__,c=document.getElementById('c'),x=c.getContext('2d');let t=0;function draw(){let w=c.clientWidth||700,h=270,d=devicePixelRatio||1;c.width=w*d;c.height=h*d;x.setTransform(d,0,0,d,0,0);x.fillStyle='#081927';x.fillRect(0,0,w,h);let y=h/2,half1=65,half2=half1/Math.max(.25,D.ratio);x.strokeStyle='#5cdff7';x.lineWidth=3;x.beginPath();x.moveTo(0,y-half1);x.lineTo(w*.35,y-half1);x.lineTo(w*.65,y-half2);x.lineTo(w,y-half2);x.moveTo(0,y+half1);x.lineTo(w*.35,y+half1);x.lineTo(w*.65,y+half2);x.lineTo(w,y+half2);x.stroke();let factor=Math.max(.1,Math.min(3,D.velocity));for(let i=0;i<90;i++){let f=((i/90+t*(.002+factor*.003))%1),xx=f*w,local=xx<w*.35?half1:xx>w*.65?half2:half1+(half2-half1)*(xx-w*.35)/(w*.30);let yy=y+(Math.sin(i*12.9+t*.06))*local*.72;x.fillStyle='#a8efff';x.beginPath();x.arc(xx,yy,1.8,0,7);x.fill()}x.fillStyle='#d9f4ff';x.font='bold 14px system-ui';x.fillText('PIPE-FLOW VISUALIZATION',15,22);x.font='12px system-ui';x.fillText('Inlet velocity '+D.velocity.toFixed(2)+' m/s · Re '+D.re.toFixed(0),15,h-12);t++;requestAnimationFrame(draw)}draw();</script></body></html>'''.replace("__DATA__", data)
    canvas_component(html, 320)


def aero_animation(speed: float, cd: float):
    data = json.dumps({"speed": speed, "cd": cd})
    html = r'''<!doctype html><html><head><style>body{margin:0;background:#071522;color:#eaf7ff;font:13px system-ui}canvas{width:100%;height:280px;border:1px solid #1e536b;border-radius:12px}</style></head><body><canvas id="c" height="280"></canvas><script>const D=__DATA__,c=document.getElementById('c'),x=c.getContext('2d');let t=0;function draw(){let w=c.clientWidth||700,h=280,d=devicePixelRatio||1;c.width=w*d;c.height=h*d;x.setTransform(d,0,0,d,0,0);x.fillStyle='#081927';x.fillRect(0,0,w,h);let cx=w*.5,cy=h*.55,cw=Math.min(220,w*.35),wake=30+D.cd*110;x.strokeStyle='#267b99';x.lineWidth=1.3;for(let j=0;j<9;j++){let yy=22+j*28;x.beginPath();x.moveTo(0,yy);if(yy>cy-45&&yy<cy+45){let side=yy<cy?-1:1;x.bezierCurveTo(cx-70,yy,cx-45,cy+side*65,cx+30,cy+side*48);x.bezierCurveTo(cx+cw*.65,cy+side*45,cx+cw+20,yy,cx+cw+wake,yy+Math.sin(t*.04+j)*13)}else x.lineTo(w,yy);x.stroke()}x.save();x.translate(cx,cy);x.fillStyle='#12516b';x.strokeStyle='#75eaff';x.lineWidth=3;x.beginPath();x.moveTo(0,10);x.lineTo(28,-20);x.quadraticCurveTo(60,-45,115,-43);x.lineTo(170,-42);x.lineTo(cw,2);x.lineTo(cw,21);x.lineTo(0,21);x.closePath();x.fill();x.stroke();for(let wx of [48,cw-40]){x.fillStyle='#030a11';x.beginPath();x.arc(wx,22,15,0,7);x.fill();x.strokeStyle='#8beaff';x.stroke()}x.restore();for(let i=0;i<65;i++){let f=(i/65+t*(.003+D.speed/90000))%1,xx=f*w,yy=28+(i*39)%235;if(xx>cx-25&&xx<cx+cw+10&&yy>cy-55&&yy<cy+65)yy=cy+(yy<cy?-1:1)*62;x.fillStyle='#b4f7ff';x.beginPath();x.arc(xx,yy,1.7,0,7);x.fill()}x.fillStyle='#dff6ff';x.font='bold 14px system-ui';x.fillText('WIND TUNNEL · FLOW LEFT TO RIGHT',15,20);t++;requestAnimationFrame(draw)}draw();</script></body></html>'''.replace("__DATA__", data)
    canvas_component(html, 330)
# --------------------------- Sidebar and dashboard ---------------------------
PAGES = ["Dashboard", "Stress & materials", "Strength of materials advanced", "Beam & structural", "Shaft & machine design", "Machine design advanced", "Dynamics & vibration", "Manufacturing", "Unit converter", "Thermodynamics", "Thermodynamic cycles", "Heat transfer", "Fluid mechanics", "Fluid statics", "Aerodynamics", "EV battery designer", "EV drivetrain & motor", "EV vehicle simulator", "EV matching & regeneration", "History & reports"]
with st.sidebar:
    st.markdown("# ⚡ ForgeLab")
    st.caption("MECHANICAL ENGINEERING · EV SYSTEMS")
    search_query = st.text_input(
        "Search modules",
        placeholder="Search engineering modules...",
        key="module_search",
    ).strip().casefold()
    filtered_pages = [page for page in PAGES if search_query in page.casefold()]
    if filtered_pages:
        if st.session_state.get("module_navigation") not in filtered_pages:
            st.session_state.pop("module_navigation", None)
        current = st.radio(
            "Navigate modules",
            filtered_pages,
            label_visibility="collapsed",
            key="module_navigation",
        )
    else:
        current = "Dashboard"
        st.warning("No matching modules found.")
    st.divider()
    st.caption("Core undergraduate engineering calculators and conceptual simulations")
    st.caption("Cloud session history is temporary unless exported.")

st.title("⚡ ForgeLab Engineering Suite")
st.caption("Mechanical engineering fundamentals · machine design · thermal-fluid sciences · aerodynamics · electric vehicles")

if current == "Dashboard":
    st.markdown(
        """
        <div class="hero-panel">
          <div class="hero-kicker">ENGINEERING WORKSPACE · 2026</div>
          <div class="hero-title">Build. Calculate. <span>Innovate.</span></div>
          <div class="hero-copy">Your interactive workspace for mechanical engineering and electric vehicle systems.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metrics([("Engineering modules", "20"), ("Engineering domains", "10"), ("Visual simulations", "5"), ("Report exports", "CSV / PDF")])
    st.markdown("### Explore engineering modules")
    st.caption("Choose a workspace to open its calculators, visualizations and engineering tools.")
    dashboard_groups = [
        ("⚙️  MECHANICS & DESIGN", [
            ("Stress & materials", "Stress, strain, material properties and factor of safety."),
            ("Strength of materials advanced", "Principal stress, pressure vessels and fatigue."),
            ("Beam & structural", "Beam reactions, shear force, bending moment and deflection."),
            ("Shaft & machine design", "Shafts, gears and machine components."),
            ("Machine design advanced", "Advanced mechanical design calculations."),
            ("Dynamics & vibration", "Motion, forces and vibration analysis."),
        ]),
        ("🏭  MANUFACTURING & ENGINEERING TOOLS", [
            ("Manufacturing", "Manufacturing processes and production engineering."),
            ("Unit converter", "Convert common engineering units."),
            ("History & reports", "Review calculations and export reports."),
        ]),
        ("🌡️  THERMAL & FLUID SCIENCES", [
            ("Thermodynamics", "Thermodynamic properties and energy calculations."),
            ("Thermodynamic cycles", "Ideal gas power and refrigeration cycles."),
            ("Heat transfer", "Conduction, convection and thermal calculations."),
            ("Fluid mechanics", "Pipe flow, pumps and fluid energy."),
            ("Fluid statics", "Hydrostatic pressure and buoyancy."),
            ("Aerodynamics", "Vehicle drag, lift and airflow visualization."),
        ]),
        ("⚡  ELECTRIC VEHICLE SYSTEMS", [
            ("EV battery designer", "Configure a conceptual series-parallel battery pack."),
            ("EV drivetrain & motor", "Motor torque, power, gearing and wheel output."),
            ("EV vehicle simulator", "Explore simplified EV road-load behaviour."),
            ("EV matching & regeneration", "Match motor and battery, estimate energy recovery."),
        ]),
    ]
    for group_title, modules in dashboard_groups:
        st.markdown(f'<div class="module-group-title">{group_title}</div>', unsafe_allow_html=True)
        for start_index in range(0, len(modules), 2):
            cols = st.columns(2, gap="medium")
            for col, (module_name, description) in zip(cols, modules[start_index:start_index + 2]):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{module_name}**")
                        st.caption(description)
                        if st.button("Open workspace  →", key=f"dashboard_open_{module_name}", use_container_width=True):
                            st.session_state["module_navigation"] = module_name
                            st.rerun()
    st.info("ForgeLab is an educational and preliminary design toolkit. Validate calculations, assumptions, material data and applicable engineering standards before using results in a real design.")

elif current == "Stress & materials":
    st.subheader("Stress, strain, elasticity and material selection")
    tab1,tab2,tab3 = st.tabs(["Axial stress / strain", "Young's modulus", "Material factor of safety"])
    with tab1:
        with st.form("stress_form"):
            c1,c2=st.columns(2)
            F=c1.number_input("Axial force (N)",value=10000.0); A=c2.number_input("Area (mm²)",value=100.0,min_value=0.000001)
            L=c1.number_input("Original length (mm)",value=1000.0,min_value=0.000001); delta=c2.number_input("Extension (mm)",value=0.5)
            go=st.form_submit_button("Calculate stress and strain")
        if go:
            r=eng.stress_strain(F,A,L,delta); summary=f"Stress σ = F/A = {F:.3f}/{A:.3f} = {r['stress_mpa']:.4f} MPa\nStrain ε = ΔL/L = {delta:.4f}/{L:.4f} = {r['strain']:.7f}"
            result_panel("Axial stress / strain",summary,[r"\sigma=\frac{F}{A}",r"\varepsilon=\frac{\Delta L}{L_0}",r"1\ \mathrm{N/mm^2}=1\ \mathrm{MPa}"],[("Axial stress",f"{r['stress_mpa']:.3f} MPa"),("Normal strain",f"{r['strain']:.6f}")],"Uniform axial stress, small deformation and consistent N-mm units.")
            xs=[i/20*abs(F)*1.2 for i in range(21)]; ys=[x/A for x in xs]
            fig=pgo.Figure(pgo.Scatter(x=xs,y=ys,mode="lines",name="σ=F/A")); fig.update_layout(title="Linear stress vs force",xaxis_title="Force (N)",yaxis_title="Stress (MPa)",template="plotly_dark",height=330); st.plotly_chart(fig,use_container_width=True)
    with tab2:
        with st.form("young_form"):
            s=st.number_input("Normal stress (MPa)",value=200.0); e=st.number_input("Normal strain",value=.001,min_value=.000000001,format="%.8f")
            go=st.form_submit_button("Calculate Young's modulus")
        if go:
            r=eng.young_modulus(s,e); result_panel("Young's modulus",f"E = σ/ε = {s:.4f}/{e:.8f} = {r['E_mpa']:.3f} MPa = {r['E_gpa']:.5f} GPa",[r"E=\frac{\sigma}{\varepsilon}"],[("Young's modulus",f"{r['E_gpa']:.3f} GPa")],"Stress and strain must be measured in the linear-elastic region.")
    with tab3:
        refs={"Mild steel":250.0,"Aluminium 6061-T6":276.0,"Copper":70.0,"Titanium Grade 5":880.0}
        with st.form("fos_form"):
            mat=st.selectbox("Reference material",list(refs)); stress=st.number_input("Working stress (MPa)",value=100.0,min_value=.000001)
            go=st.form_submit_button("Calculate factor of safety")
        st.dataframe([{"Material":k,"Illustrative reference yield strength (MPa)":v} for k,v in refs.items()],use_container_width=True,hide_index=True)
        if go:
            fos=eng.factor_of_safety(refs[mat],stress); result_panel("Material factor of safety",f"Material: {mat}\nReference yield strength Sy = {refs[mat]:.1f} MPa\nWorking stress = {stress:.3f} MPa\nFOS = Sy/σworking = {fos:.4f}",[r"n=\frac{S_y}{\sigma_{\mathrm{working}}}"],[("Factor of safety",f"{fos:.3f}")],"Strengths are illustrative; exact grade, condition, fatigue, temperature, environment and applicable design code are not included.")

elif current == "Strength of materials advanced":
    st.subheader("Advanced strength of materials")
    tab1,tab2,tab3=st.tabs(["Mohr's circle / principal stress", "Thin-wall pressure vessel", "Fatigue · Modified Goodman"])
    with tab1:
        with st.form("mohr_form"):
            c1,c2=st.columns(2); sx=c1.number_input("Normal stress σx (MPa)",value=80.0); sy=c2.number_input("Normal stress σy (MPa)",value=20.0); tau=c1.number_input("Shear stress τxy (MPa)",value=30.0); go=st.form_submit_button("Calculate principal stresses")
        if go:
            r=eng.mohr_circle(sx,sy,tau); summary=f"Average normal stress = (σx+σy)/2 = {r['sigma_avg_mpa']:.3f} MPa\nPrincipal stress σ1 = {r['sigma1_mpa']:.3f} MPa\nPrincipal stress σ2 = {r['sigma2_mpa']:.3f} MPa\nMaximum in-plane shear = R = {r['tau_max_mpa']:.3f} MPa\nPrincipal plane angle θp = 0.5 atan2(2τxy, σx−σy) = {r['principal_angle_deg']:.3f}°"
            result_panel("Plane stress transformation",summary,[r"\sigma_{avg}=\frac{\sigma_x+\sigma_y}{2}",r"R=\sqrt{\left(\frac{\sigma_x-\sigma_y}{2}\right)^2+\tau_{xy}^2}",r"\sigma_{1,2}=\sigma_{avg}\pm R",r"\tau_{max,in-plane}=R",r"\theta_p=\frac12\tan^{-1}\left(\frac{2\tau_{xy}}{\sigma_x-\sigma_y}\right)"],[("σ1",f"{r['sigma1_mpa']:.2f} MPa"),("σ2",f"{r['sigma2_mpa']:.2f} MPa"),("Max in-plane shear",f"{r['tau_max_mpa']:.2f} MPa")],"Plane-stress state; angle convention depends on the sign convention and element rotation definition.")
            angles=[i*math.pi/180 for i in range(361)]; avg=r['sigma_avg_mpa']; rad=r['tau_max_mpa']; fig=pgo.Figure(pgo.Scatter(x=[avg+rad*math.cos(a) for a in angles],y=[rad*math.sin(a) for a in angles],mode="lines",name="Mohr circle")); fig.add_hline(y=0,line_color="white"); fig.add_vline(x=0,line_color="white"); fig.update_layout(template="plotly_dark",title="Mohr's circle",xaxis_title="Normal stress σ (MPa)",yaxis_title="Shear stress τ (MPa)",height=360); st.plotly_chart(fig,use_container_width=True)
    with tab2:
        with st.form("pressure_vessel_form"):
            c1,c2=st.columns(2); p=c1.number_input("Internal pressure (MPa)",value=2.0,min_value=0.0); d=c2.number_input("Internal diameter (mm)",value=500.0,min_value=.001); t=c1.number_input("Wall thickness (mm)",value=8.0,min_value=.001); go=st.form_submit_button("Calculate thin-wall stresses")
        if go:
            r=eng.thin_wall_cylinder(p,d,t); result_panel("Thin-wall cylindrical pressure vessel",f"Hoop stress σh=pd/(2t) = {r['hoop_mpa']:.3f} MPa\nLongitudinal stress σl=pd/(4t) = {r['longitudinal_mpa']:.3f} MPa",[r"\sigma_h=\frac{pD}{2t}",r"\sigma_l=\frac{pD}{4t}"],[("Hoop stress",f"{r['hoop_mpa']:.2f} MPa"),("Longitudinal stress",f"{r['longitudinal_mpa']:.2f} MPa")],"Thin-wall cylinder assumption t/D < 0.1. No code stress intensification, weld efficiency, corrosion allowance, fatigue, openings or end effects. Not a pressure-vessel certification design.")
    with tab3:
        with st.form("goodman_form"):
            c1,c2=st.columns(2); sm=c1.number_input("Mean stress σm (MPa)",value=60.0); sa=c2.number_input("Alternating stress σa (MPa)",value=80.0,min_value=0.0); se=c1.number_input("Corrected endurance limit Se (MPa)",value=250.0,min_value=.001); sut=c2.number_input("Ultimate tensile strength Sut (MPa)",value=600.0,min_value=.001); go=st.form_submit_button("Calculate Goodman fatigue factor")
        if go:
            n=eng.goodman_fos(sm,sa,se,sut); result_panel("Modified Goodman fatigue estimate",f"Goodman utilization = σa/Se + σm/Sut = {sa/se+sm/sut:.4f}\nFatigue factor of safety n = 1/utilization = {n:.3f}",[r"\frac{\sigma_a}{S_e}+\frac{\sigma_m}{S_{ut}}=\frac{1}{n}",r"n=\frac{1}{\sigma_a/S_e+\sigma_m/S_{ut}}"],[("Goodman fatigue FOS",f"{n:.3f}")],"Linear modified Goodman approximation for uniaxial normal stress. Endurance limit must already account for size, surface, reliability, temperature and other modifiers. Not a fatigue-life prediction.")

elif current == "Beam & structural":
    st.subheader("Beam analysis, flexure and column stability")
    tab1,tab2,tab3=st.tabs(["Simply supported beam", "Bending stress", "Euler column buckling"])
    with tab1:
        with st.form("beam_form"):
            c1,c2=st.columns(2); P=c1.number_input("Central point load P (N)",value=1000.0,min_value=0.0); L=c2.number_input("Span L (mm)",value=2000.0,min_value=.001); E=c1.number_input("Young's modulus E (MPa)",value=200000.0,min_value=.001); I=c2.number_input("Second moment I (mm⁴)",value=8000000.0,min_value=.001)
            go=st.form_submit_button("Analyse beam")
        if go:
            r=eng.beam_central_load(P,L,E,I); summary=f"RA=RB=P/2 = {r['RA_N']:.3f} N\nVmax=P/2 = {r['Vmax_N']:.3f} N\nMmax=PL/4 = {r['Mmax_Nmm']:.3f} N·mm\nδmax=PL³/(48EI) = {r['deflection_mm']:.6f} mm"
            result_panel("Simply supported beam",summary,[r"R_A=R_B=\frac{P}{2}",r"V_{\max}=\frac{P}{2}",r"M_{\max}=\frac{PL}{4}",r"\delta_{\max}=\frac{PL^3}{48EI}"],[("Maximum moment",f"{r['Mmax_Nmm']/1e6:.3f} kN·m"),("Midspan deflection",f"{r['deflection_mm']:.4f} mm")],"Prismatic, linearly elastic beam; simply supported; single central point load; small deflection.")
            f=pgo.Figure(); f.add_trace(pgo.Scatter(x=r['x_mm'],y=r['shear_N'],name="Shear force",line=dict(color="#55dcff"))); f.update_layout(template="plotly_dark",title="Shear force diagram",xaxis_title="Position x (mm)",yaxis_title="Shear (N)",height=280); st.plotly_chart(f,use_container_width=True)
            f2=pgo.Figure(); f2.add_trace(pgo.Scatter(x=r['x_mm'],y=r['moment_Nmm'],name="Bending moment",fill="tozeroy",line=dict(color="#ffbd69"))); f2.update_layout(template="plotly_dark",title="Bending moment diagram",xaxis_title="Position x (mm)",yaxis_title="Moment (N·mm)",height=280); st.plotly_chart(f2,use_container_width=True)
            f3=pgo.Figure(); f3.add_trace(pgo.Scatter(x=r['x_mm'],y=r['deflection_curve_mm'],name="Deflection",line=dict(color="#8ce6a8"))); f3.update_layout(template="plotly_dark",title="Elastic deflection curve (downward magnitude)",xaxis_title="Position x (mm)",yaxis_title="Deflection (mm)",height=280); st.plotly_chart(f3,use_container_width=True)
    with tab2:
        with st.form("bend_form"):
            M=st.number_input("Bending moment (N·mm)",value=500000.0); y=st.number_input("Distance from neutral axis (mm)",value=25.0,min_value=0.0); I=st.number_input("Second moment of area (mm⁴)",value=800000.0,min_value=.000001); go=st.form_submit_button("Calculate bending stress")
        if go:
            s=eng.bending_stress(M,y,I); result_panel("Bending stress",f"σ = My/I = {M:.2f}×{y:.3f}/{I:.3f} = {s:.4f} MPa",[r"\sigma=\frac{My}{I}"],[("Bending stress",f"{s:.3f} MPa")],"Linear-elastic Euler-Bernoulli beam theory; plane sections remain plane.")
    with tab3:
        with st.form("buckling_form"):
            c1,c2=st.columns(2); Ee=c1.number_input("E (MPa)",value=200000.0,min_value=.001); Ii=c2.number_input("Weak-axis I (mm⁴)",value=1.0e6,min_value=.001); Ll=c1.number_input("Actual length (mm)",value=2000.0,min_value=.001); K=c2.selectbox("Effective-length factor K",[0.5,0.7,1.0,2.0],index=2); go=st.form_submit_button("Calculate Euler critical load")
        if go:
            pc=eng.euler_buckling(Ee,Ii,Ll,K); result_panel("Euler column buckling",f"Effective length = KL = {K*Ll:.2f} mm\nPcr = π²EI/(KL)² = {pc:.2f} N",[r"P_{cr}=\frac{\pi^2EI}{(KL)^2}"],[("Euler critical load",f"{pc/1000:.3f} kN")],"Ideal slender, straight, prismatic column; elastic material; concentric axial load; end condition represented by K. Check slenderness and inelastic buckling separately.")

elif current == "Shaft & machine design":
    st.subheader("Shafts, torsion, power transmission and gears")
    tab1,tab2,tab3=st.tabs(["Shaft torsion", "Gear pair", "Power–torque relation"])
    with tab1:
        with st.form("torsion_form"):
            c1,c2=st.columns(2); T= c1.number_input("Torque (N·m)",value=250.0); radius=c2.number_input("Shaft outer radius (mm)",value=25.0,min_value=.001); J=c1.number_input("Polar second moment J (mm⁴)",value=2.0e6,min_value=.001); length=c2.number_input("Shaft length (mm)",value=1000.0,min_value=.001); G=c1.number_input("Shear modulus G (MPa)",value=80000.0,min_value=.001); go=st.form_submit_button("Calculate shaft torsion")
        if go:
            r=eng.torsion(T*1000,radius,J,length,G); result_panel("Shaft torsion",f"τmax=Tr/J = {r['tau_mpa']:.3f} MPa\nθ=TL/JG = {r['twist_rad']:.6f} rad = {r['twist_deg']:.4f}°",[r"\tau_{\max}=\frac{Tr}{J}",r"\theta=\frac{TL}{JG}"],[("Maximum shear stress",f"{r['tau_mpa']:.2f} MPa"),("Angle of twist",f"{r['twist_deg']:.3f}°")],"Circular shaft, elastic torsion, constant cross-section; torque converted from N·m to N·mm.")
    with tab2:
        with st.form("gear_form"):
            c1,c2=st.columns(2); rpm=c1.number_input("Input speed (RPM)",value=3000.0,min_value=.001); tq=c2.number_input("Input torque (N·m)",value=100.0); z1=c1.number_input("Driver teeth",value=20,min_value=1,step=1); z2=c2.number_input("Driven teeth",value=60,min_value=1,step=1); eta=c2.number_input("Mechanical efficiency (%)",value=97.0,min_value=.001,max_value=100.0); go=st.form_submit_button("Calculate gear output")
        if go:
            r=eng.gear_pair(rpm,tq,z1,z2,eta); result_panel("Gear pair",f"Gear ratio = Z2/Z1 = {r['ratio']:.3f}\nOutput speed = N1/ratio = {r['output_rpm']:.2f} RPM\nOutput torque = T1×ratio×η = {r['output_torque_nm']:.2f} N·m",[r"i=\frac{Z_2}{Z_1}=\frac{N_1}{N_2}",r"N_2=\frac{N_1}{i}",r"T_2=T_1i\eta"],[("Gear ratio",f"{r['ratio']:.2f}:1"),("Output speed",f"{r['output_rpm']:.0f} RPM"),("Output torque",f"{r['output_torque_nm']:.1f} N·m")],"Ideal external spur-gear ratio with user-specified overall efficiency; losses, tooth stress, backlash, lubrication and gear rating are not evaluated.")

    with tab3:
        with st.form("shaft_power_form"):
            c1,c2=st.columns(2); power= c1.number_input("Power (kW)",value=15.0,min_value=0.0); speed_rpm=c2.number_input("Shaft speed (RPM)",value=1500.0,min_value=.001); go=st.form_submit_button("Calculate shaft torque")
        if go:
            r=eng.shaft_power_torque(power,speed_rpm); result_panel("Shaft power and torque",f"P(kW)=T(N·m)×N(RPM)/9550\\nTorque T=9550P/N = 9550×{power:.3f}/{speed_rpm:.2f} = {r['torque_nm']:.3f} N·m",[r"P=T\omega",r"P_{kW}=\frac{TN}{9550}",r"T=\frac{9550P_{kW}}{N_{RPM}}"],[("Shaft torque",f"{r['torque_nm']:.2f} N·m")],"Steady rotational power; assumes torque and speed refer to the same shaft and does not include transmission losses.")

elif current == "Machine design advanced":
    st.subheader("Machine-element design: helical compression spring")
    with st.form("spring_form"):
        c1,c2=st.columns(2); F=c1.number_input("Axial spring load (N)",value=300.0,min_value=0.0); d=c2.number_input("Wire diameter d (mm)",value=5.0,min_value=.001); D=c1.number_input("Mean coil diameter D (mm)",value=30.0,min_value=.001); n=c2.number_input("Active coils",value=8.0,min_value=.1); G=c1.number_input("Shear modulus G (MPa)",value=79000.0,min_value=.001); go=st.form_submit_button("Calculate spring")
    if go:
        r=eng.helical_spring(F,d,D,n,G); result_panel("Helical compression spring",f"Spring index C=D/d = {r['spring_index']:.3f}\nWahl factor Kw = {r['wahl_factor']:.4f}\nMaximum corrected shear stress = {r['shear_stress_mpa']:.2f} MPa\nSpring rate k=Gd⁴/(8D³n) = {r['rate_n_mm']:.3f} N/mm\nDeflection δ=F/k = {r['deflection_mm']:.3f} mm",[r"C=\frac{D}{d}",r"K_w=\frac{4C-1}{4C-4}+\frac{0.615}{C}",r"\tau=K_w\frac{8FD}{\pi d^3}",r"k=\frac{Gd^4}{8D^3n}",r"\delta=\frac{F}{k}"],[("Spring rate",f"{r['rate_n_mm']:.2f} N/mm"),("Shear stress",f"{r['shear_stress_mpa']:.1f} MPa"),("Deflection",f"{r['deflection_mm']:.2f} mm")],"Close-coiled round-wire helical spring, static axial load. Check buckling, surge, fatigue, solid height, clash allowance, end design and material limits separately.")

elif current == "Dynamics & vibration":
    st.subheader("Single-degree-of-freedom vibration")
    with st.form("vib_form"):
        c1,c2=st.columns(2); m= c1.number_input("Mass (kg)",value=10.0,min_value=.001); k=c2.number_input("Stiffness (N/m)",value=20000.0,min_value=.001); c=c1.number_input("Viscous damping (N·s/m)",value=100.0,min_value=0.0); x0=c2.number_input("Initial displacement (mm)",value=10.0); go=st.form_submit_button("Calculate natural frequency")
    if go:
        r=eng.sdof_vibration(m,k,c); result_panel("SDOF vibration",f"Undamped natural frequency = {r['fn_hz']:.4f} Hz\nCritical damping coefficient = {r['critical_damping']:.3f} N·s/m\nDamping ratio ζ = {r['zeta']:.4f}\nDamped frequency = {r['damped_frequency_hz']:.4f} Hz",[r"\omega_n=\sqrt{\frac{k}{m}}",r"f_n=\frac{\omega_n}{2\pi}",r"c_c=2\sqrt{km}",r"\zeta=\frac{c}{c_c}",r"\omega_d=\omega_n\sqrt{1-\zeta^2}\quad (\zeta<1)"],[("Natural frequency",f"{r['fn_hz']:.3f} Hz"),("Damping ratio",f"{r['zeta']:.3f}")],"Linear viscously damped SDOF oscillator. Damped oscillation frequency applies only to the underdamped case.")
        if r['zeta']<1:
            tt=[i/100 for i in range(1001)]; z=r['zeta']; wn=r['wn_rad_s']; wd=r['wd_rad_s']; xinit=x0/1000
            decay=[xinit*math.exp(-z*wn*t)*math.cos(wd*t) for t in tt]
            fig=pgo.Figure(pgo.Scatter(x=tt,y=[v*1000 for v in decay],name="Free response")); fig.update_layout(template="plotly_dark",title="Underdamped free-vibration response",xaxis_title="Time (s)",yaxis_title="Displacement (mm)",height=330); st.plotly_chart(fig,use_container_width=True)
        else: st.info("The selected system is critically damped or overdamped; it does not oscillate in this free-response model.")

elif current == "Manufacturing":
    st.subheader("Manufacturing process calculations")
    tab1,tab2,tab3=st.tabs(["Turning / machining", "Casting solidification", "Sheet metal / welding"])
    with tab1:
        with st.form("machining_form"):
            c1,c2=st.columns(2); D=c1.number_input("Work diameter (mm)",value=50.0,min_value=.001); V=c2.number_input("Cutting speed (m/min)",value=120.0,min_value=.001); f=c1.number_input("Feed (mm/rev)",value=.2,min_value=.0001); d=c2.number_input("Depth of cut (mm)",value=2.0,min_value=.0001); L=c1.number_input("Machining length (mm)",value=100.0,min_value=.001); go=st.form_submit_button("Calculate machining parameters")
        if go:
            r=eng.machining(D,V,f,d,L); result_panel("Turning calculations",f"Spindle speed N=1000Vc/(πD) = {r['rpm']:.1f} RPM\nFeed rate = fN = {r['feed_rate_mm_min']:.2f} mm/min\nMachining time = L/(fN) = {r['time_min']:.3f} min\nMRR = πD f d N = {r['mrr_mm3_min']:.1f} mm³/min",[r"N=\frac{1000V_c}{\pi D}",r"V_f=fN",r"t_m=\frac{L}{fN}",r"MRR=\pi DfdN"],[("Spindle speed",f"{r['rpm']:.0f} RPM"),("Machining time",f"{r['time_min']:.2f} min"),("MRR",f"{r['mrr_mm3_min']:.0f} mm³/min")],"Turning operation with constant cutting speed, feed and depth of cut; tool approach, overtravel, tool changes and machine limits are ignored.")
    with tab2:
        st.write("Chvorinov's rule estimates casting solidification time from casting volume-to-surface-area ratio.")
        with st.form("casting_form"):
            C=st.number_input("Mould constant C (s/mm²)",value=.04,min_value=.0000001,format="%.6f"); n=st.number_input("Exponent n",value=2.0,min_value=.1); vol=st.number_input("Casting volume (mm³)",value=100000.0,min_value=.001); area=st.number_input("Cooling surface area (mm²)",value=30000.0,min_value=.001); go=st.form_submit_button("Estimate solidification time")
        if go:
            ratio=vol/area; ts=C*ratio**n; result_panel("Chvorinov solidification estimate",f"Modulus V/A = {ratio:.4f} mm\nSolidification time t = C(V/A)^n = {ts:.2f} s",[r"t_s=C\left(\frac{V}{A}\right)^n"],[("Estimated solidification time",f"{ts:.2f} s")],"Empirical rule; mould constant must be determined for the alloy, mould material, coating and process. Not a casting defect predictor.")

    with tab3:
        subt1,subt2=st.tabs(["Blanking / punching force", "Welding heat input"])
        with subt1:
            with st.form("blanking_form"):
                c1,c2=st.columns(2); th=c1.number_input("Sheet thickness (mm)",value=2.0,min_value=.001); per=c2.number_input("Cut perimeter (mm)",value=250.0,min_value=.001); shear=c1.number_input("Material shear strength (MPa)",value=250.0,min_value=.001); go=st.form_submit_button("Calculate cutting force")
            if go:
                force=eng.sheet_metal_blank_force(th,per,shear); result_panel("Sheet-metal blanking force",f"F=t×L×τs = {th:.3f}×{per:.2f}×{shear:.2f} = {force:.2f} N",[r"F_{cut}=tL\tau_s"],[("Ideal cutting force",f"{force/1000:.2f} kN")],"Idealized shear cutting; excludes clearance, tool geometry, friction, stripping force, press dynamics and material anisotropy.")
        with subt2:
            with st.form("weld_heat_form"):
                c1,c2=st.columns(2); volts=c1.number_input("Arc voltage (V)",value=24.0,min_value=.001); amps=c2.number_input("Welding current (A)",value=180.0,min_value=.001); travel=c1.number_input("Travel speed (mm/s)",value=5.0,min_value=.001); efficiency=c2.number_input("Process efficiency (fraction)",value=.8,min_value=.001,max_value=1.0); go=st.form_submit_button("Calculate heat input")
            if go:
                q=eng.welding_heat_input(volts,amps,travel,efficiency); result_panel("Welding heat input",f"Heat input H=ηVI/v = {q:.4f} kJ/mm",[r"H=\frac{\eta VI}{v}"],[("Heat input",f"{q:.3f} kJ/mm")],"Arc energy estimate; actual thermal cycle depends on process, joint, workpiece thickness, arc efficiency and heat losses.")

elif current == "Unit converter":
    st.subheader("Engineering unit converter")

    groups={"Length":{"mm":.001,"cm":.01,"m":1.0,"km":1000.0},"Force":{"N":1.0,"kN":1000.0},"Pressure":{"Pa":1.0,"kPa":1000.0,"MPa":1e6,"GPa":1e9,"bar":1e5},"Area":{"mm²":1e-6,"cm²":1e-4,"m²":1.0},"Power":{"W":1.0,"kW":1000.0},"Energy":{"J":1.0,"kJ":1000.0,"Wh":3600.0,"kWh":3.6e6},"Speed":{"m/s":1.0,"km/h":1/3.6},"Torque":{"N·m":1.0,"N·mm":.001}}
    with st.form("converter_form"):
        category=st.selectbox("Quantity",list(groups)); c1,c2=st.columns(2); value=c1.number_input("Value",value=1.0); source=c1.selectbox("From unit",list(groups[category])); target=c2.selectbox("To unit",list(groups[category])); go=st.form_submit_button("Convert units")
    if go:
        converted=value*groups[category][source]/groups[category][target]; formula=f"Converted value = input × factor(from) / factor(to) = {value:g} × {groups[category][source]:g} / {groups[category][target]:g} = {converted:.10g} {target}"
        result_panel("Engineering unit conversion",formula,[r"x_{target}=x_{source}\frac{f_{source}}{f_{target}}"],[("Converted value",f"{converted:.6g} {target}")],"Factors convert through SI base units; confirm dimensional compatibility and unit symbols.")

elif current == "Thermodynamics":
    st.subheader("Thermodynamics: properties, energy balance and cycles")
    tab1,tab2,tab3=st.tabs(["Ideal gas", "First Law", "Otto / Carnot cycles"])
    with tab1:
        with st.form("gas_form"):
            c1,c2=st.columns(2); m=c1.number_input("Gas mass (kg)",value=1.0,min_value=.000001); p=c2.number_input("Pressure (kPa)",value=100.0,min_value=.000001); V=c1.number_input("Volume (m³)",value=.8,min_value=.000001); T=c2.number_input("Temperature (K)",value=300.0,min_value=.000001); go=st.form_submit_button("Calculate ideal-gas properties")
        if go:
            r=eng.ideal_gas(m,p,V,T); result_panel("Ideal-gas properties",f"Density ρ=m/V = {r['density']:.4f} kg/m³\nSpecific gas constant R=pV/(mT) = {r['R_kj_kgk']:.5f} kJ/(kg·K)\nPressure check p=ρRT = {r['pressure_check_kpa']:.3f} kPa",[r"pV=mRT",r"\rho=\frac{m}{V}",r"R=\frac{pV}{mT}"],[("Density",f"{r['density']:.3f} kg/m³"),("Inferred R",f"{r['R_kj_kgk']:.4f} kJ/kg·K")],"Ideal gas; pressure in kPa, volume in m³, so kPa·m³ = kJ. No real-gas compressibility correction.")
    with tab2:
        with st.form("firstlaw_form"):
            c1,c2=st.columns(2); Q=c1.number_input("Heat into system Q (kJ)",value=500.0); W=c2.number_input("Work by system W (kJ)",value=120.0); dU=c1.number_input("Change in internal energy ΔU (kJ)",value=300.0); dKE=c2.number_input("Change in kinetic energy ΔKE (kJ)",value=0.0); dPE=c1.number_input("Change in potential energy ΔPE (kJ)",value=0.0); go=st.form_submit_button("Check energy balance")
        if go:
            r=eng.first_law_closed(Q,W,dU,dKE,dPE); result_panel("First Law closed-system energy balance",f"Left side Q−W = {r['Q_minus_W_kJ']:.3f} kJ\nRight side ΔU+ΔKE+ΔPE = {r['delta_total_energy_kJ']:.3f} kJ\nBalance residual = {r['residual_kJ']:.6f} kJ",[r"Q-W=\Delta U+\Delta KE+\Delta PE"],[("Energy balance residual",f"{r['residual_kJ']:.4f} kJ")],"Positive heat is into the system; positive work is done by the system. Residual near zero indicates consistency of supplied quantities.")
    with tab3:
        sub1,sub2=st.tabs(["Air-standard Otto cycle", "Carnot efficiency"])
        with sub1:
            with st.form("otto_form"):
                c1,c2=st.columns(2); rc=c1.number_input("Compression ratio r",value=8.0,min_value=1.01); t1=c2.number_input("Initial temperature T1 (K)",value=300.0,min_value=1.0); p1=c1.number_input("Initial pressure P1 (kPa)",value=100.0,min_value=.001); qin=c2.number_input("Heat added qin (kJ/kg)",value=800.0,min_value=.001); gamma=c1.number_input("Specific heat ratio γ",value=1.4,min_value=1.001); cv=c2.number_input("cv (kJ/kg·K)",value=eng.CV_AIR,min_value=.001,format="%.5f"); go=st.form_submit_button("Simulate Otto cycle")
            if go:
                r=eng.otto_cycle(rc,t1,p1,qin,gamma,cv); result_panel("Air-standard Otto cycle",f"T2={r['T2']:.2f} K · T3={r['T3']:.2f} K · T4={r['T4']:.2f} K\nP2={r['p2']:.2f} kPa · P3={r['p3']:.2f} kPa · P4={r['p4']:.2f} kPa\nHeat rejected qout={r['qout']:.2f} kJ/kg\nNet work={r['work']:.2f} kJ/kg\nThermal efficiency={100*r['efficiency']:.2f}%",[r"T_2=T_1r^{\gamma-1}",r"P_2=P_1r^\gamma",r"T_3=T_2+\frac{q_{in}}{c_v}",r"T_4=\frac{T_3}{r^{\gamma-1}}",r"\eta_{Otto}=1-\frac{q_{out}}{q_{in}}=1-\frac{1}{r^{\gamma-1}}"],[("Thermal efficiency",f"{100*r['efficiency']:.2f}%"),("Net work",f"{r['work']:.1f} kJ/kg")],"Air-standard ideal cycle with constant specific heats and isentropic compression/expansion. Real engine heat losses, pumping, friction, variable properties and combustion are not modelled.")
                fig=pgo.Figure(pgo.Scatter(x=r['v_cycle'],y=r['p_cycle'],mode="lines+markers",name="Otto cycle",line=dict(color="#57dcff",width=3))); fig.update_layout(template="plotly_dark",title="P–V diagram (relative specific volume) ",xaxis_title="Relative specific volume",yaxis_title="Pressure (kPa)",height=370); st.plotly_chart(fig,use_container_width=True)
                st.markdown("**Cycle animation / process sequence**")
                anim='''<!doctype html><html><body style="margin:0;background:#081927;color:#e7f5ff;font:14px system-ui"><canvas id="c" width="700" height="230" style="width:100%;height:230px"></canvas><script>let c=document.getElementById('c'),x=c.getContext('2d'),t=0;function d(){x.fillStyle='#081927';x.fillRect(0,0,700,230);let stage=Math.floor(t/90)%4;x.strokeStyle='#5ce4ff';x.lineWidth=4;x.strokeRect(80,28,130,160);let y=[105,150,55,90][stage];x.fillStyle='#19799b';x.fillRect(82,30,126,y);x.strokeStyle='#e5b96d';x.beginPath();x.moveTo(80,30+y);x.lineTo(210,30+y);x.stroke();let labels=['1–2 Isentropic compression','2–3 Constant-volume heat addition','3–4 Isentropic expansion','4–1 Constant-volume heat rejection'];x.fillStyle='white';x.font='bold 16px system-ui';x.fillText(labels[stage],250,90);x.font='13px system-ui';x.fillStyle='#9bb8c9';x.fillText('Animated conceptual piston position · ideal air-standard Otto cycle',250,120);t++;requestAnimationFrame(d)}d()</script></body></html>'''
                canvas_component(anim,245)
        with sub2:
            with st.form("carnot_form"):
                hot=st.number_input("Hot reservoir temperature (K)",value=800.0,min_value=.001); cold=st.number_input("Cold reservoir temperature (K)",value=300.0,min_value=.001); go=st.form_submit_button("Calculate Carnot efficiency")
            if go:
                eta=eng.carnot_efficiency(hot,cold); result_panel("Carnot efficiency",f"ηmax = 1−Tc/Th = 1−{cold:.2f}/{hot:.2f} = {eta*100:.3f}%",[r"\eta_{Carnot}=1-\frac{T_C}{T_H}"],[("Maximum theoretical efficiency",f"{eta*100:.2f}%")],"Absolute temperatures in kelvin; reversible engine between two thermal reservoirs.")

elif current == "Thermodynamic cycles":
    st.subheader("Power and refrigeration cycles")
    tab1,tab2,tab3,tab4=st.tabs(["Diesel cycle", "Brayton cycle", "Rankine cycle", "Refrigeration / heat pump"])
    with tab1:
        with st.form("diesel_form"):
            c1,c2=st.columns(2); rcomp=c1.number_input("Compression ratio r",value=18.0,min_value=1.01); rcut=c2.number_input("Cut-off ratio rc",value=2.0,min_value=1.001); t1=c1.number_input("Initial T1 (K)",value=300.0,min_value=1.0); p1=c2.number_input("Initial P1 (kPa)",value=100.0,min_value=.001); go=st.form_submit_button("Calculate Diesel cycle")
        if go:
            r=eng.diesel_cycle(rcomp,rcut,t1,p1); result_panel("Air-standard Diesel cycle",f"T2={r['T2']:.2f} K · T3={r['T3']:.2f} K · T4={r['T4']:.2f} K\nqin=cp(T3−T2) = {r['qin']:.2f} kJ/kg\nqout=cv(T4−T1) = {r['qout']:.2f} kJ/kg\nNet work = {r['work']:.2f} kJ/kg\nEfficiency = {100*r['efficiency']:.2f}%",[r"T_2=T_1r^{\gamma-1}",r"T_3=T_2r_c",r"T_4=\frac{T_3}{(r/r_c)^{\gamma-1}}",r"\eta_D=1-\frac{q_{out}}{q_{in}}"],[("Diesel efficiency",f"{100*r['efficiency']:.2f}%"),("Net work",f"{r['work']:.1f} kJ/kg")],"Air-standard ideal Diesel cycle with constant specific heats; no combustion duration, heat loss, friction, pumping or variable-property model.")
    with tab2:
        with st.form("brayton_form"):
            c1,c2=st.columns(2); rp=c1.number_input("Compressor pressure ratio",value=8.0,min_value=1.001); T1=c2.number_input("Compressor inlet T1 (K)",value=300.0,min_value=1.0); T3=c1.number_input("Turbine inlet T3 (K)",value=1200.0,min_value=1.0); go=st.form_submit_button("Calculate Brayton cycle")
        if go:
            r=eng.brayton_cycle(rp,T1,T3); result_panel("Ideal Brayton cycle",f"Compressor outlet T2={r['T2']:.2f} K\nTurbine outlet T4={r['T4']:.2f} K\nCompressor work={r['compressor_work']:.2f} kJ/kg\nTurbine work={r['turbine_work']:.2f} kJ/kg\nNet work={r['net_work']:.2f} kJ/kg\nThermal efficiency={100*r['efficiency']:.2f}%",[r"T_2=T_1r_p^{(\gamma-1)/\gamma}",r"T_4=\frac{T_3}{r_p^{(\gamma-1)/\gamma}}",r"W_c=c_p(T_2-T_1)",r"W_t=c_p(T_3-T_4)",r"\eta=\frac{W_t-W_c}{q_{in}}"],[("Brayton efficiency",f"{100*r['efficiency']:.2f}%"),("Net work",f"{r['net_work']:.1f} kJ/kg")],"Ideal simple gas-turbine cycle; isentropic compressor/turbine and constant specific heat. No pressure losses, regeneration, intercooling or reheating.")
    with tab3:
        st.caption("Enter specific enthalpies from a trusted steam table or property package. No built-in steam-property database is claimed.")
        with st.form("rankine_form"):
            c1,c2=st.columns(2); h1=c1.number_input("Pump inlet h1 (kJ/kg)",value=191.8); h2=c2.number_input("Pump outlet h2 (kJ/kg)",value=192.0); h3=c1.number_input("Boiler outlet h3 (kJ/kg)",value=3230.0); h4=c2.number_input("Turbine outlet h4 (kJ/kg)",value=2200.0); go=st.form_submit_button("Calculate Rankine energy balance")
        if go:
            r=eng.rankine_cycle(h1,h2,h3,h4); result_panel("Simple Rankine cycle energy balance",f"Pump work = h2−h1 = {r['pump_work']:.2f} kJ/kg\nTurbine work = h3−h4 = {r['turbine_work']:.2f} kJ/kg\nBoiler heat input = h3−h2 = {r['qin']:.2f} kJ/kg\nNet work = turbine work−pump work = {r['net_work']:.2f} kJ/kg\nThermal efficiency = Wnet/Qin = {100*r['efficiency']:.2f}%",[r"w_p=h_2-h_1",r"w_t=h_3-h_4",r"q_{in}=h_3-h_2",r"w_{net}=w_t-w_p",r"\eta_{th}=\frac{w_{net}}{q_{in}}"],[("Net work",f"{r['net_work']:.1f} kJ/kg"),("Thermal efficiency",f"{100*r['efficiency']:.2f}%")],"Idealized four-state enthalpy balance. State enthalpies must be obtained externally at the actual pressures/temperatures; turbine moisture, pump efficiency and pressure drops are not solved.")
    with tab4:
        with st.form("refrigeration_form"):
            c1,c2=st.columns(2); ql=c1.number_input("Cooling capacity QL (kW)",value=10.0,min_value=.001); power=c2.number_input("Compressor input power (kW)",value=2.5,min_value=.001); go=st.form_submit_button("Calculate refrigeration COP")
        if go:
            r=eng.refrigeration_cop(ql,power); result_panel("Refrigeration / heat pump",f"Refrigerator COP = QL/Win = {r['cop']:.3f}\nHeat rejected QH=QL+Win = {r['heat_rejected_kw']:.2f} kW\nHeat-pump COP = QH/Win = {r['heat_pump_cop']:.3f}",[r"COP_R=\frac{Q_L}{W_{in}}",r"Q_H=Q_L+W_{in}",r"COP_{HP}=\frac{Q_H}{W_{in}}=COP_R+1"],[("Refrigerator COP",f"{r['cop']:.2f}"),("Heat-pump COP",f"{r['heat_pump_cop']:.2f}")],"Steady energy balance around the refrigeration device; no refrigerant property states, compressor map, pressure drops or heat-exchanger sizing.")

elif current == "Heat transfer":
    st.subheader("Conduction and convection")
    with st.form("heat_form"):
        c1,c2=st.columns(2); k= c1.number_input("Thermal conductivity k (W/m·K)",value=45.0,min_value=.000001); A=c2.number_input("Area (m²)",value=.5,min_value=.000001); dT=c1.number_input("Temperature difference ΔT (K)",value=80.0); L=c2.number_input("Wall thickness (m)",value=.02,min_value=.000001); h=c1.number_input("Convection coefficient h (W/m²·K)",value=25.0,min_value=.000001); go=st.form_submit_button("Calculate heat-transfer rates")
    if go:
        r=eng.heat_transfer(k,A,dT,L,h); result_panel("Conduction and convection",f"Conduction rate Qdot=kAΔT/L = {r['conduction_w']:.2f} W\nConvection rate Qdot=hAΔT = {r['convection_w']:.2f} W",[r"\dot Q_{cond}=\frac{kA(T_1-T_2)}{L}",r"\dot Q_{conv}=hA(T_s-T_\infty)"],[("Conduction",f"{r['conduction_w']:.1f} W"),("Convection",f"{r['convection_w']:.1f} W")],"Steady one-dimensional plane-wall conduction and Newton's law of cooling; constant properties and uniform temperature difference. The two rates are separate modes, not added in series automatically.")

    st.markdown("### Thermal radiation")
    with st.form("radiation_form"):
        c1,c2=st.columns(2); eps=c1.number_input("Surface emissivity (0–1)",value=.85,min_value=0.0,max_value=1.0); ar=c2.number_input("Radiating area (m²)",value=1.0,min_value=.000001); ts=c1.number_input("Surface temperature (K)",value=500.0,min_value=.001); tr=c2.number_input("Surrounding temperature (K)",value=300.0,min_value=.001); go=st.form_submit_button("Calculate radiative heat transfer")
    if go:
        q=eng.radiation_heat(eps,ar,ts,tr); result_panel("Thermal radiation",f"Net radiative heat rate = εσA(Ts⁴−Tsur⁴) = {q:.2f} W",[r"\dot Q_{rad}=\varepsilon\sigma A(T_s^4-T_{sur}^4)",r"\sigma=5.670374419\times10^{-8}\ \mathrm{W/(m^2K^4)}"],[("Net radiation",f"{q:.2f} W")],"Large isothermal diffuse-gray surface with effective surroundings and view factor approximated as 1; shielding and participating media are not modelled.")

elif current == "Fluid mechanics":
    st.subheader("Pipe flow, Reynolds number, head loss and pump sizing")
    tab1,tab2,tab3=st.tabs(["Pipe-flow calculator", "Pump power", "Continuity / Bernoulli"])
    with tab1:
        with st.form("pipe_form"):
            c1,c2=st.columns(2); D=c1.number_input("Pipe inside diameter (m)",value=.05,min_value=.00001,format="%.4f"); Q=c2.number_input("Volume flow rate (m³/s)",value=.002,min_value=0.0,format="%.5f"); rho=c1.number_input("Density (kg/m³)",value=998.0,min_value=.00001); mu=c2.number_input("Dynamic viscosity (Pa·s)",value=.001,min_value=.00000001,format="%.6f"); L=c1.number_input("Pipe length (m)",value=20.0,min_value=.0001); eps=c2.number_input("Absolute roughness (m)",value=.000045,min_value=0.0,format="%.6f"); go=st.form_submit_button("Calculate pipe flow")
        if go:
            r=eng.pipe_flow(D,Q,rho,mu,L,eps); hf="Transitional range: use a suitable correlation or measured data" if r['head_loss_m'] is None else f"{r['head_loss_m']:.4f} m"; dp="not estimated in transitional range" if r['pressure_drop_pa'] is None else f"{r['pressure_drop_pa']/1000:.3f} kPa"
            summary=f"Area A=πD²/4 = {r['area_m2']:.6f} m²\nMean velocity V=Q/A = {r['velocity_m_s']:.4f} m/s\nReynolds number Re=ρVD/μ = {r['reynolds']:.1f} ({r['regime']})\nDarcy friction factor f = {r['friction_factor'] if r['friction_factor'] is not None else 'not assigned'}\nDarcy-Weisbach head loss hf=f(L/D)V²/(2g) = {hf}\nPressure drop Δp=ρghf = {dp}"
            result_panel("Pipe flow",summary,[r"A=\frac{\pi D^2}{4}",r"V=\frac{Q}{A}",r"Re=\frac{\rho VD}{\mu}",r"h_f=f\frac{L}{D}\frac{V^2}{2g}",r"\Delta p=\rho g h_f"],[("Mean velocity",f"{r['velocity_m_s']:.3f} m/s"),("Reynolds number",f"{r['reynolds']:.0f}"),("Flow regime",r['regime'])],"Steady incompressible fully developed circular-pipe flow. Laminar friction factor f=64/Re; turbulent friction factor uses Swamee–Jain. Transitional flow (Re 2300–4000) is flagged. Minor losses and elevation changes are not included.")
            pipe_animation(D/D*.65 if D else 1,r['velocity_m_s'],r['reynolds'])
    with tab2:
        with st.form("pump_form"):
            c1,c2=st.columns(2); q=c1.number_input("Flow rate (m³/s)",value=.01,min_value=.000001); head=c2.number_input("Pump head (m)",value=25.0,min_value=0.0); density=c1.number_input("Fluid density (kg/m³)",value=1000.0,min_value=.00001); eta=c2.number_input("Pump efficiency (%)",value=75.0,min_value=.001,max_value=100.0); go=st.form_submit_button("Calculate pump power")
        if go:
            r=eng.pump_power(q,head,density,eta); result_panel("Pump power",f"Hydraulic power = ρgQH = {r['hydraulic_w']:.2f} W\nRequired shaft input = Phyd/η = {r['shaft_w']:.2f} W",[r"P_h=\rho gQH",r"P_{shaft}=\frac{P_h}{\eta}"],[("Hydraulic power",f"{r['hydraulic_w']/1000:.3f} kW"),("Shaft input",f"{r['shaft_w']/1000:.3f} kW")],"Steady incompressible fluid; specified total pump head; efficiency entered as a fraction of 100%.")

    with tab3:
        with st.form("bernoulli_form"):
            c1,c2=st.columns(2); d1=c1.number_input("Inlet diameter D1 (m)",value=.08,min_value=.0001); d2=c2.number_input("Outlet diameter D2 (m)",value=.04,min_value=.0001); flow=c1.number_input("Volume flow rate Q (m³/s)",value=.005,min_value=0.0); p1=c2.number_input("Inlet pressure P1 (Pa)",value=200000.0); z1=c1.number_input("Inlet elevation z1 (m)",value=0.0); z2=c2.number_input("Outlet elevation z2 (m)",value=0.0); rh=c1.number_input("Fluid density (kg/m³)",value=1000.0,min_value=.0001); go=st.form_submit_button("Solve Bernoulli between sections")
        if go:
            r=eng.bernoulli_two_sections(d1,d2,flow,p1,z1,z2,rh); result_panel("Continuity and Bernoulli",f"A1=πD1²/4 = {r['a1']:.6f} m² · A2=πD2²/4 = {r['a2']:.6f} m²\nV1=Q/A1 = {r['v1']:.3f} m/s · V2=Q/A2 = {r['v2']:.3f} m/s\nP2 = P1 + ½ρ(V1²−V2²) + ρg(z1−z2) = {r['p2_pa']:.2f} Pa",[r"Q=A_1V_1=A_2V_2",r"\frac{P_1}{\rho g}+\frac{V_1^2}{2g}+z_1=\frac{P_2}{\rho g}+\frac{V_2^2}{2g}+z_2"],[("Outlet velocity",f"{r['v2']:.3f} m/s"),("Outlet pressure",f"{r['p2_pa']/1000:.2f} kPa")],"Steady incompressible, inviscid one-dimensional flow; no friction or minor losses. If P2 is negative gauge/absolute depending on P1 reference, inspect the chosen pressure basis.")

elif current == "Fluid statics":
    st.subheader("Hydrostatics and buoyancy")
    tab1,tab2=st.tabs(["Hydrostatic pressure", "Buoyancy"])
    with tab1:
        with st.form("hydro_form"):
            rho=st.number_input("Fluid density (kg/m³)",value=1000.0,min_value=.0001); depth=st.number_input("Depth below free surface (m)",value=5.0,min_value=0.0); area=st.number_input("Submerged plane area (m²)",value=1.0,min_value=.0001); go=st.form_submit_button("Calculate hydrostatic load")
        if go:
            p=eng.hydrostatic_pressure(rho,depth); force=p*area; result_panel("Hydrostatic pressure and plane force",f"Gauge pressure p=ρgh = {p:.2f} Pa = {p/1000:.3f} kPa\nUniform-depth force estimate F=pA = {force:.2f} N",[r"p=\rho gh",r"F=pA"],[("Gauge pressure",f"{p/1000:.3f} kPa"),("Plane force estimate",f"{force:.1f} N")],"Static incompressible fluid of uniform density; pressure is gauge pressure at the specified depth. Plane-area force estimate assumes that depth is uniform over the area.")
    with tab2:
        with st.form("buoyancy_form"):
            rho_f=st.number_input("Fluid density (kg/m³)",value=1000.0,min_value=.0001); volume=st.number_input("Displaced fluid volume (m³)",value=.02,min_value=.000001); mass=st.number_input("Object mass (kg)",value=15.0,min_value=0.0); go=st.form_submit_button("Calculate buoyancy")
        if go:
            fb=rho_f*eng.G*volume; weight=mass*eng.G; net=fb-weight; result_panel("Archimedes buoyancy",f"Buoyant force Fb=ρfluid g Vdisplaced = {fb:.2f} N\nWeight W=mg = {weight:.2f} N\nNet vertical force (up positive)=Fb−W = {net:.2f} N\nResult: {'rises' if net>0 else 'sinks' if net<0 else 'neutral equilibrium'} tendency",[r"F_b=\rho_f gV_{displaced}",r"W=mg",r"F_{net}=F_b-W"],[("Buoyant force",f"{fb:.2f} N"),("Net force",f"{net:.2f} N")],"Fully displaced volume as entered; stability, partial immersion, fluid stratification and surface effects are not modelled.")

elif current == "Aerodynamics":
    st.subheader("Vehicle aerodynamics and wind tunnel")
        with st.form("aero_form"):
        c1,c2=st.columns(2); v= c1.number_input("Vehicle speed (km/h)",value=100.0,min_value=0.0); rho=c2.number_input("Air density (kg/m³)",value=1.225,min_value=.00001); cd=c1.number_input("Drag coefficient Cd",value=.29,min_value=0.0); A=c2.number_input("Frontal area (m²)",value=2.2,min_value=.00001); cl=c1.number_input("Lift coefficient Cl (+ lift / − downforce)",value=-.1); go=st.form_submit_button("Calculate aerodynamic loads")
    if go:
        r=eng.aerodynamics(v,rho,cd,A,cl); result_panel("Aerodynamic load estimate",f"Speed V={v:.2f}/3.6 = {r['speed_m_s']:.3f} m/s\nDynamic pressure q=½ρV² = {r['dynamic_pressure_pa']:.2f} Pa\nDrag D=qCdA = {r['drag_n']:.2f} N\nPower Pdrag=DV = {r['drag_power_kw']:.3f} kW\nLift L=qClA = {r['lift_n']:.2f} N",[r"q=\frac12\rho V^2",r"D=\frac12\rho V^2C_DA",r"P_D=DV",r"L=\frac12\rho V^2C_LA"],[("Aerodynamic drag",f"{r['drag_n']:.1f} N"),("Drag power",f"{r['drag_power_kw']:.2f} kW"),("Lift (signed)",f"{r['lift_n']:.1f} N")],"Steady incompressible external-flow estimate with fixed coefficients; no yaw, ground effect, rotating wheels, ride-height or local pressure distribution. Coefficients require validated source data or tests.")
    aero_animation(v,cd)

elif current == "EV battery designer":
    st.subheader("EV battery pack designer")
    with st.form("battery_form"):
        c1,c2=st.columns(2); cv=c1.number_input("Cell nominal voltage (V)",value=3.6,min_value=.1); ca=c2.number_input("Cell capacity (Ah)",value=5.0,min_value=.01); ns=c1.number_input("Cells in series Ns",value=108,min_value=1,step=1); np_=c2.number_input("Cells in parallel Np",value=20,min_value=1,step=1); usable=c1.number_input("Usable energy (%)",value=90.0,min_value=1.0,max_value=100.0); whkm=c2.number_input("Energy consumption (Wh/km)",value=150.0,min_value=.1); go=st.form_submit_button("Design battery pack")
    if go:
        r=eng.ev_battery(cv,ca,int(ns),int(np_),usable,whkm); result_panel("EV battery pack",f"Total cells = Ns×Np = {r['cells']}\nNominal voltage Vpack=Ns×Vcell = {r['voltage_v']:.2f} V\nCapacity Ahpack=Np×Ahcell = {r['capacity_ah']:.2f} Ah\nNominal energy E=V×Ah/1000 = {r['energy_kwh']:.2f} kWh\nUsable energy = E×usable fraction = {r['usable_kwh']:.2f} kWh\nEstimated range = Eusable×1000/(Wh/km) = {r['range_km']:.1f} km",[r"N_{cells}=N_sN_p",r"V_{pack}=N_sV_{cell}",r"Ah_{pack}=N_pAh_{cell}",r"E_{kWh}=\frac{V_{pack}Ah_{pack}}{1000}",r"Range=\frac{E_{usable}\times1000}{Wh/km}"],[("Pack voltage",f"{r['voltage_v']:.1f} V"),("Nominal energy",f"{r['energy_kwh']:.2f} kWh"),("Estimated range",f"{r['range_km']:.0f} km")],"Nominal cell values; ideal series/parallel arithmetic. Does not size busbars, fuses, contactors, cooling, BMS, cell balancing, voltage sag, thermal propagation or crash protection.")
        battery_animation(int(ns),int(np_),r['voltage_v'],r['capacity_ah'],r['energy_kwh'])

elif current == "EV drivetrain & motor":
    st.subheader("EV motor performance, gearing and drivetrain")
    tab1,tab2=st.tabs(["Motor power and torque", "Drivetrain output"])
    with tab1:
        with st.form("motor_form"):
            c1,c2=st.columns(2); tq=c1.number_input("Motor torque (N·m)",value=200.0,min_value=0.0); rpm=c2.number_input("Motor speed (RPM)",value=3000.0,min_value=.001); pin=c1.number_input("Electrical input power (kW)",value=70.0,min_value=.001); go=st.form_submit_button("Calculate motor performance")
        if go:
            p=2*math.pi*rpm*tq/60/1000; eff=p/pin*100
            result_panel("EV motor performance",f"Mechanical output P=Tω=2πNT/60 = {p:.3f} kW\nElectrical input power = {pin:.3f} kW\nEstimated efficiency = Pout/Pin×100 = {eff:.2f}%",[r"P=T\omega",r"\omega=\frac{2\pi N}{60}",r"P_{kW}=\frac{T_{Nm}N_{RPM}}{9550}",r"\eta=\frac{P_{out}}{P_{in}}\times100\%"],[("Mechanical power",f"{p:.2f} kW"),("Efficiency",f"{eff:.1f}%")],"Steady operating point. If efficiency exceeds 100%, review inputs. Motor torque-speed limits, field weakening, inverter current and thermal derating are not modelled.")
            speeds=[i*max(rpm*1.5,1000)/100 for i in range(101)]; torques=[tq if n<=rpm else tq*rpm/max(n,1) for n in speeds]; powers=[tt*nn/9550 for tt,nn in zip(torques,speeds)]; fig=pgo.Figure(); fig.add_trace(pgo.Scatter(x=speeds,y=torques,name="Torque (N·m)")); fig.add_trace(pgo.Scatter(x=speeds,y=powers,name="Power (kW)",yaxis="y2")); fig.update_layout(template="plotly_dark",title="Illustrative torque–speed and power curve",xaxis_title="Speed (RPM)",yaxis=dict(title="Torque (N·m)"),yaxis2=dict(title="Power (kW)",overlaying="y",side="right"),height=360); st.plotly_chart(fig,use_container_width=True); help_text("Illustrative constant-torque then constant-power curve, not a manufacturer motor map.")
    with tab2:
        with st.form("drive_form"):
            c1,c2=st.columns(2); tm=c1.number_input("Motor torque (N·m)",value=200.0); nm=c2.number_input("Motor RPM",value=3000.0,min_value=.001); ratio=c1.number_input("Reduction ratio",value=9.0,min_value=.001); eta=c2.number_input("Drivetrain efficiency (%)",value=95.0,min_value=.001,max_value=100.0); radius=c1.number_input("Tyre rolling radius (m)",value=.3,min_value=.001); go=st.form_submit_button("Calculate wheel output")
        if go:
            tw=tm*ratio*eta/100; nw=nm/ratio; speed=nw*2*math.pi*radius*60/1000; force=tw/radius
            result_panel("EV drivetrain",f"Wheel torque Tw=Tm×i×η = {tw:.2f} N·m\nWheel speed Nw=Nm/i = {nw:.2f} RPM\nVehicle speed=2πNwr×60/1000 = {speed:.2f} km/h\nTractive force=Tw/r = {force:.2f} N",[r"T_w=T_mi\eta",r"N_w=\frac{N_m}{i}",r"v=\frac{2\pi N_wr}{60}",r"F_t=\frac{T_w}{r}"],[("Wheel torque",f"{tw:.1f} N·m"),("Vehicle speed",f"{speed:.1f} km/h"),("Tractive force",f"{force:.0f} N")],"Single fixed reduction gear, no tyre slip, constant effective tyre radius; gear and tyre limits not checked.")

elif current == "EV vehicle simulator":
    st.subheader("Simplified EV longitudinal simulator")
    with st.form("evsim_form"):
        c1,c2=st.columns(2); mass=c1.number_input("Vehicle mass (kg)",value=1500.0,min_value=.1); speed=c2.number_input("Target speed (km/h)",value=60.0,min_value=0.0); accel=c1.number_input("Acceleration (m/s²)",value=.5); grade=c2.number_input("Road gradient (%)",value=0.0); crr=c1.number_input("Rolling resistance coefficient",value=.012,min_value=0.0); cd=c2.number_input("Drag coefficient Cd",value=.29,min_value=0.0); area=c1.number_input("Frontal area (m²)",value=2.2,min_value=.0001); rho=c2.number_input("Air density (kg/m³)",value=1.225,min_value=.0001); battery=st.number_input("Usable battery energy (kWh)",value=45.0,min_value=.001); whkm=st.number_input("Vehicle energy consumption (Wh/km)",value=150.0,min_value=.001); go=st.form_submit_button("Run vehicle estimate")
    if go:
        r=eng.ev_road_load(mass,speed,accel,grade,crr,cd,area,rho); electrical=r['wheel_power_kw']/.92 if r['wheel_power_kw']>=0 else r['wheel_power_kw']*.92; current=electrical*1000/400 if electrical>=0 else electrical*1000/400; range_=battery*1000/whkm
        result_panel("EV longitudinal road-load estimate",f"Rolling resistance = Crr·mg·cosθ = {r['rolling_n']:.2f} N\nAerodynamic drag = ½ρCdAv² = {r['aero_n']:.2f} N\nGradient force = mg·sinθ = {r['grade_n']:.2f} N\nAcceleration force = ma = {r['accel_n']:.2f} N\nTotal tractive force = sum = {r['total_force_n']:.2f} N\nWheel power = Ftotal·v = {r['wheel_power_kw']:.2f} kW\nApprox electrical demand at 92% efficiency = {electrical:.2f} kW\nIllustrative range from consumption = {range_:.1f} km",[r"F_{roll}=C_{rr}mg\cos\theta",r"F_{aero}=\frac12\rho C_DAv^2",r"F_{grade}=mg\sin\theta",r"F_{acc}=ma",r"F_{tractive}=F_{roll}+F_{aero}+F_{grade}+F_{acc}",r"P_{wheel}=F_{tractive}v"],[("Tractive force",f"{r['total_force_n']:.0f} N"),("Wheel power",f"{r['wheel_power_kw']:.2f} kW"),("Estimated range",f"{range_:.0f} km")],"Steady target speed with entered acceleration and gradient applied simultaneously. Fixed 92% drivetrain efficiency and 400 V bus for indicative current only; no transient motor map, tyre, battery voltage sag, temperature, traffic or regenerative strategy.")
        vehicle_animation(speed,r['total_force_n'],r['wheel_power_kw'],range_)

elif current == "EV matching & regeneration":
    st.subheader("EV motor–battery matching and regenerative braking")
    tab1,tab2=st.tabs(["Motor–battery matching", "Regenerative braking"])
    with tab1:
        with st.form("evmatch_form"):
            c1,c2=st.columns(2); mass=c1.number_input("Vehicle mass (kg)",value=1500.0,min_value=.1); speed=c2.number_input("Design speed (km/h)",value=60.0,min_value=.1); acc=c1.number_input("Acceleration (m/s²)",value=.5); grade=c2.number_input("Gradient (%)",value=0.0); crr=c1.number_input("Rolling resistance coefficient",value=.012,min_value=0.0); cd=c2.number_input("Drag coefficient",value=.29,min_value=0.0); area=c1.number_input("Frontal area (m²)",value=2.2,min_value=.001); ratio=c2.number_input("Reduction ratio",value=9.0,min_value=.001); radius=c1.number_input("Tyre radius (m)",value=.3,min_value=.001); drive=c2.number_input("Drivetrain efficiency (%)",value=95.0,min_value=.001,max_value=100.0); meff=c1.number_input("Motor/inverter efficiency (%)",value=92.0,min_value=.001,max_value=100.0); voltage=c2.number_input("Battery voltage (V)",value=400.0,min_value=.1); capacity=c1.number_input("Battery capacity (Ah)",value=100.0,min_value=.001); c_rate=c2.number_input("Continuous battery C-rate",value=2.0,min_value=.001); rated=c1.number_input("Motor rated power (kW)",value=60.0,min_value=.001); peak=c2.number_input("Motor peak power (kW)",value=100.0,min_value=.001); maxrpm=c1.number_input("Motor maximum RPM",value=8000.0,min_value=.001); go=st.form_submit_button("Run matching analysis")
        if go:
            if rated>peak: st.warning("Entered motor peak rating is lower than rated rating; verify inputs.")
            road=eng.ev_road_load(mass,speed,acc,grade,crr,cd,area); pm=road['wheel_power_kw']/(drive/100); pe=pm/(meff/100); current=pe*1000/voltage; actual_c=current/capacity; pbat=voltage*capacity*c_rate/1000; torque=road['total_force_n']*radius/(ratio*drive/100); motor_rpm=(speed/3.6)/ (2*math.pi*radius)*60*ratio
            summary=f"Tractive force = {road['total_force_n']:.1f} N\nWheel power = {road['wheel_power_kw']:.2f} kW\nRequired motor mechanical power = Pwheel/ηdrive = {pm:.2f} kW\nRequired electrical input = Pmotor/ηmotor = {pe:.2f} kW\nEstimated battery current I=P/V = {current:.1f} A\nBattery discharge rate = I/Ah = {actual_c:.2f} C\nContinuous battery power estimate = V×Ah×C/1000 = {pbat:.2f} kW\nRequired motor torque = F×r/(gear ratio×ηdrive) = {torque:.1f} N·m\nMotor speed at design vehicle speed = {motor_rpm:.0f} RPM\nRated motor power: {'PASS' if pm<=rated else 'WARNING'} · Peak motor power: {'PASS' if pm<=peak else 'WARNING'}\nBattery continuous power: {'PASS' if pe<=pbat else 'WARNING'} · Motor max RPM: {'PASS' if motor_rpm<=maxrpm else 'WARNING'}"
            result_panel("EV motor–battery compatibility",summary,[r"F_{tractive}=F_{roll}+F_{aero}+F_{grade}+F_{acc}",r"P_m=\frac{F_{tractive}v}{\eta_{drive}}",r"P_e=\frac{P_m}{\eta_{motor}}",r"I=\frac{P_e}{V_{pack}}",r"C_{rate}=\frac{I}{Ah_{pack}}",r"P_{battery,continuous}=\frac{V\times Ah\times C}{1000}"],[("Motor demand",f"{pm:.2f} kW"),("Battery demand",f"{pe:.2f} kW"),("Discharge rate",f"{actual_c:.2f} C")],"Simplified steady road-load check; acceleration and gradient are applied together. Battery power check uses user-entered C-rate and nominal voltage. No voltage sag, BMS limits, cell temperature, inverter map, traction limits or transient duty cycle.")
    with tab2:
        with st.form("regen_form"):
            c1,c2=st.columns(2); mass= c1.number_input("Vehicle mass (kg)",value=1500.0,min_value=.1); speed=c2.number_input("Initial speed (km/h)",value=60.0,min_value=0.0); capture=c1.number_input("Kinetic energy capture fraction (%)",value=70.0,min_value=0.0,max_value=100.0); eff=c2.number_input("Electrical recovery efficiency (%)",value=80.0,min_value=0.0,max_value=100.0); duration=c1.number_input("Braking duration (s)",value=10.0,min_value=.001); go=st.form_submit_button("Estimate recovered energy")
        if go:
            r=eng.regenerative_braking(mass,speed,capture,eff,duration); result_panel("Regenerative braking estimate",f"Initial kinetic energy = ½mv² = {r['kinetic_j']/1000:.3f} kJ\nRecovered electrical energy = KE×capture×η = {r['recovered_wh']:.2f} Wh\nAverage recovered power = Erecovered/t = {r['average_kw']:.2f} kW",[r"KE=\frac12mv^2",r"E_{recovered}=KE\,f_{capture}\,\eta_{recovery}",r"P_{avg}=\frac{E_{recovered}}{t}"],[("Recovered energy",f"{r['recovered_wh']:.2f} Wh"),("Average recovery power",f"{r['average_kw']:.2f} kW")],"Single stop from the specified speed; ignores braking distribution, tyre adhesion, motor/inverter limits, battery state of charge, temperature and charge acceptance.")

elif current == "History & reports":
    st.subheader("Session history and exports")
    hist=st.session_state.history
    st.caption("Streamlit Community Cloud instances can restart and local session memory is temporary. Download your reports to retain results.")
    if hist:
        st.dataframe(hist,use_container_width=True,hide_index=True)
        csvbuf=io.StringIO(); writer=csv.DictWriter(csvbuf,fieldnames=["time","module","summary","formulas"]); writer.writeheader(); writer.writerows(hist)
        st.download_button("Download calculation history CSV",csvbuf.getvalue().encode(),file_name="ForgeLab_history.csv",mime="text/csv")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from xml.sax.saxutils import escape
            b=io.BytesIO(); doc=SimpleDocTemplate(b,pagesize=A4); styles=getSampleStyleSheet(); data=[["Date","Module","Summary"]]
            for row in hist[:100]: data.append([row['time'],row['module'],row['summary'][:500]])
            table=Table(data,colWidths=[75,95,270],repeatRows=1); table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.HexColor('#173a50')),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),'TOP')]))
            story=[Paragraph("FORGELAB ENGINEERING REPORT",styles['Title']),Spacer(1,10),table]; doc.build(story); b.seek(0)
            st.download_button("Download PDF report",b.getvalue(),file_name="ForgeLab_report.pdf",mime="application/pdf")
        except Exception as ex: st.warning(f"PDF export is unavailable in this environment: {ex}")
        if st.button("Clear session history"): st.session_state.history=[]; st.rerun()
    else: st.info("No calculations saved in this browser session yet. Run a module, then return here to export the results.")

st.divider()
st.caption("ForgeLab is an educational and preliminary engineering tool. Always validate units, material data, boundary conditions, manufacturer ratings, design codes and safety requirements before using any result in a real design.") st.form("aero_form"):
        
