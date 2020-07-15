import argparse
import json

import numpy as np

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Aquarium Solver.')
    parser.add_argument('filename', metavar='Setup_File', type=str,
                    help='(string) Name of the problem setup file')
    args = parser.parse_args()
    """ Load json parameters
        height:              Aquarium height [m]
        width:               Aquarium width [m]
        lenght:              Aquarium lenght [m]
        window_loss:         Heat loss in side Aquarium windows
        heater_a:            Heater A temperature [°C]
        heater_b:            Heater B temperature [°C]
        ambient_temperature: Ambient temperature of the aquarium [°C]
        filename:            file to save results [j/s]
    """
    with open(args.filename, 'r') as setup_file:
        config = json.load(setup_file)
    print(config)
    