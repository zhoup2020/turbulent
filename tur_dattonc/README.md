# Turbulence study based on meteorological tower observation data
This is a project that deals with the turbulence of meteorological tower research.
## Version
1.0.0
## Installation
To install the most recent development version in GitHub, run  
```pip install ```
## Requirements
This package has the following requirements:  
+ `numpy` and `scipy`  for numerical computations
+ `pandas` to read .dat files and numerical computations
+ `xarray` to save data to .nc files
+ `PyEMD` to implement EMD decomposition
+ `joblib` to parallel computing
+ `tkinter` to implement partial visualization   
See `requirements.txt` for details:  
```pip install -r requirements.txt```
## Usage example
See `test` for detail.  
+ The file `test/test1.py` is for calculating '$\Delta S$' and visualizing the profile of 
'$\Delta S$'.  
+ The file `test/test2.py` is intended to test an example of merging different .dat 
files to produce a .nc file.
+ The file `test/test3.py` is 
## Caveats and known limitations
+ File format restrictions:The program requires that the input file name must have 
a `.dat` or `.csv` suffix, and since we only used the `.dat` files automatically generated 
by our observation instrument, we did not test the program for csv file compatibility.
+ Data format restrictions:Because this project is dedicated to the processing of data 
observed by our observing instruments, the reading data part may not be universal. 
Therefore, the project requires that the input `.dat` file preferably contain the variables
`u, v, w, T, q, CO2`.
## Contact
Github:[zhoup2020](https://github.com/zhoup2020)  
Email:zhoup2020@outlook.com


