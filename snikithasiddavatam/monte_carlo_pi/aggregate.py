#!/usr/bin/env python3
#script that takes ap. individual job output files and combines them into a single dataset for analysis
import os
import re
from datetime import datetime

OUTPUT_DIR = "."           # Where output_*.txt files are
LOG_FILE   = "logs/mc_pi.log"
PI_REF     = 3.14159265358979323846

