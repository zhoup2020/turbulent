# Description of a python-based turbulence analysis tool  
## 1.Software Introduction  
### Software Background  
This software is a turbulence analysis tool developed based on python language, which aims to solve the problems of meteorological data format conversion,
large-scale data analysis and tedious repetitive operations, and is suitable for the processing of observation data from gradient towers and meteorological 
station observation data. By analyzing the observation data (including wind speed, temperature, humidity and CO2 concentration), 
the software can decompose the turbulence signals from the data and further process them, which can provide strong technical support for the atmospheric boundary layer research,
wind energy assessment and environmental monitoring. This project is for educational/learning purposes only.
### Key Features  
The core functions of this software include: file format conversion, using a precise file reading and writing method, the meteorological tower of different height layers of observation data with the suffix name of .dat file
can be merged and converted into a file with the suffix name of .netcdf. Correlation coefficient calculation, can write the correlation coefficient calculation results between two variables in the read data into the file. 
Quadrant analysis, including de-sliding window averaging and calculation of statistics characterizing the coherent structure of turbulence (ΔS, CEM, ICEM, etc.). EMD decomposition of turbulent signals, which decomposes the 
data into high and low frequency signals. Wavelet analysis, which calculates the wavelet analysis results of the turbulent signals.  
### Technical Advantages  
Using lightweight modular design , the bottom based on Python language , to achieve low resource consumption and high operational efficiency . Support Windows/macOS/Linux platform.  
### Intended Users
Researchers and data analysts with atmospheric science backgrounds, etc.  
## 2.Module Introduction  
The gui_design module is used to create the GUI page, the icons module is the icon elements called in the GUI page, the test module is used to test part of the functionality of the tur_dattonc module, and the tur_dattonc module is responsible for the basic code framework for processing the data.  
## 3.Frequently Asked Questions  
File format problems, this software is based on meteorological tower observation data research for development, did not take into account all the file reading situation. If you encounter file format problems, you can directly modify the source code.  
## 4.Technical Support  
Contact details:pzhou6804@gmail.com or zhoup2020@outlook.com  
Author：Ping Zhou  
Supervisor：Zhongming Gao
## 5.Resource Usage Statement   
Some of the icons/materials used in this project are sourced from the Pixso platform and are subject to the following terms:  
### License  
The material is licensed under a Creative Commons Attribution 4.0 International License (https://pixso.cn/help/guide/40/1672831237851416?menu=base) and you are free to:  
Share: copy and distribute the material;  
Modify: create secondary works based on the material.    
### Attribution requirements
Usage must be clearly labeled:  
Source: coming from “Pixso” (https://pixso.cn/community/file/GzF87zsI9TG7I7s2qAVnZQ); author:Kilbert   
Link to the protocol: CC BY 4.0 protocol(https://creativecommons.org/licenses/by/4.0/deed.en);   
### Restrictions on use  
Pixso platform resources can only be used for learning and communication purposes, and are prohibited to be used:
Direct commercial sales or for-profit products;Scenes not related to learning, open source, non-profit.  
### Disclaimer
The icons/materials in this project are not directly related to the Pixso platform, and Pixso is not responsible for their usage scenarios.
