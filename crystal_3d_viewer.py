# crystal_3d_viewer.py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pymatgen.core.structure import Structure
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.io.cif import CifParser

def view_3d_structure(cif_path):
    """Visualize crystal structure with CrystalNN bonding algorithm"""
    # Read CIF file
    parser = CifParser(cif_path)
    structure = parser.get_structures()[0]
    
    # Get CrystalNN bonding information
    cnn = CrystalNN()
    bonds = []
    for i, site in enumerate(structure):
        neighbors = cnn.get_nn_info(structure, i)
        for neighbor in neighbors:
            j = neighbor['site_index']
            if j > i:  # Avoid duplicate bonds
                bonds.append((i, j))
    
    # Get coordinates and elements
    coords = structure.cart_coords
    symbols = [site.species.elements[0].symbol for site in structure]
    
    # Create plot
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    # Element styling
    elem_style = {
        'Fe': {'color': 'red', 'size': 100},
        'O': {'color': 'blue', 'size': 80},
        'C': {'color': 'green', 'size': 60}
    }
    
    # Plot atoms
    for symbol in set(symbols):
        mask = np.array(symbols) == symbol
        style = elem_style.get(symbol, {'color': 'gray', 'size': 50})
        ax.scatter(coords[mask, 0], coords[mask, 1], coords[mask, 2],
                  c=style['color'],
                  s=style['size'],
                  label=symbol,
                  depthshade=False)
    
    # Plot bonds
    for i, j in bonds:
        ax.plot([coords[i][0], coords[j][0]],
                [coords[i][1], coords[j][1]],
                [coords[i][2], coords[j][2]],
                'k-', linewidth=1.5, alpha=0.6)
    
    # Set labels and legend
    ax.set_xlabel('X (Å)')
    ax.set_ylabel('Y (Å)')
    ax.set_zlabel('Z (Å)')
    ax.legend()
    
    plt.title(f"Structure: {cif_path.split('/')[-1]}")
    plt.show()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        view_3d_structure(sys.argv[1])
    else:
        print("Usage: python crystal_3d_viewer.py <CIF_FILE>")