import argparse
import json

import numpy as np

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Aquarium View.')
    parser.add_argument('filename', metavar='Setup_File', type=str,
                    help='(string) Name of the view setup file')
    args = parser.parse_args()
    """ Load json parameters
        filename: File to read aquarium temperature
        t_a :     Temperature prefered by fish A
        t_b :     Temperature prefered by fish B
        t_c :     Temperature prefered by fish C
        n_a :     Number of type A fish
        n_b :     Number of type B fish
        n_c :     Number of type C fish

    """
    with open(args.filename, 'r') as setup_file:
        config = json.load(setup_file)
    print(config)