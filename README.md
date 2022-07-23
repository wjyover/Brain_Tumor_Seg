# Brain_Tumor_Seg
# Description
Brain_Tumor_seg based the whole tumor (all tumor-related T2w signal abnormalities) and the tumor core (including contrast-enhanced and non-enhanced tumor, cystic change, necrosis) predictor with axial T2W images (slice thickness <5 mm).
# Installation
1. Install [nnU-Net](https://github.com/MIC-DKFZ/nnUNet) as described on their website.
2. Download [t2_whole.model](https://1drv.ms/u/s!Agu87mLKyliLhjixVepPZvOYGF-Z?e=b42WD3) and [t2_core.model](https://1drv.ms/u/s!Agu87mLKyliLhjlf9B4ZjxXpy-sB?e=m0jTrB)
# Usage
python predict_tumor.py
