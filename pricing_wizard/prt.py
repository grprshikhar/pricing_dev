# Importing required libraries
import pandas as pd
import itertools
import modules.gsheet as gsheet
from modules.options_handler import options_handler
from modules.print_utils import tabulate_dataframe, print_check, print_exclaim
import modules.gsheet as gsheet
import numpy as np
from modules.prt_dataframe import data_collector


#downloading the required data to build the dataframe needed
main_df = data_collector()

