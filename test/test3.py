from tur_dattonc import dat_nc
input_path = [f"G:/inldata/ecdata/{letter}{number}/ec_flux_20210427_0000.dat" for letter in ['C','B','A'] for number in range(4,0,-1)]
heights = [1.2,2.0,3.5,6.0,8.2,12.8,15.8,23.0,30.3,40.2,50.6,60.5]
variables = ['u', 'v', 'w', 't', 'water', 'CO2']
dat_nc(input_path,'2021-04-27',0.1,variables,heights,"C:/Users/xx/Desktop")