import math
import scipy.optimize as op
from datetime import datetime
from types import SimpleNamespace
from Utils import(
    pas, f_projected,
    # ===== Constants =====
    stefan,elong,elongA,Ar_ratio,kclo,w_max,icl,Work,Weight,Area,
)

def iterate_tcl(Iclo, tsk, elong, stefan, Ar_ratio, tr, hc, ta, FACL, nsa_cl, Js):
    if Iclo == 0:
        tcl = tsk
        hr = elong * stefan * Ar_ratio * ((tcl + 273.15) ** 2 + (tr + 273.15) ** 2) * (tcl + 273.15 + tr + 273.15)
        FCL = 1.0
    else:
        n = 0
        tcl = tsk  # default
        
        while True:
            n += 1
            tcl_old = tcl
            
            hr = elong * stefan * Ar_ratio * ((tcl + 273.15) ** 2 + (tr + 273.15) ** 2) * (tcl + 273.15 + tr + 273.15)
            FCL = 1 / (1 + 0.155 * (hc + hr) * FACL * Iclo)
            tcl = FCL * tsk + (1 - FCL) * (hc * ta + hr * tr) / (hc + hr) + FCL * nsa_cl * Js / (0.155 * Iclo)
            
            if n > 150:
                raise RuntimeError("tcl iteration not converged")
            
            if abs(tcl_old - tcl) < 0.001:
                break
    
    return tcl, hr, FCL


def perform_calculation(global_params, record):
    g = SimpleNamespace(**global_params)
    r = SimpleNamespace(**record)
    s = SimpleNamespace(**r.solar_inputs)

    # --- alias
    # include_solar=g.include_solar
    estimate_hc=g.estimate_hc
    fcd=g.fcd
    physiol_source=g.physiol_source

    ta,Vel,Vel_10 = r.ta,r.Vel,r.Vel_10
    representative_temp = r.representative_temp
    Pa,RH = r.Pa,r.RH
    tr = r.tr
    Iclo,FACL=r.Iclo,r.FACL
    M_watt,Ms=r.M_watt,r.Ms
    tsk,w=r.tsk,r.w
    conduct_heat=r.conduct_heat

    altitude_rad=s.altitude_rad
    Kd,Ku,Ikt,Idn = s.Kd,s.Ku,s.Ikt,s.Idn
    c_skyi=s.c_skyi
    nsa_cl,nsa_sk=s.nsa_cl,s.nsa_sk

    # --- calculation

    # convective heat transfer coefficient
    if estimate_hc == "Two-node model":
        hc1 = 5.66 * (Ms / 58.15 - 0.85) ** 0.39  # Active in still air
        hc2 = 8.6 * Vel ** 0.53  # Walking in still air
        hc = max(hc1, hc2, 3)  # Minimum 3 W/m2K
        hco = max(5.66 * (Ms / 58.15 - 0.85) ** 0.39, 3)
    elif estimate_hc == "Kuwabara's formula":
        # Kuwabara et al. (2002)
        hc = 3.36 + 6.86 * Vel ** 0.92  # 0.1-4.7 m/s range
        hco = 3.36

    # --- angle factor ---
    AFground = 0.5
    AFsky = c_skyi / 2
    AFsurroundings = 0.5 - AFsky #Use this if the diffused or reflected solar radiation from objects other than the sky in the upper hemisphere cannot be ignored

    # Solar radiation components
    Js_dn = FACL * f_projected(altitude_rad, Area) * Idn    # Direct solar radiation reached to the clothed body [W/m2]
    Js_kt = FACL * Ar_ratio * AFsky * Ikt                   # Diffused solar radiation reached to the clothed body [W/m2]
    Js_low = FACL * Ar_ratio * AFground * Ku                # assuming it consists of diffuse component only
    Js = Js_dn + Js_kt + Js_low

    Cdj = fcd * conduct_heat

    fn = 1 - fcd # non-contact area factor [-]

    if physiol_source == "Two-node model":
        # ===== Constants for Two-node model =====
        set_tsk = 33.7          # Gagge et al.(1986)
        set_tcr = 36.8          # Gagge et al.(1986)
        set_tb = 36.49          # = alpha*set_tsk + (1-alpha)*set_tcr
        C_SW = 170.0            # [g/m2h]Gagge et al.(1986);ASHRAE Standard 55-2013;ASHRAE Fundamentals 2021
        C_STR = 0.5             # [-]Fobelets and Gagge (1988)ASHRAE Standard 55-2013;ASHRAE Fundamentals 2021
        C_DIL = 120.0           # [L/m2hK]ASHRAE Standard 55-2013;ASHRAE Fundamentals 2021

        # initial guesses / state
        tsk = set_tsk
        tcr = set_tcr
        tb = set_tb
        Esk = 7.3               # [W/m2] - skin evaporative heat loss # Fobelets and Gagge (1988)
        alpha = 0.1
        BloodFlow = 6.3         # [L/m2h]Gagge et al.(1986);Fobelets and Gagge (1988)ASHRAE Standard 55-2013;ASHRAE Fundamentals 2021
        Tim = 0

        # Main simulation loop (1 hour)
        while Tim < 1.0:
            # clothing surface temp iteration (updates hr, FCL)
            tcl, hr, FCL = iterate_tcl(Iclo, tsk, elong, stefan, Ar_ratio, tr, hc, ta, FACL, nsa_cl, Js)

            htotal = hc + hr # [W/m2K]
            CLOE = Iclo - (FACL - 1) / (0.155 * FACL * htotal) # [clo]
            FCLE = FCL * FACL # Effective clothing thermal efficiency [-]
            FPCL = 1 / (1 + (0.155 / icl) * hc * FACL * Iclo) if Iclo > 0 else 1.0 # Permeation efficiency factor of clothing [-]

            ERFS = fn * Js * (FCL * nsa_cl + nsa_sk) # [W/m2]
            # ERFS_dn = fn * Js_dn * (FCL * nsa_cl + nsa_sk)
            # ERFS_kt = fn * Js_kt * (FCL * nsa_cl + nsa_sk)
            # ERFS_low = fn * Js_low * (FCL * nsa_cl + nsa_sk)

            # Heat loss [W/m2]
            SensibleHeat = fn * FCLE * (hc * (tsk - ta) + hr * (tsk - tr)) - ERFS + Cdj
            Eres = 0.017251 * M_watt * (5.8662 - Pa)  # respiratory evaporation
            Cres = 0.0014 * M_watt * (34 - ta)  # respiratory convection

            # Heat flow between core and skin [W/m2]
            HeatFlow_sk = (tcr - tsk) * (5.28 + 1.163 * BloodFlow) - Esk - SensibleHeat
            HeatFlow_cr = M_watt- (tcr - tsk) * (5.28 + 1.163 * BloodFlow) - Cres - Eres - Work

            # heat capacities [kJ/m2K](average man : 70 kg, 1.8 square meter)
            SpecficHeat_sk = alpha * 0.97 * Weight
            SpecficHeat_cr = (1.0 - alpha) * 0.97 * Weight

            # time step adapt (average man : 70 kg, 1.8 square meter)
            delta_tsk = (HeatFlow_sk * Area) / max(SpecficHeat_sk, 1e-9)
            delta_tcr = (HeatFlow_cr * Area) / max(SpecficHeat_cr, 1e-9)
            # delta_tb = alpha * delta_tsk + (1 - alpha) * delta_tcr
            deltaTime = 1/60  
            if abs(delta_tsk) >= 0.1 or abs(delta_tcr) >= 0.1:
                deltaTime = 1/600  
            
            Tim += deltaTime

            # Update temperatures
            tsk += delta_tsk * deltaTime
            tcr += delta_tcr * deltaTime
            tb = alpha * tsk + (1 - alpha) * tcr

            # regulatory sweating (g/m2h)
            # Vascular & sweat control signals
            SKSIG = tsk - set_tsk
            WARMS = max(SKSIG, 0)
            COLDS = max(-SKSIG, 0)
            
            CRSIG = tcr - set_tcr
            WARMC = max(CRSIG, 0)
            COLDC = max(-CRSIG, 0)
            
            BSIG = tb - set_tb
            WARMB = max(BSIG, 0)
            COLDB = max(-BSIG, 0)

            # Control skin blood flow by signals
            BloodFlow = (6.3 + C_DIL * WARMC) / (1 + C_STR * COLDS)
            BloodFlow = max(0.5, min(90, BloodFlow)) 
            # ratio of skin-core masses
            alpha = 0.0417737 + 0.7451832 / (BloodFlow + 0.585417)

            # Sweating control
            REGSW = C_SW * WARMB * math.exp(WARMS / 10.7)  # [g/m2h]
            RGSWL = 500.0 # Max sweating rate [g/m2h] # Fobelets and Gagge (1988)
            REGSW = max(0, min(RGSWL, REGSW)) 

            Ersw = (1.0 - fcd) * 0.68 * REGSW  # [W/m2]

            # Metabolic adjustment for shivering
            M_watt= Ms + 19.4 * COLDS * COLDC

            # Evaporative heat loss
            LR = 15.1512 * (tsk + 273.15) / 273.15  # Lewis Relation
            Psks = pas(tsk)
            Emax = fn * LR * hc * FACL * FPCL * (Psks - Pa)

            if Emax > 0:
                w_rsw = Ersw / Emax
                w_dif = (1 - w_rsw) * 0.06
                Edif = w_dif * Emax
                Esk = Ersw + Edif
                w = Esk / Emax
                
                if w >= w_max:
                    w = w_max
                    w_rsw = (w_max - 0.06) / 0.94
                    Ersw = w_rsw * Emax
                    w_dif = (1 - w_rsw) * 0.06
                    Edif = w_dif * Emax
                    Esk = Ersw + Edif
            else:
                w_dif = 0
                Edif = 0
                Esk = Emax
                w = w_max
                w_rsw = w_max
                Ersw = 0

            # Unevaporated sweat
            # DRIP = max(0, (REGSW * 0.68 - w_rsw * Emax) / 0.68)
            # Psk = w * Psks + (1 - w) * Pa # Vapor pressure at tsk [kPa]
            # RHsk = Psk / Psks # 

    elif physiol_source == "Input directly":
        tcl, hr, FCL = iterate_tcl(Iclo, tsk, elong, stefan, Ar_ratio, tr, hc, ta, FACL, nsa_cl, Js)
        
        htotal = hc + hr # [W/m2K]
        CLOE = Iclo - (FACL - 1) / (0.155 * FACL * htotal) # [clo]
        FCLE = FCL * FACL # Effective clothing thermal efficiency [-]
        FPCL = 1 / (1 + (0.155 / icl) * hc * FACL * Iclo) if Iclo > 0 else 1.0 # Permeation efficiency factor of clothing [-]
        LR = 16.5 # 15.1512 * (tsk + 273.15) / 273.15 'Lewis Relation[K/kPa] '
        Psks = pas(tsk)
        Esk = fn * w * LR * hc * FACL * FPCL * (Psks - Pa) 
        
        ERFS = fn * Js * (FCL * nsa_cl + nsa_sk) # [W/m2]
        # ERFS_dn = fn * Js_dn * (FCL * nsa_cl + nsa_sk)
        # ERFS_kt = fn * Js_kt * (FCL * nsa_cl + nsa_sk)
        # ERFS_low = fn * Js_low * (FCL * nsa_cl + nsa_sk)

        SensibleHeat = fn * FCLE * (hc * (tsk - ta) + hr * (tsk - tr)) - ERFS + Cdj


    # ===== Thermal indices calculation ===== 
    Qsk = SensibleHeat + Esk # total rate of heat loss from skin [W/m2]

    # ______ SET* - standard new effective temperature ______
    # Standard environment for SET* (Gagge et al., 1986)
    hr_st = hr
    hc_st = max(5.66 * (Ms / 58.15 - 0.85) ** 0.39,3) 

    # standard MET-CLOS relation gives SET=24 when PMV=0 # Gagge et al.(1986)
    MW = M_watt - Work
    Iclo_st = 1.3264 / (MW / 58.15 + 0.7383) - 0.0953
    ### Iclo_st = 1.52 / (MW / 58.15 + 0.6944) - 0.1835  # ASHRAE Standard 55-2013
    FACL_st = 1 + kclo * Iclo_st
    htotal_st = hc_st + hr_st
    CLOE_st = Iclo_st - (FACL_st - 1) / (0.155 * FACL_st * htotal_st) # [clo]
    FCLE_st = 1 / (1 + 0.155 * htotal_st * CLOE_st) # [-]
    FPCL_st = 1 / (1 + (0.155 / icl) * hc_st * FACL_st * Iclo_st) # [-]
    h_st = htotal_st * FCLE_st

    f_SETstar = lambda x: Qsk - h_st * (tsk - x) - fn * w * LR * hc_st * FPCL_st * FACL_st * (Psks - pas(x) / 2)

    SETstar = op.brentq(f_SETstar, -100, 100)


    # ______ OET - occupied effective temperature ______
    # Nagano et al. (2020)
    # Standard environment for OET, same as SET*
    hd_oet = h_st
    hu_oet = h_st * fn + hd_oet * fcd # = h_st, assuming hd_oet = h_st

    EATF_oet = h_st * fn * (ta - representative_temp) 
    TVF_oet = fn * (hc_st * FCLE_st - hc * FCLE) * (tsk - ta) 
    SERFL_oet = fn * (hr_st * FCLE_st * (tsk - ta) - hr * FCLE * (tsk - tr))
    SEHF_oet = LR * w * hc_st * FPCL_st * FACL_st * fn * (Psks - pas(SETstar) / 2) - LR * w * hc * FPCL * FACL * fn * (Psks - Pa)
    SECF_oet = hd_oet * fcd * (tsk - representative_temp) - Cdj
    
    # effective temperature differences from representative temperature [°C]
    theta_EATF_oet = EATF_oet / hu_oet      # Effective air temperature field
    theta_TVF_oet = TVF_oet / hu_oet        # Thermal velocity field
    theta_SERFL_oet = SERFL_oet / hu_oet    # Standard ERFL
    theta_ERFS_oet = ERFS / hu_oet          # Effective shortwave radiant field
    theta_SEHF_oet = SEHF_oet / hu_oet      # Standard EHF
    theta_SECF_oet = SECF_oet / hu_oet      # Standard effective conduction field


    # ______ PMV-7730-2005 ______
    # ISO 7730:2005
    MW_7730 = Ms - Work # [W/m2K]
    Icl_watt = 0.155 * Iclo # [m2K/W]
    if Iclo <= 0.078:
        FACL_7730 = 1 + 1.29 * Icl_watt
    else:
        FACL_7730 = 1.05 + 0.645 * Icl_watt
    
    hcf_7730 = 12.1 * math.sqrt(Vel)  

    ### tcla = (ta + 273)  + (35.5 - ta) / (3.5 * (6.45 * Icl_watt + 0.1)) # 1994 'first guess for tcl [K]
    tcla = (ta + 273) + (35.5 - ta) / (3.5 * Icl_watt + 0.1) # 2005 # first guess for tcl [K]
    
    P1 = Icl_watt * FACL_7730
    P2 = P1 * 3.96
    P3 = P1 * 100
    P4 = P1 * (ta + 273)
    P5 = 308.7 - 0.028 * MW_7730 + P2 * ((tr + 273) / 100) ** 4
    
    XN = tcla / 100
    XF = XN
    n = 0
    eps = 0.00015
    converged = False

    # calculate surface temperature of clothing by iteration
    while True:
        XF = (XF + XN) / 2
        hcn_7730 = 2.38 * abs(100*XF - (ta + 273)) ** 0.25
        hc_7730 = max(hcf_7730, hcn_7730)

        XN = (P5 + P4 * hc_7730 - P2 * XF**4) / (100 + P3 * hc_7730)

        n += 1
        if abs(XN - XF) <= eps:
            converged = True
            break

        if n > 150:
            break

    if not converged:
        PMV_7730 = 999999
        PPD_7730 = 100
    else:
        tcl_7730 = 100 * XN - 273 # [°C]
    
        # heat loss components
        Edif_7730 = 3.05 * 0.001 * (5733 - 6.99 * MW_7730 - 1000 * Pa) # HL1
        if MW_7730 > 58.15:
            Ecomf = 0.42 * (MW_7730 - 58.15) # HL2
        else:
            Ecomf = 0

        Eres_7730 = 0.017 * Ms * (5.867 - Pa) # HL3
        Cres_7730 = 0.0014 * Ms * (34 - ta) # HL4
        Rad_7730 = 3.96 * FACL_7730 * (XN**4 - ((tr + 273) / 100)**4) # HL5
        Conv_7730 = FACL_7730 * hc_7730 * (tcl_7730 - ta) # 1994 # HL6
        Esw_7730 = MW_7730 - Edif_7730 - Ecomf - Cres_7730 - Eres_7730 - Rad_7730 - Conv_7730 + ERFS + Cdj
        # calculate PMV and PPD
        PMV_7730 = (0.303 * math.exp(-0.036 * Ms) + 0.028) * (Esw_7730)  
        PPD_7730 = 100 - 95 * math.exp(-0.03353 * PMV_7730**4 - 0.2179 * PMV_7730**2)


    #  ______ ETU - universal effective temperature ______
    # Nagano and Horikoshi (2011b)
    # Standard environment for ETU: 0.1m/s, 0clo
    hc_etu = 3 # [W/m2K]
    FCLE_etu = 1 # the effective clothing thermal efficiency in the standard environment
    hr_etu = 4.5
    hd_etu = 7.5 
    hu_etu = 7.5 # = (hco + hro) * Fcleo * fn + hdo * fcd
    FACL_etu = 1 # 1 + kclo * Iclo
    FPCL_etu = 1 / (1 + (0.155 / icl) * hc_etu * FACL_etu)

    f_ETU = lambda x: Qsk - hu_etu * (tsk - x) - LR * w * hc_etu * FPCL_etu * FACL_etu * fn * (Psks - pas(x) / 2)
    ETU = op.brentq(f_ETU, -100, 100)
    
    EATF_etu = (hc_etu + hr_etu) * FCLE_etu * fn * (ta - representative_temp) 
    TVF_etu = fn * (hc_etu * FCLE_etu - hc * FCLE) * (tsk - ta) 
    SERFL_etu = fn * (hr_etu * FCLE_etu * (tsk - ta) - hr * FCLE * (tsk - tr))
    SEHF_etu = LR * w * hc_etu * FPCL_etu * FACL_etu * fn * (Psks - pas(ETU) / 2) - LR * w * hc * FPCL * FACL * fn * (Psks - Pa)
    SECF_etu = hd_etu * fcd * (tsk - representative_temp) - Cdj

    # effective temperature differences from representative temperature [°C]
    theta_EATF_etu = EATF_etu / hu_etu      # Effective air temperature field
    theta_TVF_etu = TVF_etu / hu_etu        # Thermal velocity field
    theta_SERFL_etu = SERFL_etu / hu_etu    # Standard ERFL
    theta_ERFS_etu = ERFS / hu_etu          # Effective shortwave radiant field
    theta_SEHF_etu = SEHF_etu / hu_etu      # Standard EHF
    theta_SECF_etu = SECF_etu / hu_etu      # Standard effective conduction field


    #  ______ WCT_wind chill temperature ______
    # ISO 11079:2007
    Vel_wct = Vel_10 * 3.6 # [km/h]
    WCT = 13.12 + 0.6215 * ta - 11.37 * Vel_wct**0.16 + 0.3965 * ta * Vel_wct**0.16
    
    #  ______ WBGT ______
    # Ono and Tonouchi (2014)
    WBGT_Ono = 0.735 * ta + 0.0374 * RH + 0.00292 * ta * RH + 7.619 * Kd / 1000 - 4.557 * (Kd / 1000)**2 - 0.0572 * Vel - 4.064

    #  ______ UTCI ______
    """
    The following is based on the original FORTLAN program for approximating UTCI.
    The fortlan program - UTCI, Version a 0.002, October 2009, Copyright (C) 2009  Peter Broede - is publicly available at utci.org.
    """
    trtotal = ((tr + 273.15)**4 + ERFS / (elong * stefan * Ar_ratio * FCL))**0.25 - 273.15 # Mean radiant temperature including solar effect
    D_Tmrt = trtotal - ta
    UTCI_approx =(ta+		
        0.607562052	 + 
        -0.022771234 * ta + 
        0.00080647	 * ta*ta + 
        -0.000154271 * ta*ta*ta + 
        -3.24652e-06 * ta*ta*ta*ta + 
        7.32603e-08	 * ta*ta*ta*ta*ta + 
        1.35959e-09	 * ta*ta*ta*ta*ta*ta + 
        -2.2583652	 * Vel_10 + 
        0.088032604	 * ta*Vel_10 + 
        0.002168445	 * ta*ta*Vel_10 + 
        -1.53347e-05 * ta*ta*ta*Vel_10 + 
        -5.72984e-07 * ta*ta*ta*ta*Vel_10 + 
        -2.5509e-09	 * ta*ta*ta*ta*ta*Vel_10 + 
        -0.751269505 * Vel_10*Vel_10 + 
        -0.004083503 * ta*Vel_10*Vel_10 + 
        -5.21671e-05 * ta*ta*Vel_10*Vel_10 + 
        1.94545e-06	 * ta*ta*ta*Vel_10*Vel_10 + 
        1.141e-08	 * ta*ta*ta*ta*Vel_10*Vel_10 + 
        0.158137256	 * Vel_10*Vel_10*Vel_10 + 
        -6.57263e-05 * ta*Vel_10*Vel_10*Vel_10 + 
        2.22698e-07	 * ta*ta*Vel_10*Vel_10*Vel_10 + 
        -4.16117e-08 * ta*ta*ta*Vel_10*Vel_10*Vel_10 + 
        -0.012776275 * Vel_10*Vel_10*Vel_10*Vel_10 + 
        9.66892e-06	 * ta*Vel_10*Vel_10*Vel_10*Vel_10 + 
        2.52786e-09	 * ta*ta*Vel_10*Vel_10*Vel_10*Vel_10 + 
        0.000456307	 * Vel_10*Vel_10*Vel_10*Vel_10*Vel_10 + 
        -1.74203e-07 * ta*Vel_10*Vel_10*Vel_10*Vel_10*Vel_10 + 
        -5.91491e-06 * Vel_10*Vel_10*Vel_10*Vel_10*Vel_10*Vel_10 + 
        0.398374029	 * D_Tmrt + 
        0.000183945	 * ta*D_Tmrt + 
        -0.000173755 * ta*ta*D_Tmrt + 
        -7.60781e-07 * ta*ta*ta*D_Tmrt + 
        3.7783e-08	 * ta*ta*ta*ta*D_Tmrt + 
        5.4308e-10	 * ta*ta*ta*ta*ta*D_Tmrt + 
        -0.020051827 * Vel_10*D_Tmrt + 
        0.00089286	 * ta*Vel_10*D_Tmrt + 
        3.45433e-06	 * ta*ta*Vel_10*D_Tmrt + 
        -3.77926e-07 * ta*ta*ta*Vel_10*D_Tmrt + 
        -1.69699e-09 * ta*ta*ta*ta*Vel_10*D_Tmrt + 
        0.000169992	 * Vel_10*Vel_10*D_Tmrt + 
        -4.99204e-05 * ta*Vel_10*Vel_10*D_Tmrt + 
        2.47417e-07	 * ta*ta*Vel_10*Vel_10*D_Tmrt + 
        1.07596e-08	 * ta*ta*ta*Vel_10*Vel_10*D_Tmrt + 
        8.49243e-05	 * Vel_10*Vel_10*Vel_10*D_Tmrt + 
        1.35191e-06	 * ta*Vel_10*Vel_10*Vel_10*D_Tmrt + 
        -6.21531e-09 * ta*ta*Vel_10*Vel_10*Vel_10*D_Tmrt + 
        -4.9941e-06	 * Vel_10*Vel_10*Vel_10*Vel_10*D_Tmrt + 
        -1.89489e-08 * ta*Vel_10*Vel_10*Vel_10*Vel_10*D_Tmrt + 
        8.153e-08	 * Vel_10*Vel_10*Vel_10*Vel_10*Vel_10*D_Tmrt + 
        0.000755043	 * D_Tmrt*D_Tmrt + 
        -5.65095e-05 * ta*D_Tmrt*D_Tmrt + 
        -4.52167e-07 * ta*ta*D_Tmrt*D_Tmrt + 
        2.46689e-08	 * ta*ta*ta*D_Tmrt*D_Tmrt + 
        2.42674e-10	 * ta*ta*ta*ta*D_Tmrt*D_Tmrt + 
        0.000154547	 * Vel_10*D_Tmrt*D_Tmrt + 
        5.24111e-06	 * ta*Vel_10*D_Tmrt*D_Tmrt + 
        -8.75875e-08 * ta*ta*Vel_10*D_Tmrt*D_Tmrt + 
        -1.50743e-09 * ta*ta*ta*Vel_10*D_Tmrt*D_Tmrt + 
        -1.56236e-05 * Vel_10*Vel_10*D_Tmrt*D_Tmrt + 
        -1.33896e-07 * ta*Vel_10*Vel_10*D_Tmrt*D_Tmrt + 
        2.4971e-09	 * ta*ta*Vel_10*Vel_10*D_Tmrt*D_Tmrt + 
        6.51712e-07	 * Vel_10*Vel_10*Vel_10*D_Tmrt*D_Tmrt + 
        1.9496e-09	 * ta*Vel_10*Vel_10*Vel_10*D_Tmrt*D_Tmrt + 
        -1.00361e-08 * Vel_10*Vel_10*Vel_10*Vel_10*D_Tmrt*D_Tmrt + 
        -1.21207e-05 * D_Tmrt*D_Tmrt*D_Tmrt + 
        -2.18204e-07 * ta*D_Tmrt*D_Tmrt*D_Tmrt + 
        7.51269e-09	 * ta*ta*D_Tmrt*D_Tmrt*D_Tmrt + 
        9.79064e-11	 * ta*ta*ta*D_Tmrt*D_Tmrt*D_Tmrt + 
        1.25007e-06	 * Vel_10*D_Tmrt*D_Tmrt*D_Tmrt + 
        -1.81585e-09 * ta*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt + 
        -3.52198e-10 * ta*ta*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt + 
        -3.36515e-08 * Vel_10*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt + 
        1.35908e-10	 * ta*Vel_10*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt + 
        4.17033e-10	 * Vel_10*Vel_10*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt + 
        -1.30369e-09 * D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        4.13908e-10	 * ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        9.22652e-12	 * ta*ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        -5.0822e-09	 * Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        -2.24731e-11 * ta*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        1.17139e-10	 * Vel_10*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        6.62155e-10	 * D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        4.03863e-13	 * ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        1.95087e-12	 * Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        -4.73602e-12 * D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt + 
        5.12733497	 * Pa + 
        -0.312788561 * ta*Pa + 
        -0.019670186 * ta*ta*Pa + 
        0.000999691	 * ta*ta*ta*Pa + 
        9.51739e-06	 * ta*ta*ta*ta*Pa + 
        -4.66426e-07 * ta*ta*ta*ta*ta*Pa + 
        0.548050612	 * Vel_10*Pa + 
        -0.003305528 * ta*Vel_10*Pa + 
        -0.001641194 * ta*ta*Vel_10*Pa + 
        -5.16671e-06 * ta*ta*ta*Vel_10*Pa + 
        9.52692e-07	 * ta*ta*ta*ta*Vel_10*Pa + 
        -0.042922362 * Vel_10*Vel_10*Pa + 
        0.005008457	 * ta*Vel_10*Vel_10*Pa + 
        1.00601e-06	 * ta*ta*Vel_10*Vel_10*Pa + 
        -1.81749e-06 * ta*ta*ta*Vel_10*Vel_10*Pa + 
        -0.001258135 * Vel_10*Vel_10*Vel_10*Pa + 
        -0.00017933	 * ta*Vel_10*Vel_10*Vel_10*Pa + 
        2.34994e-06	 * ta*ta*Vel_10*Vel_10*Vel_10*Pa + 
        0.000129736	 * Vel_10*Vel_10*Vel_10*Vel_10*Pa + 
        1.29065e-06	 * ta*Vel_10*Vel_10*Vel_10*Vel_10*Pa + 
        -2.28559e-06 * Vel_10*Vel_10*Vel_10*Vel_10*Vel_10*Pa + 
        -0.036947635 * D_Tmrt*Pa + 
        0.001623253	 * ta*D_Tmrt*Pa + 
        -3.1428e-05	 * ta*ta*D_Tmrt*Pa + 
        2.59836e-06	 * ta*ta*ta*D_Tmrt*Pa + 
        -4.77137e-08 * ta*ta*ta*ta*D_Tmrt*Pa + 
        0.008642034	 * Vel_10*D_Tmrt*Pa + 
        -0.000687405 * ta*Vel_10*D_Tmrt*Pa + 
        -9.13864e-06 * ta*ta*Vel_10*D_Tmrt*Pa + 
        5.15917e-07	 * ta*ta*ta*Vel_10*D_Tmrt*Pa + 
        -3.59217e-05 * Vel_10*Vel_10*D_Tmrt*Pa + 
        3.28697e-05	 * ta*Vel_10*Vel_10*D_Tmrt*Pa + 
        -7.10542e-07 * ta*ta*Vel_10*Vel_10*D_Tmrt*Pa + 
        -1.24382e-05 * Vel_10*Vel_10*Vel_10*D_Tmrt*Pa + 
        -7.38584e-09 * ta*Vel_10*Vel_10*Vel_10*D_Tmrt*Pa + 
        2.20609e-07	 * Vel_10*Vel_10*Vel_10*Vel_10*D_Tmrt*Pa + 
        -0.000732469 * D_Tmrt*D_Tmrt*Pa + 
        -1.87382e-05 * ta*D_Tmrt*D_Tmrt*Pa + 
        4.80925e-06	 * ta*ta*D_Tmrt*D_Tmrt*Pa + 
        -8.75492e-08 * ta*ta*ta*D_Tmrt*D_Tmrt*Pa + 
        2.77863e-05	 * Vel_10*D_Tmrt*D_Tmrt*Pa + 
        -5.06005e-06 * ta*Vel_10*D_Tmrt*D_Tmrt*Pa + 
        1.14325e-07	 * ta*ta*Vel_10*D_Tmrt*D_Tmrt*Pa + 
        2.53017e-06	 * Vel_10*Vel_10*D_Tmrt*D_Tmrt*Pa + 
        -1.72857e-08 * ta*Vel_10*Vel_10*D_Tmrt*D_Tmrt*Pa + 
        -3.95079e-08 * Vel_10*Vel_10*Vel_10*D_Tmrt*D_Tmrt*Pa + 
        -3.59413e-07 * D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        7.04388e-07	 * ta*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        -1.89309e-08 * ta*ta*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        -4.79769e-07 * Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        7.9608e-09	 * ta*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        1.62897e-09	 * Vel_10*Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        3.94368e-08	 * D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        -1.18566e-09 * ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        3.34678e-10	 * Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        -1.15606e-10 * D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*Pa + 
        -2.80626406	 * Pa*Pa + 
        0.548712484	 * ta*Pa*Pa + 
        -0.003994284 * ta*ta*Pa*Pa + 
        -0.000954009 * ta*ta*ta*Pa*Pa + 
        1.93091e-05	 * ta*ta*ta*ta*Pa*Pa + 
        -0.308806365 * Vel_10*Pa*Pa + 
        0.011695236	 * ta*Vel_10*Pa*Pa + 
        0.000495272	 * ta*ta*Vel_10*Pa*Pa + 
        -1.90711e-05 * ta*ta*ta*Vel_10*Pa*Pa + 
        0.002107878	 * Vel_10*Vel_10*Pa*Pa + 
        -0.000698446 * ta*Vel_10*Vel_10*Pa*Pa + 
        2.30109e-05	 * ta*ta*Vel_10*Vel_10*Pa*Pa + 
        0.000417857	 * Vel_10*Vel_10*Vel_10*Pa*Pa + 
        -1.27044e-05 * ta*Vel_10*Vel_10*Vel_10*Pa*Pa + 
        -3.0462e-06	 * Vel_10*Vel_10*Vel_10*Vel_10*Pa*Pa + 
        0.051450742	 * D_Tmrt*Pa*Pa + 
        -0.00432511	 * ta*D_Tmrt*Pa*Pa + 
        8.99281e-05	 * ta*ta*D_Tmrt*Pa*Pa + 
        -7.14664e-07 * ta*ta*ta*D_Tmrt*Pa*Pa + 
        -0.000266016 * Vel_10*D_Tmrt*Pa*Pa + 
        0.00026379	 * ta*Vel_10*D_Tmrt*Pa*Pa + 
        -7.01199e-06 * ta*ta*Vel_10*D_Tmrt*Pa*Pa + 
        -0.000106823 * Vel_10*Vel_10*D_Tmrt*Pa*Pa + 
        3.61341e-06	 * ta*Vel_10*Vel_10*D_Tmrt*Pa*Pa + 
        2.29749e-07	 * Vel_10*Vel_10*Vel_10*D_Tmrt*Pa*Pa + 
        0.000304789	 * D_Tmrt*D_Tmrt*Pa*Pa + 
        -6.42071e-05 * ta*D_Tmrt*D_Tmrt*Pa*Pa + 
        1.16258e-06	 * ta*ta*D_Tmrt*D_Tmrt*Pa*Pa + 
        7.68023e-06	 * Vel_10*D_Tmrt*D_Tmrt*Pa*Pa + 
        -5.47447e-07 * ta*Vel_10*D_Tmrt*D_Tmrt*Pa*Pa + 
        -3.59938e-08 * Vel_10*Vel_10*D_Tmrt*D_Tmrt*Pa*Pa + 
        -4.36498e-06 * D_Tmrt*D_Tmrt*D_Tmrt*Pa*Pa + 
        1.68738e-07	 * ta*D_Tmrt*D_Tmrt*D_Tmrt*Pa*Pa + 
        2.67489e-08	 * Vel_10*D_Tmrt*D_Tmrt*D_Tmrt*Pa*Pa + 
        3.23927e-09	 * D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*Pa*Pa + 
        -0.035387412 * Pa*Pa*Pa + 
        -0.22120119	 * ta*Pa*Pa*Pa + 
        0.015512604	 * ta*ta*Pa*Pa*Pa + 
        -0.000263917 * ta*ta*ta*Pa*Pa*Pa + 
        0.045343346	 * Vel_10*Pa*Pa*Pa + 
        -0.004329439 * ta*Vel_10*Pa*Pa*Pa + 
        0.00014539	 * ta*ta*Vel_10*Pa*Pa*Pa + 
        0.000217509	 * Vel_10*Vel_10*Pa*Pa*Pa + 
        -6.66725e-05 * ta*Vel_10*Vel_10*Pa*Pa*Pa + 
        3.33217e-05	 * Vel_10*Vel_10*Vel_10*Pa*Pa*Pa + 
        -0.002269216 * D_Tmrt*Pa*Pa*Pa + 
        0.000380262	 * ta*D_Tmrt*Pa*Pa*Pa + 
        -5.45314e-09 * ta*ta*D_Tmrt*Pa*Pa*Pa + 
        -0.000796355 * Vel_10*D_Tmrt*Pa*Pa*Pa + 
        2.53458e-05	 * ta*Vel_10*D_Tmrt*Pa*Pa*Pa + 
        -6.31224e-06 * Vel_10*Vel_10*D_Tmrt*Pa*Pa*Pa + 
        0.000302122	 * D_Tmrt*D_Tmrt*Pa*Pa*Pa + 
        -4.77404e-06 * ta*D_Tmrt*D_Tmrt*Pa*Pa*Pa + 
        1.73826e-06	 * Vel_10*D_Tmrt*D_Tmrt*Pa*Pa*Pa + 
        -4.09088e-07 * D_Tmrt*D_Tmrt*D_Tmrt*Pa*Pa*Pa + 
        0.614155345	 * Pa*Pa*Pa*Pa + 
        -0.061675593 * ta*Pa*Pa*Pa*Pa + 
        0.001333748	 * ta*ta*Pa*Pa*Pa*Pa + 
        0.003553754	 * Vel_10*Pa*Pa*Pa*Pa + 
        -0.000513028 * ta*Vel_10*Pa*Pa*Pa*Pa + 
        0.00010245	 * Vel_10*Vel_10*Pa*Pa*Pa*Pa + 
        -0.001485264 * D_Tmrt*Pa*Pa*Pa*Pa + 
        -4.11469e-05 * ta*D_Tmrt*Pa*Pa*Pa*Pa + 
        -6.80434e-06 * Vel_10*D_Tmrt*Pa*Pa*Pa*Pa + 
        -9.77676e-06 * D_Tmrt*D_Tmrt*Pa*Pa*Pa*Pa + 
        0.088277311	 * Pa*Pa*Pa*Pa*Pa + 
        -0.003018593 * ta*Pa*Pa*Pa*Pa*Pa + 
        0.00104453	 * Vel_10*Pa*Pa*Pa*Pa*Pa + 
        0.000247091	 * D_Tmrt*Pa*Pa*Pa*Pa*Pa + 
        0.001483481	 * Pa*Pa*Pa*Pa*Pa*Pa 
    )
        
    results = dict(
        WCT=WCT,
        WBGT_Ono=WBGT_Ono,
        UTCI_approx=UTCI_approx,
        PMV_7730=PMV_7730,
        PPD_7730=PPD_7730,
        SETstar=SETstar, # = OET
        theta_EATF_oet=theta_EATF_oet,
        theta_TVF_oet=theta_TVF_oet,
        theta_SERFL_oet=theta_SERFL_oet,
        theta_ERFS_oet=theta_ERFS_oet,
        theta_SEHF_oet=theta_SEHF_oet,
        theta_SECF_oet=theta_SECF_oet,
        representative_temp=representative_temp,
        ETU=ETU,
        theta_EATF_etu=theta_EATF_etu,
        theta_TVF_etu=theta_TVF_etu,
        theta_SERFL_etu=theta_SERFL_etu,
        theta_ERFS_etu=theta_ERFS_etu,
        theta_SEHF_etu=theta_SEHF_etu,
        theta_SECF_etu=theta_SECF_etu,
    )
    return results
