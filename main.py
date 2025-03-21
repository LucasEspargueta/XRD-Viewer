import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from pymatgen.core.structure import Structure
from pymatgen.analysis.diffraction.xrd import XRDCalculator
import subprocess

class PowderDiffractionViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("XRD Viewer Free")
        self.root.geometry("1400x900")
        
        # Initialize variables
        self.files = []
        self.spectra = {}
        self.wavelength = 1.5406  # Cu K-alpha
        self.sigma = 0.04  # Peak broadening (degrees)
        self.theta_range = [10, 90]
        self.step = 0.02
        
        # Create GUI components
        self.create_widgets()
        self.setup_plot()
        
    def view_3d_structure(self):
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a CIF file first")
            return
    
        try:
            cif_path = self.files[selected[0]]
            subprocess.Popen(["python", "crystal_3d_viewer.py", cif_path])
        except Exception as e:
            messagebox.showerror("Error", f"3D visualization failed:\n{str(e)}")    
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Range settings
        range_frame = ttk.LabelFrame(control_frame, text="2θ Range Settings", padding=5)
        range_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(range_frame, text="Start (°):").grid(row=0, column=0, sticky=tk.W)
        self.start_entry = ttk.Entry(range_frame, width=8)
        self.start_entry.insert(0, "10")
        self.start_entry.grid(row=0, column=1, padx=2)
        
        ttk.Label(range_frame, text="End (°):").grid(row=1, column=0, sticky=tk.W)
        self.end_entry = ttk.Entry(range_frame, width=8)
        self.end_entry.insert(0, "90")
        self.end_entry.grid(row=1, column=1, padx=2)
        
        ttk.Label(range_frame, text="Step (°):").grid(row=2, column=0, sticky=tk.W)
        self.step_entry = ttk.Entry(range_frame, width=8)
        self.step_entry.insert(0, "0.04")
        self.step_entry.grid(row=2, column=1, padx=2)
        
        ttk.Button(range_frame, text="Apply Range", 
                 command=self.update_theta_range).grid(row=3, column=0, columnspan=2, pady=5)
        
        # File management
        file_frame = ttk.LabelFrame(control_frame, text="CIF Files", padding=5)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_list = tk.Listbox(file_frame, height=15, selectmode=tk.MULTIPLE)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_files).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Plot area
        plot_frame = ttk.Frame(main_frame)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Toolbar with checkboxes
        self.toolbar = ttk.Frame(plot_frame)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        advanced_btn = ttk.Button(self.toolbar, text="Advanced Settings",
                                command=self.show_advanced_settings)
        advanced_btn.pack(side=tk.RIGHT, padx=5)
        
        # 3D structure button
        #ttk.Button(btn_frame, text="View 3D Structure", 
        #  command=self.view_3d_structure).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
    def setup_plot(self):
        self.ax.set_xlabel("2θ (degrees)", fontsize=12)
        self.ax.set_ylabel("Intensity (a.u.)", fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.fig.tight_layout()
        
    def show_advanced_settings(self):
        """Dialog for advanced parameters"""
        adv = tk.Toplevel(self.root)
        adv.title("Advanced Settings")
        
        ttk.Label(adv, text="Wavelength (Å):").grid(row=0, column=0)
        wl_entry = ttk.Entry(adv)
        wl_entry.insert(0, str(self.wavelength))
        wl_entry.grid(row=0, column=1)
        
        ttk.Label(adv, text="Peak Broadening (°):").grid(row=1, column=0)
        sigma_entry = ttk.Entry(adv)
        sigma_entry.insert(0, str(self.sigma))
        sigma_entry.grid(row=1, column=1)
        
        def apply_settings():
            self.wavelength = float(wl_entry.get())
            self.sigma = float(sigma_entry.get())
            if self.files:
                self.redraw_all_patterns()
            adv.destroy()
            
        ttk.Button(adv, text="Apply", command=apply_settings).grid(row=2, columnspan=2)
    
    def redraw_all_patterns(self):
        """Recompute all patterns with new settings"""
        current_files = self.files.copy()
        self.clear_files()
        self.files = current_files
        self.process_files(current_files)
        
    def update_theta_range(self):
        try:
            new_start = float(self.start_entry.get())
            new_end = float(self.end_entry.get())
            new_step = float(self.step_entry.get())
            
            if new_start >= new_end:
                raise ValueError("Start angle must be less than end angle")
            if new_step <= 0:
                raise ValueError("Step size must be positive")
            
            self.theta_range = [new_start, new_end]
            self.step = new_step
            
            # Reprocess all files with new settings
            if self.files:
                current_files = self.files.copy()
                self.clear_files()
                self.files = current_files
                self.process_files(current_files)
                
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            self.reset_range_entries()
            
    def reset_range_entries(self):
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, str(self.theta_range[0]))
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, str(self.theta_range[1]))
        self.step_entry.delete(0, tk.END)
        self.step_entry.insert(0, str(self.step))
        
    def add_files(self):
        new_files = filedialog.askopenfilenames(filetypes=[("CIF Files", "*.cif")])
        if new_files:
            self.files.extend(new_files)
            self.update_file_list()
            self.process_files(new_files)
            
    def remove_selected_files(self):
        selected = self.file_list.curselection()
        if selected:
            # Remove in reverse order to preserve indices
            for idx in reversed(selected):
                path = self.files[idx]
                if path in self.spectra:
                    # Remove checkbox
                    self.spectra[path]['checkbox'].destroy()
                    del self.spectra[path]
                del self.files[idx]
            self.update_file_list()
            self.redraw_plot()
            
    def clear_files(self):
        # Destroy all checkboxes and clear data
        for path in list(self.spectra.keys()):
            self.spectra[path]['checkbox'].destroy()
            del self.spectra[path]
        self.files = []
        self.update_file_list()
        self.clear_plot()
        
    def update_file_list(self):
        self.file_list.delete(0, tk.END)
        for f in self.files:
            self.file_list.insert(tk.END, os.path.basename(f))
            
    def process_files(self, filepaths):
        """Process files with pymatgen-based calculation"""
        for path in filepaths:
            try:
                two_theta, intensities, _ = self.calculate_peaks(path)
                x, y = self.generate_pattern(two_theta, intensities)
                self.add_spectrum(path, x, y)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {os.path.basename(path)}:\n{str(e)}")
                
    def calculate_peaks(self, cif_path):
        """Calculate XRD pattern using pymatgen's accurate XRD calculator"""
        try:
            structure = Structure.from_file(cif_path)
            calculator = XRDCalculator(wavelength=self.wavelength)
            pattern = calculator.get_pattern(structure, scaled=True)
            return pattern.x, pattern.y, pattern.hkls
            
        except Exception as e:
            messagebox.showerror("Calculation Error", 
                               f"Failed to calculate pattern:\n{str(e)}")
            raise
    
    def generate_pattern(self, two_theta, intensities):
        """Generate continuous pattern with proper peak shape"""
        theta = np.linspace(self.theta_range[0], self.theta_range[1], 
                          int((self.theta_range[1]-self.theta_range[0])/self.step))
        pattern = np.zeros_like(theta)
        
        # Pseudo-Voigt peak profile
        for angle, intensity in zip(two_theta, intensities):
            if self.theta_range[0] <= angle <= self.theta_range[1]:
                sigma = self.sigma / (2*np.sqrt(2*np.log(2)))  # Convert to Gaussian sigma
                lor = intensity * (1/(1 + ((theta - angle)/sigma)**2))
                gau = intensity * np.exp(-((theta - angle)/sigma)**2)
                pattern += 0.5*lor + 0.5*gau  # Pseudo-Voigt mix
                
        return theta, pattern/np.max(pattern)
    
    def add_spectrum(self, path, x, y):
        color = plt.cm.tab10(len(self.spectra) % 10)
        line, = self.ax.plot(x, y, lw=1.5, alpha=0.8, 
                            color=color, label=os.path.basename(path))
        
        var = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(self.toolbar, 
                            text=os.path.basename(path),
                            variable=var,
                            command=self.toggle_spectrum)
        cb.pack(side=tk.LEFT, padx=5)
        
        self.spectra[path] = {
            'line': line,
            'var': var,
            'checkbox': cb,
            'color': color
        }
        
        self.update_plot()
        
    def toggle_spectrum(self):
        for path, spec in self.spectra.items():
            visible = spec['var'].get()
            spec['line'].set_visible(visible)
        self.canvas.draw_idle()
        
    def clear_plot(self):
        self.ax.clear()
        self.setup_plot()
        self.canvas.draw()
        
    def redraw_plot(self):
        self.clear_plot()
        for path in self.files:
            if path in self.spectra:
                x = self.spectra[path]['line'].get_xdata()
                y = self.spectra[path]['line'].get_ydata()
                line, = self.ax.plot(x, y, lw=1.5, alpha=0.8,
                                   color=self.spectra[path]['color'])
                self.spectra[path]['line'] = line
        self.update_plot()
        
    def update_plot(self):
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = PowderDiffractionViewer(root)
    root.mainloop()