# multimeter
Keysight/Agilent 34410A Multimeter GUI

0. goto https://github.com/vadmu/multimeter -> Code -> download ZIP -> unpack

# How to configure the remote mode
1. Turn on the Multimeter
2. Set to the remote mode (Shift + Utility)
3. Open Keysight Connection Expert
4. Copy VISA Address to multimeter/visa_interface.py line 6

# How to run the code
1. https://docs.conda.io/en/latest/miniconda.html (include in the PATH = YES during installation)
2. run miniconda in the comand line interface (Win + R, type cmd)
3. "cd D:\..." to your code folder witn the file main.py
4. "conda env create -f environment.yml" takes several minutes to install all the libraries
5. "conda activate multimeter"
6. "python main.py"
