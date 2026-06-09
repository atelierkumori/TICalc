# TICalc

A GUI application for calculating comprehensive thermal indices, including ETU and OET.

---

## Table of Contents

- [TICalc](#ticalc)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Calculated Indices](#calculated-indices)
  - [Citation](#citation)
  - [Requirements](#requirements)
    - [macOS](#macos)
    - [Windows](#windows)
    - [Python (source)](#python-source)
  - [Installation](#installation)
    - [macOS](#macos-1)
    - [Windows](#windows-1)
    - [Python (Source)](#python-source-1)
  - [Preparing Your Data File](#preparing-your-data-file)
  - [Running the Application](#running-the-application)
  - [License](#license)

---

## Introduction

**TICalc** is a graphical application for calculating a comprehensive set of thermal comfort and thermal environment indices. It is designed for researchers and practitioners who need to evaluate outdoor and indoor thermal environments.

The application is particularly focused on two integrated indices — **ETU** (Universal Effective Temperature) and **OET** (Occupied Effective Temperature).

---

## Calculated Indices

| Index | Full Name | Reference |
|---|---|---|
| WCT | Wind Chill Temperature | ISO 11079 (2007) |
| WBGT | Wet Bulb Globe Temperature | Ono and Tonouchi (2014) |
| UTCI (approx.) | Universal Thermal Climate Index | Broede (2009) |
| PMV | Predicted Mean Vote | ISO 7730 (2005) |
| PPD | Predicted Percentage Dissatisfied | ISO 7730 (2005) |
| SET* | Standard Effective Temperature | Gagge et al. (1986) |
| ETU | Universal Effective Temperature | Nagano and Horikoshi (2011b) |
| OET | Occupied Effective Temperature | Nagano et al. (2020) |

> **References**
>
> - ASHRAE. 2013. ANSI/ASHRAE Standard 55-2013: Thermal environmental conditions for human occupancy. Atlanta (GA): ASHRAE.
> - ASHRAE. 2021. 2021 ASHRAE Handbook - Fundamentals (SI Edition). ASHRAE.
> - Broede P. 2009. The fortlan program - UTCI, Version a 0.002, Oct. 2009, Copyright (C) 2009 Peter Broede. https://utci.org
> - Fiala D, Havenith G, Bröde P, Kampmann B, Jendritzky G. 2012. UTCI-Fiala multi-node model of human heat transfer and temperature regulation. Int J Biometeorol. 56(3):429–441. https://doi.org/10.1007/s00484-011-0424-7
> - Fobelets APR, Gagge AP. 1988. Rationalization of the effective temperature ET*, as a measure of the enthalpy of the human indoor environment. ASHRAE Trans. 94(1):12–31
> - Gagge AP, Fobelets AP, Berglund LG. 1986. A standard predictive index of human response to the thermal environment. ASHRAE Trans. 92(2B):709–731
> - Gagge AP, Rapp GM, Hardy JD. 1967. The effective radiant field and operative temperature necessary for comfort with radiant heating. ASHRAE Trans. 73(I):I.2.1–I.2.9
> - Gagge AP, Stolwijk JAJ, Nishi Y. 1971. An effective temperature scale based on a simple model of human physiological regulatory response. ASHRAE Trans. 77:247–262
> - Havenith G, Fiala D, Błazejczyk K, Richards M, Bröde P, Holmér I, Rintamaki H, Benshabat Y, Jendritzky G. et al. 2012. The UTCI-clothing model. Int J Biometeorol. 56(3):461–470. https://doi.org/10.1007/s00484-011-0451-4
> - Horikoshi T, Kobayashi Y. 1985. Corrected humid operative temperature as an index of combined influences of thermal conditions upon the human body. Trans of AIJ. (355):12–19. https://doi.org/10.3130/aijax.355.0_12
> - Horikoshi T, Tsuchikawa T, Kurazumi Y, Matsubara N. 1995. Mathematical expression of combined and separate effect of air temperature, humidity, air velocity and thermal radiation on thermal comfort. ACES. 7(3–4):9–12
> - ISO. 2005. ISO 7730: 2005 Ergonomics of the thermal environment — Analytical determination and interpretation of thermal comfort using calculation of the PMV and PPD indices and local thermal comfort criteria.
> - ISO. 2007. ISO 11079: 2007 Ergonomics of the thermal environment — Determination and interpretation of cold stress when using required clothing insulation (IREQ) and local cooling effects.
> - Kuwabara K, Nagano K, Shimakura K, Mochida T. 2002. Experiments to determine the convective heat transfer coefficient of a thermal manikin. Environ Ergon X Eds Tochihara Y, Ohnaka T. 423–429
> - Nagano K, Horikoshi T. 2011a. Development of outdoor thermal index indicating universal and separate effects on human thermal comfort. Int J Biometeorol. 55(2):219–227. https://doi.org/10.1007/s00484-010-0327-z
> - Nagano K, Horikoshi T. 2011b. New index indicating the universal and separate effects on human comfort under outdoor and non-uniform thermal conditions. Energy Build. 43(7):1694–1701. https://doi.org/10.1016/j.enbuild.2011.03.012
> - Nagano K, Horikoshi T. 2016. Efficiency of index ETVO for evaluation of indoor thermal environment with and without solar radiation. In: The 14th International Conference of Indoor Air Quality and Climate (Indoor Air 2016). p 8
> - Nagano K, Shimura K, Mishima M, Inoue T, Kiriyama K, Sudo M, Horikoshi T. 2020. Effect of different asphalt pavement on pedestrians' heat stress. Jpn J Biometeor. 57(2):81–94. https://doi.org/10.11227/seikisho.57.81
> - Ono M, Tonouchi M. 2014. Estimation of wet-bulb globe temperature using generally measured meteorological indices. Jpn J Biometeorol. 50(4):147–157. https://doi.org/10.11227/seikisho.50.147
> - Reindl DT, Beckman WA, Duffie JA. 1990. Diffuse fraction correlations. Sol Energy. 45(1):1–7. https://doi.org/10.1016/0038-092X(90)90060-P
> - Siegel R. 1973. Net Radiation Method for Enclosure Systems Involving Partially Transparent Walls. NASA p 31. Report No.: TN D-7384.
> - Underwood CR, Ward EJ. 1966. The solar radiation area of man. Ergonomics. 9(2):155–168. https://doi.org/10.1080/00140136608964361

---

## Citation

**If you use the application:**

> Nagano K. 2026. TICalc: Thermal Indices Calculator \[Software\]. Zenodo. https://doi.org/10.5281/zenodo.20568842

**If you refer to the revised ETU/OET formulae:**

> Nagano K, Horikoshi T. 2026. ETU and OET: Thermal Indices for Integrated and Factor- and Segment-Resolved Evaluation. Zenodo. https://doi.org/10.5281/zenodo.20570988

The application is based on this revision. Therefore, if you use this application in your research, please cite both mentioned above.

**For the original theory, please cite the peer-reviewed publications:**

> Nagano K, Horikoshi T. 2011b. New index indicating the universal and separate effects on human comfort under outdoor and non-uniform thermal conditions. Energy Build. 43(7):1694–1701. https://doi.org/10.1016/j.enbuild.2011.03.012
> 
> Nagano K, Shimura K, Mishima M, Inoue T, Kiriyama K, Sudo M, Horikoshi T. 2020. Effect of different asphalt pavement on pedestrians' heat stress. Jpn J Biometeor. 57(2):81–94. https://doi.org/10.11227/seikisho.57.81

---

## Requirements

### macOS

| Item | Requirement |
|---|---|
| OS version | macOS 12 (Monterey) or later |
| Architecture | Apple Sillicon (arm64) only |
| Disk space | 157 MB |

### Windows

| Item | Requirement |
|---|---|
| OS version | Windows 10 (64-bit) or later |
| Disk space | 44 MB |

### Python (source)

| Item | Requirement |
|---|---|
| Python version | 3.9 or later |
| Key dependencies | FreeSimpleGUI 5.2.0+, openpyxl 3.1.5+, scipy 1.17.1+, pywin32 311+ (Windows only) |

---

## Installation

### macOS

1. Download `TICalc_mac.dmg` from the [Releases](https://github.com/atelierkumori/TICalc/releases) page.
2. Open the `TICalc_mac.dmg` file and drag **TICalc** into your Applications folder.
3. On first launch, right-click the app icon and choose **Open** to bypass Gatekeeper.

### Windows

1. Download `TICalc_win.zip` from the [Releases](https://github.com/atelierkumori/TICalc/releases) page and unzip it.
2. Place **TICalc** anywhere you like (e.g., Desktop or Documents).
3. If the app fails to launch, install [Visual C++ Redistributable](https://aka.ms/vc14/vc_redist.x64.exe) and try again.

### Python (Source)

1. Clone this repository.

```bash
git clone https://github.com/atelierkumori/TICalc.git
cd TICalc
```

2. Install the required packages.

```bash
pip install -r requirements.txt
```

3. **Windows users only:** Install an additional dependency:

```bash
pip install pywin32
```

4. Launch the application.

```bash
python src/main.py
```

---

## Preparing Your Data File

The app reads data from xls/xlsx format files and returns calculation results in the same sheet.
See [`template.xlsx`](https://github.com/atelierkumori/TICalc/template.xlsx) file.

> ⚠️ DO NOT change the sheet name "Data"

1. Set each item in the SETTINGS field (Lines 1 to 7) according to the data you want to evaluate.

   > ⚠️ DO NOT change the cell positions in the SETTINGS field.

   | Cell | Description |
   |------|-------------|
   | A2 | Solar radiation: select `Include` to account for solar radiation, or `Exclude` to ignore it |
   | A3, B3 | Latitude [°] — mandatory if A2 = `Include` |
   | A4, B4 | Longitude [°] — mandatory if A2 = `Include` |
   | A5 | UTC offset: Coordinated Universal Time offset [h] |
   | A6 | Reflected solar radiation: select `Input directly` to enter values manually, or `Estimate by albedo` to calculate from albedo |
   | A7 | Albedo [-] — mandatory if A6 = `Estimate by albedo` |
   | G2 | Sky view factor at pyranometer [-] |
   | G3 | Reference wind height [m] (used for wind speed correction) |
   | G4 | Measured wind height [m] (anemometer installation height) |
   | G5 | Convective heat transfer coefficient formula: select `Kuwabara's formula`, or `Two-node model` |
   | G6 | Humidity metric: select `Relative humidity`, `Wet-bulb temp`, `Humidity ratio`, or `Vapor pressure` |
   | G7 | Longwave radiation: select `Mean radiant temp`, or `Ld and Lu` (upward/downward longwave irradiance) |
   | L2 | Contact area factor [-] — mandatory when accounting for conductive heat |
   | L3 | Physiological source: select `Input directly` to enter values manually, or `Two-node model` to predict |

2. Enter the data you want to evaluate from the 10th row onward in columns A to S. Required input items may change depending on the settings in the SETTINGS field.

   > ⚠️ DO NOT change the column headings (A8–S9), or the column order (A–S).

   | Field name | Unit | Description |
   |---|---|---|
   |A: `date` | ymd | Date |
   |B: `time` | h:m:s | Time |
   |C: `ta` | °C | Air temperature |
   |D: `Humidity metric` | * | depending on G6 |
   |E: `vel` | m/s | Wind velocity |
   |F: `Kd` | W/m<sup>2</sup> | Downward solar irradiance |
   |G: `Ku` | W/m<sup>2</sup> | Upward solar irradiance |
   |H: `Lu or tr` | * | Downward longwave irradiance or mean radiant temp., depending on G7 |
   |I: `Lu` | W/m<sup>2</sup> | Upward longwave radiation, depending on G7 |
   |J: `αcln` | - | Net solar absorptance of cloth(s) |
   |K: `αskn` | - | Net solar absorptance of skin |
   |L: `clo` | clo | Clothing insulation |
   |M: `met` | met | Metabolic rate |
   |N: `representative air temperature` | °C | If blank, set to 0. |
   |O: `sky factor` | - | Enter the sky factor for the location where thermal indices are to be evaluated. Enter the same value as G2 when the location is the same as the pyranometer installation location. |
   |P: `Is the place shaded?` | y/n | Enter “y” to exclude direct solar radiation |
   |Q: `tsk` | °C | Skin temperature |
   |R: `wettedness` | - | Wettedness |
   |S: `Heat loss at contact surface` | W/m<sup>2</sup> | Heat loss at contact surface |

> A sample data is included in the [`template.xlsx`](https://github.com/atelierkumori/TICalc/template.xlsx).

---

## Running the Application

1. Launch **TICalc**.
2. Click **Browse** and select your template-based xls/xlsx file.
3. Close the file in Excel before proceeding.
4. Click **Run** to start the calculation.
5. The results of calculating the input data in columns A through S for each row of the file selected via **Browse** are displayed in columns W through AQ of the same row. If an error occurs, a message will appear in the box within the window.

<!-- Add a screenshot here once available:
![Screenshot of AppName](docs/screenshot.png)
-->

---

## License

This project is licensed under the [MIT License](https://github.com/atelierkumori/TICalc/LICENSE.txt).

Copyright (c) 2026 NAGANO Kazuo
