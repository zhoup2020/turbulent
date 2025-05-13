# Description of a python-based turbulence analysis tool  
## 1.Software Introduction  
### Software Background  
This software is a turbulence analysis tool developed based on python language, which aims to solve the problems of meteorological data format conversion,
large-scale data analysis and tedious repetitive operations, and is suitable for the processing of observation data from gradient towers and meteorological 
station observation data. By analyzing the observation data (including wind speed, temperature, humidity and CO2 concentration), 
the software can decompose the turbulence signals from the data and further process them, which can provide strong technical support for the atmospheric boundary layer research,
wind energy assessment and environmental monitoring.  
### Key Features  
The core functions of this software include: file format conversion, using a precise file reading and writing method, the meteorological tower of different height layers of observation data with the suffix name of .dat file
can be merged and converted into a file with the suffix name of .netcdf. Correlation coefficient calculation, can write the correlation coefficient calculation results between two variables in the read data into the file. 
Quadrant analysis, including de-sliding window averaging and calculation of statistics characterizing the coherent structure of turbulence (ΔS, CEM, ICEM, etc.). EMD decomposition of turbulent signals, which decomposes the 
data into high and low frequency signals. Wavelet analysis, which calculates the wavelet analysis results of the turbulent signals.  
### Technical Advantages  
Using lightweight modular design , the bottom based on Python language , to achieve low resource consumption and high operational efficiency . Support Windows/macOS/Linux platform.  
### Intended Users
Researchers and data analysts with atmospheric science backgrounds, etc.
## Frequently Asked Questions  
File format problems, this software is based on meteorological tower observation data research for development, did not take into account all the file reading situation. If you encounter file format problems, you can directly modify the source code.  
## Technical Support  
Contact details:pzhou6804@gmail.com or zhoup2020@outlook.com
