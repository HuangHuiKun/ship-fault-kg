# Anonymised vibration, lubricant and availability dataset for multimodal condition-based maintenance of tugboat propulsion systems

Reserved dataset DOI: https://doi.org/10.5281/zenodo.20101612

This Zenodo package supports the manuscript:

**Vibration-led multimodal condition-based maintenance decision support for tugboat propulsion: an anonymised field case study**

## Version note

Final submission dataset package aligned with the manuscript after engine-family anonymisation, table renumbering, OMML equation cleanup and the brief AI-assisted-technologies declaration. The machine-readable SSS audit trail remains reconstructive for releasable representative cases. The public DOI will resolve after the Zenodo record is published; during peer review, a private Zenodo preview link can be supplied through confidential Editorial Manager comments.

## Purpose

The package provides anonymised supporting material for an integrated multimodal condition-based maintenance (IM-CBM) framework applied to coastal tugboat propulsion systems. The files preserve engine-family case traceability while removing vessel names and vessel codes, operator identity, port schedules, raw point-level FFT arrays tied to proprietary routes and commercially sensitive availability or contract records.

## Main contents

```text
data/
  table1_propulsion_architecture_anonymised.csv
  table2_oil_cross_validation_anonymised.csv
  table3_lti_by_fault_type_anonymised.csv
  table4_diagnostic_zones_economics.csv
  table4A_sensitivity_checks.csv
  measurement_counts.csv
  representative_fft_features_anonymised.csv
  sss_formula_parameters.csv
  sss_ht_regression_summary.csv
  case_level_metadata_and_sss_examples.csv
figures/
  Figure_1_IM_CBM_Framework.png
  Figure_2_SSS_Heatmap.png
  Figure_3_Representative_FFT_Spectra.png
  Figure_4_Harmonic_Order_Analysis.png
  Figure_5_Lead_Time_Analysis.png
  Figure_6_SSS_vs_Unavailability.png
  Figure_7_Diagnostic_Matrix_and_Economic_Screening.png
  Graphical_Abstract_Key_Findings.png
code/
  summarise_dataset.py
  generate_zone_cost_plot.py
  requirements.txt
metadata/
  figure_manifest.csv
  data_dictionary.csv
  zenodo_metadata_template.json
  upload_form_values_for_zenodo.txt
licenses/
  LICENSE_CODE_MIT.txt
  LICENSE_DATA_CC_BY_4_0.txt
restricted_raw_fft_note/
  README_raw_fft_restrictions.md
```

## Important note about raw point-level FFT arrays

Raw point-level FFT arrays are withheld under confidentiality and data-ownership restrictions. The package provides anonymised representative spectral features, processed severity scores, cross-reference variables, figures, scripts and diagnostic notes sufficient to reproduce the reported summary-level analyses without disclosing vessel-identifying data.

## Anonymisation

Original vessel names were replaced by engine-family case labels derived from the propulsion engine family such as CAT C7, CAT 3516C and CAT 3508B/C families. Commercially sensitive vessel names, operator identity, port schedules and contract-specific point-level availability records are withheld under confidentiality agreements.

## How to run the code

```bash
pip install -r code/requirements.txt
python code/summarise_dataset.py
python code/generate_zone_cost_plot.py
```

## Suggested citation

Herrera Suárez, M.; Marcillo, R. A.; Torres, R. M.; Pérez Guerrero, J. N. (2026). Anonymised vibration, lubricant and availability dataset for multimodal condition-based maintenance of tugboat propulsion systems. Zenodo. DOI: 10.5281/zenodo.20101612.

## Contact

Corresponding author: Miguel Herrera Suárez, Universidad Técnica de Manabí, miguel.herrera@utm.edu.ec
