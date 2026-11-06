"""Pure calculation functions used by ForgeLab Streamlit. SI and stated unit conventions are explicit."""
from __future__ import annotations
import math

G = 9.80665
R_AIR = 0.287  # kJ/(kg K)
GAMMA_AIR = 1.4
CV_AIR = R_AIR / (GAMMA_AIR - 1.0)  # kJ/(kg K)


def _positive(name: str, value: float, allow_zero: bool = False) -> float:
    x = float(value)
    if not math.isfinite(x) or (x < 0 if allow_zero else x <= 0):
        op = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be finite and {op}.")
    return x


def stress_strain(force_n, area_mm2, length_mm, extension_mm):
    area = _positive("Area", area_mm2)
    length = _positive("Original length", length_mm)
    stress = float(force_n) / area  # N/mm2 = MPa
    strain = float(extension_mm) / length
    return {"stress_mpa": stress, "strain": strain, "extension_mm": float(extension_mm)}


def young_modulus(stress_mpa, strain):
    e = _positive("Strain", strain)
    return {"E_mpa": float(stress_mpa) / e, "E_gpa": float(stress_mpa) / e / 1000}


def factor_of_safety(yield_mpa, working_mpa):
    return _positive("Yield strength", yield_mpa) / _positive("Working stress", working_mpa)


def beam_central_load(load_n, span_mm, young_mpa, inertia_mm4, points=81):
    P = _positive("Load", load_n, allow_zero=True)
    L = _positive("Span", span_mm)
    E = _positive("Young's modulus", young_mpa)
    I = _positive("Second moment of area", inertia_mm4)
    ra = rb = P / 2
    mmax = P * L / 4
    ymax = P * L**3 / (48 * E * I)
    xs, vs, ms, ys = [], [], [], []
    for i in range(points):
        x = L * i / (points - 1)
        if x < L / 2:
            v = ra
            m = ra * x
            y = P * x * (3 * L**2 - 4 * x**2) / (48 * E * I)
        else:
            v = -rb
            m = rb * (L - x)
            z = L - x
            y = P * z * (3 * L**2 - 4 * z**2) / (48 * E * I)
        xs.append(x); vs.append(v); ms.append(m); ys.append(y)
    return {"RA_N": ra, "RB_N": rb, "Vmax_N": P/2, "Mmax_Nmm": mmax,
            "deflection_mm": ymax, "x_mm": xs, "shear_N": vs, "moment_Nmm": ms,
            "deflection_curve_mm": ys}


def bending_stress(moment_nmm, y_mm, inertia_mm4):
    return float(moment_nmm) * float(y_mm) / _positive("Second moment of area", inertia_mm4)


def torsion(torque_nmm, radius_mm, polar_inertia_mm4, length_mm, shear_modulus_mpa):
    J = _positive("Polar second moment", polar_inertia_mm4)
    Gm = _positive("Shear modulus", shear_modulus_mpa)
    L = _positive("Shaft length", length_mm)
    tau = float(torque_nmm) * float(radius_mm) / J
    theta = float(torque_nmm) * L / (J * Gm)
    return {"tau_mpa": tau, "twist_rad": theta, "twist_deg": math.degrees(theta)}


def shaft_power_torque(power_kw, rpm):
    n = _positive("Speed", rpm)
    p = float(power_kw)
    torque = 9550.0 * p / n
    return {"torque_nm": torque, "power_kw": p}


def euler_buckling(E_mpa, I_mm4, length_mm, effective_length_factor=1.0):
    E = _positive("Young's modulus", E_mpa); I = _positive("Second moment of area", I_mm4)
    L = _positive("Length", length_mm); k = _positive("Effective length factor", effective_length_factor)
    return math.pi**2 * E * I / (k * L)**2


def gear_pair(input_rpm, input_torque_nm, driver_teeth, driven_teeth, efficiency_percent=98):
    z1 = _positive("Driver teeth", driver_teeth); z2 = _positive("Driven teeth", driven_teeth)
    eta = _positive("Efficiency", efficiency_percent) / 100
    if eta > 1: raise ValueError("Efficiency cannot exceed 100%.")
    ratio = z2 / z1
    return {"ratio": ratio, "output_rpm": float(input_rpm)/ratio,
            "output_torque_nm": float(input_torque_nm)*ratio*eta}


def sdof_vibration(mass_kg, stiffness_n_m, damping_ns_m):
    m = _positive("Mass", mass_kg); k = _positive("Stiffness", stiffness_n_m); c = _positive("Damping", damping_ns_m, allow_zero=True)
    wn = math.sqrt(k/m); cc = 2*math.sqrt(k*m); zeta = c/cc
    wd = wn*math.sqrt(max(0.0, 1-zeta*zeta)) if zeta < 1 else 0.0
    return {"wn_rad_s": wn, "fn_hz": wn/(2*math.pi), "critical_damping": cc,
            "zeta": zeta, "wd_rad_s": wd, "damped_frequency_hz": wd/(2*math.pi)}


def machining(turning_diameter_mm, cutting_speed_m_min, feed_mm_rev, depth_mm, length_mm):
    D = _positive("Diameter", turning_diameter_mm); V = _positive("Cutting speed", cutting_speed_m_min)
    f = _positive("Feed", feed_mm_rev); d = _positive("Depth of cut", depth_mm); L = _positive("Machining length", length_mm)
    rpm = 1000*V/(math.pi*D)
    feed_rate = f*rpm
    time_min = L/feed_rate
    mrr = math.pi*D*f*d*rpm
    return {"rpm": rpm, "feed_rate_mm_min": feed_rate, "time_min": time_min, "mrr_mm3_min": mrr}


def ideal_gas(mass_kg, pressure_kpa, volume_m3, temperature_k):
    m = _positive("Mass", mass_kg); p = _positive("Pressure", pressure_kpa); V = _positive("Volume", volume_m3); T = _positive("Temperature", temperature_k)
    density = m/V
    r_specific = p*V/(m*T)  # kJ/(kg K), since kPa*m3 = kJ
    return {"density": density, "R_kj_kgk": r_specific, "pressure_check_kpa": density*r_specific*T}


def first_law_closed(Q_kJ, W_by_system_kJ, delta_U_kJ, delta_KE_kJ=0, delta_PE_kJ=0):
    # Q - W = ΔU + ΔKE + ΔPE; positive Q into system, positive W by system.
    lhs = float(Q_kJ) - float(W_by_system_kJ)
    rhs = float(delta_U_kJ) + float(delta_KE_kJ) + float(delta_PE_kJ)
    return {"Q_minus_W_kJ": lhs, "delta_total_energy_kJ": rhs, "residual_kJ": lhs-rhs}


def otto_cycle(compression_ratio, t1_k, p1_kpa, qin_kj_kg, gamma=GAMMA_AIR, cv_kj_kgk=CV_AIR, points=61):
    r = _positive("Compression ratio", compression_ratio)
    T1 = _positive("Initial temperature", t1_k); p1 = _positive("Initial pressure", p1_kpa)
    qin = _positive("Heat input", qin_kj_kg); g = _positive("Specific heat ratio", gamma); cv = _positive("Specific heat at constant volume", cv_kj_kgk)
    if r <= 1 or g <= 1: raise ValueError("Compression ratio and gamma must be greater than 1.")
    T2 = T1*r**(g-1); p2 = p1*r**g
    T3 = T2 + qin/cv; p3 = p2*T3/T2
    T4 = T3/r**(g-1); p4 = p3/r**g
    qout = cv*(T4-T1); eta = 1-qout/qin; work = qin-qout
    # Relative volumes: V1=1; V2=1/r. Isentropic compression & expansion sampled.
    v1, v2 = 1.0, 1.0/r
    v12=[v1-(v1-v2)*i/(points-1) for i in range(points)]
    p12=[p1*(v1/v)**g for v in v12]
    v23=[v2]*2; p23=[p2,p3]
    v34=[v2+(v1-v2)*i/(points-1) for i in range(points)]
    p34=[p3*(v2/v)**g for v in v34]
    return {"T1":T1,"T2":T2,"T3":T3,"T4":T4,"p1":p1,"p2":p2,"p3":p3,"p4":p4,
            "qin":qin,"qout":qout,"work":work,"efficiency":eta,
            "v_cycle":v12+v23+v34+[v1],"p_cycle":p12+p23+p34+[p1]}


def carnot_efficiency(hot_k, cold_k):
    Th = _positive("Hot reservoir temperature", hot_k); Tc = _positive("Cold reservoir temperature", cold_k)
    if Tc >= Th: raise ValueError("Cold reservoir must be colder than hot reservoir.")
    return 1-Tc/Th


def heat_transfer(k_w_mk, area_m2, delta_t_k, thickness_m, h_w_m2k):
    k = _positive("Thermal conductivity", k_w_mk); A = _positive("Area", area_m2)
    L = _positive("Thickness", thickness_m); h = _positive("Convection coefficient", h_w_m2k)
    dT = float(delta_t_k)
    qcond = k*A*dT/L; qconv = h*A*dT
    return {"conduction_w":qcond,"convection_w":qconv}


def pipe_flow(diameter_m, flow_rate_m3_s, density_kg_m3, viscosity_pa_s, length_m, roughness_m=0.000045):
    D = _positive("Diameter", diameter_m); Q = _positive("Flow rate", flow_rate_m3_s, allow_zero=True)
    rho = _positive("Density", density_kg_m3); mu = _positive("Dynamic viscosity", viscosity_pa_s)
    L = _positive("Pipe length", length_m); eps = _positive("Roughness", roughness_m, allow_zero=True)
    area = math.pi*D**2/4; velocity = Q/area; re = rho*velocity*D/mu
    if re == 0: f=0.0; regime="No flow"; hf=0.0
    elif re < 2300: f=64/re; regime="Laminar"; hf=f*(L/D)*velocity**2/(2*G)
    elif re < 4000: f=None; regime="Transitional"; hf=None
    else:
        f=0.25/(math.log10(eps/(3.7*D)+5.74/(re**0.9))**2)
        regime="Turbulent"; hf=f*(L/D)*velocity**2/(2*G)
    dp = rho*G*hf if hf is not None else None
    return {"area_m2":area,"velocity_m_s":velocity,"reynolds":re,"regime":regime,
            "friction_factor":f,"head_loss_m":hf,"pressure_drop_pa":dp}


def pump_power(flow_rate_m3_s, head_m, density_kg_m3, efficiency_percent):
    Q=_positive("Flow rate",flow_rate_m3_s); H=_positive("Head",head_m,allow_zero=True); rho=_positive("Density",density_kg_m3); eta=_positive("Efficiency",efficiency_percent)/100
    if eta>1: raise ValueError("Efficiency cannot exceed 100%.")
    hydraulic=rho*G*Q*H
    return {"hydraulic_w":hydraulic,"shaft_w":hydraulic/eta}


def aerodynamics(speed_kmh, rho_kg_m3, cd, frontal_area_m2, cl=0.0):
    v=float(speed_kmh)/3.6
    if v < 0: raise ValueError("Speed cannot be negative.")
    rho=_positive("Air density",rho_kg_m3); A=_positive("Frontal area",frontal_area_m2); cdrag=_positive("Cd",cd,allow_zero=True)
    q=.5*rho*v*v; drag=q*cdrag*A; lift=q*float(cl)*A
    return {"speed_m_s":v,"dynamic_pressure_pa":q,"drag_n":drag,"drag_power_kw":drag*v/1000,"lift_n":lift}


def ev_battery(cell_v, cell_ah, series, parallel, usable_percent, wh_per_km):
    Vc=_positive("Cell voltage",cell_v); Ahc=_positive("Cell capacity",cell_ah); Ns=int(series); Np=int(parallel)
    if Ns<1 or Np<1: raise ValueError("Series and parallel cell counts must be positive integers.")
    usable=_positive("Usable percentage",usable_percent)/100; cons=_positive("Consumption",wh_per_km)
    if usable>1: raise ValueError("Usable percentage cannot exceed 100%.")
    V=Vc*Ns; Ah=Ahc*Np; energy=V*Ah/1000; u=energy*usable
    return {"voltage_v":V,"capacity_ah":Ah,"cells":Ns*Np,"energy_kwh":energy,"usable_kwh":u,"range_km":u*1000/cons}


def ev_road_load(mass_kg, speed_kmh, acceleration_m_s2, grade_percent, crr, cd, frontal_area_m2, rho=1.225):
    m=_positive("Mass",mass_kg); v=float(speed_kmh)/3.6
    if v<0: raise ValueError("Speed cannot be negative.")
    theta=math.atan(float(grade_percent)/100)
    rolling=float(crr)*m*G*math.cos(theta); aero=.5*rho*float(cd)*frontal_area_m2*v*v
    grade=m*G*math.sin(theta); accel=m*float(acceleration_m_s2)
    force=rolling+aero+grade+accel
    return {"rolling_n":rolling,"aero_n":aero,"grade_n":grade,"accel_n":accel,
            "total_force_n":force,"wheel_power_kw":force*v/1000}


def material_reference(name):
    refs={"Mild steel":250.0,"Aluminium 6061-T6":276.0,"Copper":70.0,"Titanium Grade 5":880.0}
    return refs[name]


def mohr_circle(sigma_x_mpa, sigma_y_mpa, tau_xy_mpa):
    sx, sy, t = float(sigma_x_mpa), float(sigma_y_mpa), float(tau_xy_mpa)
    avg = (sx + sy) / 2
    radius = math.sqrt(((sx - sy) / 2)**2 + t**2)
    s1, s2 = avg + radius, avg - radius
    angle = 0.5 * math.degrees(math.atan2(2*t, sx-sy))
    return {"sigma1_mpa":s1,"sigma2_mpa":s2,"tau_max_mpa":radius,"sigma_avg_mpa":avg,"principal_angle_deg":angle}


def thin_wall_cylinder(pressure_mpa, diameter_mm, thickness_mm):
    p=_positive("Internal pressure",pressure_mpa,allow_zero=True); d=_positive("Diameter",diameter_mm); t=_positive("Wall thickness",thickness_mm)
    if t/d >= .1: raise ValueError("Thin-wall assumption not met: use t/D < 0.1 as a preliminary check.")
    return {"hoop_mpa":p*d/(2*t),"longitudinal_mpa":p*d/(4*t)}


def goodman_fos(stress_mean_mpa, stress_alternating_mpa, endurance_limit_mpa, ultimate_strength_mpa):
    Se=_positive("Endurance limit",endurance_limit_mpa); Sut=_positive("Ultimate strength",ultimate_strength_mpa)
    sm=float(stress_mean_mpa); sa=_positive("Alternating stress",stress_alternating_mpa,allow_zero=True)
    denominator=sa/Se+sm/Sut
    if denominator <= 0: raise ValueError("Goodman denominator must be positive for this calculation.")
    return 1/denominator


def helical_spring(load_n, wire_diameter_mm, mean_coil_diameter_mm, active_coils, shear_modulus_mpa):
    F=_positive("Load",load_n,allow_zero=True); d=_positive("Wire diameter",wire_diameter_mm); D=_positive("Mean coil diameter",mean_coil_diameter_mm); n=_positive("Active coils",active_coils); Gm=_positive("Shear modulus",shear_modulus_mpa)
    C=D/d
    if C <= 1: raise ValueError("Spring index D/d must exceed 1.")
    wahl=(4*C-1)/(4*C-4)+0.615/C
    tau=wahl*8*F*D/(math.pi*d**3)
    k=Gm*d**4/(8*D**3*n)
    delta=F/k
    return {"spring_index":C,"wahl_factor":wahl,"shear_stress_mpa":tau,"rate_n_mm":k,"deflection_mm":delta}


def diesel_cycle(compression_ratio, cutoff_ratio, t1_k, p1_kpa, gamma=GAMMA_AIR):
    r=_positive("Compression ratio",compression_ratio); rc=_positive("Cut-off ratio",cutoff_ratio); T1=_positive("T1",t1_k); p1=_positive("P1",p1_kpa); g=_positive("Gamma",gamma)
    if r<=1 or rc<=1 or rc>=r or g<=1: raise ValueError("Require r > cut-off ratio > 1 and gamma > 1.")
    cp=g*R_AIR/(g-1); cv=R_AIR/(g-1)
    T2=T1*r**(g-1); p2=p1*r**g
    T3=T2*rc; p3=p2
    expansion=r/rc; T4=T3/(expansion**(g-1)); p4=p3/(expansion**g)
    qin=cp*(T3-T2); qout=cv*(T4-T1); eta=1-qout/qin
    return {"T2":T2,"T3":T3,"T4":T4,"p2":p2,"p3":p3,"p4":p4,"qin":qin,"qout":qout,"work":qin-qout,"efficiency":eta}


def brayton_cycle(pressure_ratio, t1_k, t3_k, gamma=GAMMA_AIR):
    rp=_positive("Pressure ratio",pressure_ratio); T1=_positive("Compressor inlet T1",t1_k); T3=_positive("Turbine inlet T3",t3_k); g=_positive("Gamma",gamma)
    if rp<=1 or g<=1 or T3<=T1: raise ValueError("Require pressure ratio > 1, gamma > 1 and T3 > T1.")
    exponent=(g-1)/g; cp=g*R_AIR/(g-1)
    T2=T1*rp**exponent; T4=T3/(rp**exponent)
    if T3 <= T2: raise ValueError("Turbine inlet temperature must exceed compressor outlet temperature.")
    wc=cp*(T2-T1); wt=cp*(T3-T4); qin=cp*(T3-T2); wnet=wt-wc
    return {"T2":T2,"T4":T4,"compressor_work":wc,"turbine_work":wt,"qin":qin,"net_work":wnet,"efficiency":wnet/qin}


def rankine_cycle(h1_kj_kg, h2_kj_kg, h3_kj_kg, h4_kj_kg):
    h1,h2,h3,h4=map(float,(h1_kj_kg,h2_kj_kg,h3_kj_kg,h4_kj_kg))
    wp=h2-h1; wt=h3-h4; qin=h3-h2; qout=h4-h1; wnet=wt-wp
    if qin<=0: raise ValueError("Boiler heat input h3-h2 must be positive.")
    if wnet<=0 or wnet>qin: raise ValueError("Check the Rankine state enthalpies; net work must be positive and no greater than heat input.")
    return {"pump_work":wp,"turbine_work":wt,"qin":qin,"qout":qout,"net_work":wnet,"efficiency":wnet/qin}


def refrigeration_cop(cooling_capacity_kw, compressor_power_kw):
    q=_positive("Cooling capacity",cooling_capacity_kw); w=_positive("Compressor power",compressor_power_kw)
    cop=q/w
    return {"cop":cop,"heat_rejected_kw":q+w,"heat_pump_cop":(q+w)/w}


def hydrostatic_pressure(density_kg_m3, depth_m):
    rho=_positive("Fluid density",density_kg_m3); h=_positive("Depth",depth_m,allow_zero=True)
    return rho*G*h


def bernoulli_two_sections(d1_m, d2_m, flow_rate_m3_s, p1_pa, z1_m=0.0, z2_m=0.0, density_kg_m3=1000.0):
    d1=_positive("Inlet diameter",d1_m); d2=_positive("Outlet diameter",d2_m); Q=_positive("Flow rate",flow_rate_m3_s,allow_zero=True); rho=_positive("Density",density_kg_m3)
    a1=math.pi*d1*d1/4; a2=math.pi*d2*d2/4; v1=Q/a1; v2=Q/a2
    p2=float(p1_pa)+.5*rho*(v1*v1-v2*v2)+rho*G*(float(z1_m)-float(z2_m))
    return {"v1":v1,"v2":v2,"p2_pa":p2,"a1":a1,"a2":a2}


def regenerative_braking(mass_kg, speed_kmh, capture_percent, efficiency_percent, duration_s):
    m=_positive("Vehicle mass",mass_kg); v=float(speed_kmh)/3.6
    if v<0: raise ValueError("Speed cannot be negative.")
    c=_positive("Capture percentage",capture_percent,allow_zero=True)/100; eta=_positive("Recovery efficiency",efficiency_percent,allow_zero=True)/100; t=_positive("Braking duration",duration_s)
    if c>1 or eta>1: raise ValueError("Percentages cannot exceed 100%.")
    kinetic=.5*m*v*v; recovered_j=kinetic*c*eta
    return {"kinetic_j":kinetic,"recovered_wh":recovered_j/3600,"average_kw":recovered_j/t/1000}


def radiation_heat(emissivity, area_m2, surface_temp_k, surrounding_temp_k):
    eps=_positive("Emissivity",emissivity,allow_zero=True); A=_positive("Area",area_m2); Ts=_positive("Surface temperature",surface_temp_k); Tsur=_positive("Surrounding temperature",surrounding_temp_k)
    if eps>1: raise ValueError("Emissivity must be between 0 and 1.")
    sigma=5.670374419e-8
    return eps*sigma*A*(Ts**4-Tsur**4)


def sheet_metal_blank_force(thickness_mm, cut_perimeter_mm, shear_strength_mpa):
    t=_positive("Thickness",thickness_mm); perimeter=_positive("Cut perimeter",cut_perimeter_mm); tau=_positive("Shear strength",shear_strength_mpa)
    return t*perimeter*tau  # MPa=N/mm2


def welding_heat_input(voltage_v, current_a, travel_speed_mm_s, efficiency=0.8):
    V=_positive("Voltage",voltage_v); I=_positive("Current",current_a); speed=_positive("Travel speed",travel_speed_mm_s); eta=_positive("Process efficiency",efficiency)
    if eta>1: raise ValueError("Efficiency must be a fraction no greater than 1.")
    return eta*V*I/speed/1000  # kJ/mm
