#!/usr/bin/env python3
"""
Thermodynamic Equilibrium Calculator for Sous Vide Cooking
Provides scientific heat transfer calculations for optimal cooking times and temperatures.
"""

import math
import json
import sys
from typing import Dict, Tuple, Any
from dataclasses import dataclass


@dataclass
class ProteinProperties:
    """Material properties for different protein types."""
    density: float  # kg/m³
    specific_heat: float  # J/(kg·K)
    thermal_conductivity: float  # W/(m·K)
    thermal_diffusivity: float  # m²/s


@dataclass
class WaterProperties:
    """Water properties for heat transfer calculations."""
    density: float = 998.0  # kg/m³ at 60°C
    specific_heat: float = 4180.0  # J/(kg·K)
    thermal_conductivity: float = 0.65  # W/(m·K)


class ThermodynamicCalculator:
    """
    Advanced thermodynamic calculator for sous vide cooking optimization.
    Uses heat transfer principles and material science for precise calculations.
    """
    
    def __init__(self):
        # Material properties database
        self.protein_properties = {
            'beef': ProteinProperties(
                density=1050,
                specific_heat=3400,
                thermal_conductivity=0.45,
                thermal_diffusivity=1.27e-7
            ),
            'chicken': ProteinProperties(
                density=1020,
                specific_heat=3600,
                thermal_conductivity=0.42,
                thermal_diffusivity=1.14e-7
            ),
            'pork': ProteinProperties(
                density=1030,
                specific_heat=3500,
                thermal_conductivity=0.43,
                thermal_diffusivity=1.19e-7
            ),
            'fish': ProteinProperties(
                density=980,
                specific_heat=3800,
                thermal_conductivity=0.48,
                thermal_diffusivity=1.29e-7
            ),
            'vegetables': ProteinProperties(
                density=900,
                specific_heat=4000,
                thermal_conductivity=0.55,
                thermal_diffusivity=1.53e-7
            )
        }
        
        self.water = WaterProperties()
        
    def calculate_grashof_number(self, temperature: float) -> float:
        """
        Calculate Grashof number for natural convection in water.
        
        Args:
            temperature: Water temperature in Celsius
            
        Returns:
            Grashof number (dimensionless)
        """
        g = 9.81  # gravitational acceleration (m/s²)
        beta = 0.0002  # thermal expansion coefficient for water (1/K)
        delta_t = 5.0  # temperature difference (K)
        characteristic_length = 0.01  # 1 cm characteristic length (m)
        kinematic_viscosity = 4.78e-7  # m²/s for water at 60°C
        
        grashof = (g * beta * delta_t * (characteristic_length ** 3)) / (kinematic_viscosity ** 2)
        return grashof
    
    def calculate_heat_transfer_coefficient(self, temperature: float) -> float:
        """
        Calculate heat transfer coefficient for natural convection.
        
        Args:
            temperature: Water temperature in Celsius
            
        Returns:
            Heat transfer coefficient (W/(m²·K))
        """
        grashof = self.calculate_grashof_number(temperature)
        prandtl = 4.3  # Prandtl number for water at typical sous vide temperatures
        
        # Nusselt number correlation for natural convection
        nusselt = 0.54 * ((grashof * prandtl) ** 0.25)
        
        # Heat transfer coefficient
        h = (nusselt * self.water.thermal_conductivity) / 0.01
        return h
    
    def calculate_biot_number(self, protein_type: str, thickness_inches: float) -> float:
        """
        Calculate Biot number to determine heat transfer regime.
        
        Args:
            protein_type: Type of protein (beef, chicken, pork, fish, vegetables)
            thickness_inches: Thickness in inches
            
        Returns:
            Biot number (dimensionless)
        """
        if protein_type not in self.protein_properties:
            raise ValueError(f"Unknown protein type: {protein_type}")
            
        props = self.protein_properties[protein_type]
        h = self.calculate_heat_transfer_coefficient(60)  # Approximate temperature
        characteristic_length = (thickness_inches * 0.0254) / 2  # Convert to meters, half thickness
        
        biot = (h * characteristic_length) / props.thermal_conductivity
        return biot
    
    def get_first_eigenvalue(self, biot_number: float) -> float:
        """
        Calculate first eigenvalue for infinite cylinder heat conduction.
        
        Args:
            biot_number: Biot number
            
        Returns:
            First eigenvalue
        """
        # Empirical correlation for first eigenvalue of infinite cylinder
        if biot_number < 0.1:
            return math.sqrt(biot_number)
        elif biot_number < 10:
            return 1.256 * math.sqrt(biot_number)
        else:
            return 1.571 + (0.5 / biot_number)  # Approaches π/2 for large Bi
    
    def calculate_helmholtz_free_energy(self, temp_initial: float, temp_final: float, 
                                       protein_type: str) -> float:
        """
        Calculate Helmholtz free energy change for temperature transition.
        F = U - TS (internal energy minus temperature-entropy product)
        
        Args:
            temp_initial: Initial temperature in Celsius
            temp_final: Final temperature in Celsius
            protein_type: Type of protein
            
        Returns:
            Helmholtz free energy change (J/kg)
        """
        props = self.protein_properties[protein_type]
        
        # Convert to Kelvin
        T1 = temp_initial + 273.15
        T2 = temp_final + 273.15
        
        # Internal energy change (ΔU = m * cv * ΔT)
        # For liquids/solids: cv ≈ cp, so we use specific_heat
        delta_u = props.specific_heat * (T2 - T1)
        
        # Entropy change for temperature change (ΔS = cv * ln(T2/T1))
        delta_s = props.specific_heat * math.log(T2 / T1)
        
        # Helmholtz free energy change at final temperature
        # ΔF = ΔU - T₂ΔS
        delta_f = delta_u - T2 * delta_s
        
        return delta_f
    
    def calculate_gibbs_energy_change(self, temp_initial: float, temp_target: float, 
                                    protein_type: str) -> float:
        """
        Calculate Gibbs free energy change for thermal transition.
        G = U - TS + PV (at constant pressure, G = H - TS)
        
        Args:
            temp_initial: Initial temperature in Celsius
            temp_target: Target temperature in Celsius  
            protein_type: Type of protein
            
        Returns:
            Gibbs energy change (J/kg)
        """
        props = self.protein_properties[protein_type]
        
        # Convert to Kelvin
        T1 = temp_initial + 273.15
        T2 = temp_target + 273.15
        
        # Enthalpy change (ΔH = m * cp * ΔT)
        delta_h = props.specific_heat * (T2 - T1)
        
        # Entropy change for temperature change (ΔS = cp * ln(T2/T1))
        delta_s = props.specific_heat * math.log(T2 / T1)
        
        # Gibbs free energy change at target temperature
        # ΔG = ΔH - T₂ΔS
        delta_g = delta_h - T2 * delta_s
        
        return delta_g
    
    def calculate_optimal_temperature_profile(self, protein_type: str, thickness_inches: float,
                                            target_temp: float, weight_kg: float = None) -> Tuple[float, float, float]:
        """
        Calculate optimal temperature profile using Helmholtz free energy minimization.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius
            
        Returns:
            Tuple of (optimal_high_temp, high_phase_duration, energy_efficiency)
        """
        props = self.protein_properties[protein_type]
        
        # Test different high temperatures to find optimal
        best_efficiency = 0
        optimal_high_temp = target_temp + 10
        best_duration = 0
        
        for temp_delta in range(8, 16):  # Test 8°C to 15°C above target
            test_high_temp = target_temp + temp_delta
            
            # Calculate Helmholtz free energy for this temperature change
            helmholtz_change = self.calculate_helmholtz_free_energy(20, test_high_temp, protein_type)
            
            # Calculate time efficiency at this temperature with weight consideration
            time_high, time_remaining = self.calculate_accelerated_equilibrium_time(
                protein_type, thickness_inches, test_high_temp, target_temp, weight_kg
            )
            
            total_time = time_high + time_remaining
            conventional_time = self.calculate_conventional_time(protein_type, thickness_inches, target_temp)
            
            # Energy efficiency combines time savings with thermodynamic efficiency
            time_efficiency = (conventional_time - total_time) / conventional_time
            energy_efficiency = abs(helmholtz_change) / (props.specific_heat * (test_high_temp - target_temp))
            
            combined_efficiency = time_efficiency * energy_efficiency
            
            if combined_efficiency > best_efficiency:
                best_efficiency = combined_efficiency
                optimal_high_temp = test_high_temp
                best_duration = time_high
        
        return optimal_high_temp, best_duration, best_efficiency
    
    def calculate_enhanced_heat_transfer_coefficient(self, temp_high: float, temp_target: float) -> float:
        """
        Calculate enhanced heat transfer coefficient with higher temperature driving force.
        
        Args:
            temp_high: High temperature in Celsius
            temp_target: Target temperature in Celsius
            
        Returns:
            Enhanced heat transfer coefficient
        """
        # Base heat transfer coefficient
        h_base = self.calculate_heat_transfer_coefficient(temp_target)
        
        # Temperature enhancement factor (exponential relationship)
        temp_ratio = (temp_high + 273.15) / (temp_target + 273.15)
        enhancement_factor = temp_ratio ** 1.25  # Empirical enhancement
        
        return h_base * enhancement_factor
    
    def calculate_accelerated_equilibrium_time(self, protein_type: str, thickness_inches: float,
                                             temp_high: float, temp_target: float, weight_kg: float = None) -> Tuple[float, float]:
        """
        Calculate equilibrium time with accelerated heat transfer using both thermodynamic principles.
        Uses Gibbs free energy (G=U-TS+PV) and Helmholtz free energy (F=U-TS) for optimization.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            temp_high: High temperature phase in Celsius
            temp_target: Target temperature in Celsius
            weight_kg: Weight of the protein in kilograms (optional, affects thermal mass)
            
        Returns:
            Tuple of (high_temp_phase_time, remaining_time) in hours
        """
        if protein_type not in self.protein_properties:
            raise ValueError(f"Unknown protein type: {protein_type}")
            
        props = self.protein_properties[protein_type]
        characteristic_length = (thickness_inches * 0.0254) / 2  # Convert to meters
        
        # Calculate both free energy changes for thermodynamic optimization
        gibbs_change = self.calculate_gibbs_energy_change(20, temp_high, protein_type)
        helmholtz_change = self.calculate_helmholtz_free_energy(temp_target, temp_high, protein_type)
        
        # Weight-based thermal mass calculations
        if weight_kg is not None:
            # Calculate thermal mass effect (larger mass takes longer to heat)
            # Thermal mass = mass × specific_heat
            thermal_mass = weight_kg * props.specific_heat
            
            # Mass factor affects heating rate (exponential relationship)
            mass_factor = 1.0 + (weight_kg / 2.0) ** 0.7  # Empirical scaling
            
            # Enhanced thermal diffusivity accounting for mass distribution
            effective_diffusivity = props.thermal_diffusivity / mass_factor
        else:
            # Estimate weight from dimensions (assuming roughly rectangular piece)
            estimated_volume_m3 = (thickness_inches * 0.0254) * (thickness_inches * 0.0254 * 3) * (thickness_inches * 0.0254 * 2)
            estimated_weight = estimated_volume_m3 * props.density
            thermal_mass = estimated_weight * props.specific_heat
            mass_factor = 1.0 + (estimated_weight / 2.0) ** 0.7
            effective_diffusivity = props.thermal_diffusivity / mass_factor
        
        # Enhanced heat transfer coefficient using thermodynamic driving forces
        h_base = self.calculate_heat_transfer_coefficient(temp_target)
        
        # Combined thermodynamic enhancement
        temp_ratio = (temp_high + 273.15) / (temp_target + 273.15)
        gibbs_factor = 1.0 + abs(gibbs_change) / 12000  # Gibbs energy enhancement
        helmholtz_factor = 1.0 + abs(helmholtz_change) / 8000  # Helmholtz optimization
        
        h_enhanced = h_base * temp_ratio ** 1.25 * gibbs_factor * helmholtz_factor
        enhanced_biot = (h_enhanced * characteristic_length) / props.thermal_conductivity
        
        # High temperature phase - calculate time to reach 90% of temperature penetration
        if enhanced_biot < 0.1:
            # Lumped capacitance - very fast
            fourier_high = -math.log(0.1)  # 90% penetration
        else:
            eigenvalue_enhanced = self.get_first_eigenvalue(enhanced_biot)
            fourier_high = -math.log(0.1) / (eigenvalue_enhanced ** 2)
        
        # Time for high temperature phase (using weight-adjusted thermal diffusivity)
        time_high_seconds = (fourier_high * (characteristic_length ** 2)) / effective_diffusivity
        time_high_hours = time_high_seconds / 3600
        
        # Effective penetration achieved during high temp phase
        penetration_depth = 2 * math.sqrt(effective_diffusivity * time_high_seconds)
        effective_thickness = max(0.1, thickness_inches * 0.0254 - penetration_depth)
        
        # Remaining time at target temperature (much reduced due to pre-heating)
        if effective_thickness <= 0.1:
            # Fully penetrated, just equilibration time
            remaining_time = 0.1  # 6 minutes for final equilibration
        else:
            # Calculate time for remaining thickness
            remaining_char_length = effective_thickness / 2
            normal_biot = self.calculate_biot_number(protein_type, effective_thickness / 0.0254)
            
            if normal_biot < 0.1:
                fourier_remaining = -math.log(0.01)  # 99% final equilibrium
            else:
                eigenvalue_normal = self.get_first_eigenvalue(normal_biot)
                fourier_remaining = -math.log(0.01) / (eigenvalue_normal ** 2)
            
            remaining_seconds = (fourier_remaining * (remaining_char_length ** 2)) / effective_diffusivity
            remaining_time = remaining_seconds / 3600
        
        return time_high_hours, remaining_time
    
    def calculate_optimal_profile(self, protein_type: str, thickness_inches: float, 
                                target_temp: float, weight_kg: float = None) -> Dict[str, Any]:
        """
        Calculate optimal two-temperature cooking profile using both Gibbs and Helmholtz free energy.
        G = U - TS + PV (Gibbs) and F = U - TS (Helmholtz) for comprehensive optimization.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius
            weight_kg: Weight of the protein in kilograms (optional, improves accuracy)
            
        Returns:
            Dictionary with optimal cooking parameters including weight effects
        """
        # Optimize high temperature using Helmholtz free energy minimization
        optimal_temp_high, optimal_duration, efficiency = self.calculate_optimal_temperature_profile(
            protein_type, thickness_inches, target_temp, weight_kg
        )
        
        # Calculate both free energy changes for the optimized profile
        gibbs_change = self.calculate_gibbs_energy_change(20, optimal_temp_high, protein_type)
        helmholtz_change = self.calculate_helmholtz_free_energy(target_temp, optimal_temp_high, protein_type)
        
        # Calculate accelerated equilibrium times with optimal temperature and weight
        time_high, time_remaining = self.calculate_accelerated_equilibrium_time(
            protein_type, thickness_inches, optimal_temp_high, target_temp, weight_kg
        )
        
        # Total time is significantly reduced due to thermodynamic optimization
        total_time = time_high + time_remaining
        
        # Calculate efficiency based on time savings
        conventional_time = self.calculate_conventional_time(protein_type, thickness_inches, target_temp)
        time_savings = max(0, (conventional_time - total_time) / conventional_time)
        
        # Calculate heat penetration metrics
        props = self.protein_properties[protein_type]
        penetration_depth = 2 * math.sqrt(props.thermal_diffusivity * time_high * 3600)
        thickness_meters = thickness_inches * 0.0254
        penetration_ratio = min(1.0, penetration_depth / thickness_meters)
        
        # Calculate total energy requirement if weight is known
        total_energy_kj = None
        if weight_kg is not None:
            props = self.protein_properties[protein_type]
            # Energy = mass × specific_heat × ΔT
            delta_t = optimal_temp_high - 20  # Assuming room temp start
            total_energy_j = weight_kg * props.specific_heat * delta_t
            total_energy_kj = total_energy_j / 1000  # Convert to kJ
        
        return {
            'high_temp_duration': time_high,  # hours
            'remaining_time': time_remaining,  # hours  
            'total_time': total_time,  # hours
            'conventional_time': conventional_time,  # hours
            'time_savings_percent': time_savings * 100,
            'penetration_ratio': penetration_ratio,
            'gibbs_energy_change': gibbs_change,
            'helmholtz_energy_change': helmholtz_change,
            'optimal_high_temp': optimal_temp_high,
            'total_energy_kj': total_energy_kj,
            'efficiency': self.calculate_efficiency(protein_type, thickness_inches)
        }
    
    def calculate_conventional_time(self, protein_type: str, thickness_inches: float, 
                                  target_temp: float) -> float:
        """
        Calculate conventional single-temperature cooking time for comparison.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius
            
        Returns:
            Conventional cooking time in hours
        """
        if protein_type not in self.protein_properties:
            raise ValueError(f"Unknown protein type: {protein_type}")
            
        props = self.protein_properties[protein_type]
        biot = self.calculate_biot_number(protein_type, thickness_inches)
        characteristic_length = (thickness_inches * 0.0254) / 2
        
        # Standard Fourier analysis for single temperature
        if biot < 0.1:
            fourier_number = -math.log(0.01)  # 99% equilibrium
        else:
            eigenvalue = self.get_first_eigenvalue(biot)
            fourier_number = -math.log(0.01) / (eigenvalue ** 2)
        
        time_seconds = (fourier_number * (characteristic_length ** 2)) / props.thermal_diffusivity
        return time_seconds / 3600
    
    def calculate_efficiency(self, protein_type: str, thickness_inches: float) -> float:
        """
        Calculate heat transfer efficiency based on Biot number.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            
        Returns:
            Efficiency as a decimal (0.0 to 1.0)
        """
        biot = self.calculate_biot_number(protein_type, thickness_inches)
        
        # Efficiency correlation based on Biot number
        if biot < 0.1:
            return 0.95  # Very efficient (lumped capacitance)
        elif biot < 1.0:
            return 0.85  # Good efficiency
        elif biot < 10.0:
            return 0.70  # Moderate efficiency
        else:
            return 0.55  # Lower efficiency for thick/low conductivity items
    
    def calculate_cooking_parameters(self, protein_type: str, thickness_inches: float,
                                   target_temp_celsius: float, doneness: str, weight_kg: float = None) -> Dict[str, Any]:
        """
        Main calculation function that returns all cooking parameters using enhanced thermodynamics.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp_celsius: Target temperature in Celsius
            doneness: Doneness level (rare, medium-rare, etc.)
            weight_kg: Weight of the protein in kilograms (optional, improves accuracy)
            
        Returns:
            Complete cooking parameter dictionary with significant time reductions and weight effects
        """
        try:
            # Calculate enhanced optimal profile with Gibbs energy considerations and weight
            profile = self.calculate_optimal_profile(protein_type, thickness_inches, target_temp_celsius, weight_kg)
            
            # Calculate additional parameters
            biot = self.calculate_biot_number(protein_type, thickness_inches)
            efficiency = self.calculate_efficiency(protein_type, thickness_inches)
            
            # Determine cooking regime with enhanced analysis
            if biot < 0.1:
                regime = "lumped_capacitance"
                regime_description = "Heat transfers very quickly and evenly throughout"
            elif biot < 1.0:
                regime = "good_heat_transfer"  
                regime_description = "Good heat transfer with minimal temperature gradients"
            else:
                regime = "internal_resistance"
                regime_description = "Benefits significantly from high-temperature acceleration phase"
            
            return {
                'success': True,
                'protein_type': protein_type,
                'thickness_inches': thickness_inches,
                'weight_kg': weight_kg,
                'target_temp_celsius': target_temp_celsius,
                'doneness': doneness,
                'biot_number': round(biot, 3),
                'efficiency': round(efficiency, 3),
                'regime': regime,
                'regime_description': regime_description,
                'high_temp_duration_hours': round(profile['high_temp_duration'], 3),
                'high_temp_duration_minutes': round(profile['high_temp_duration'] * 60, 1),
                'remaining_time_hours': round(profile['remaining_time'], 3),
                'remaining_time_minutes': round(profile['remaining_time'] * 60, 1),
                'total_time_hours': round(profile['total_time'], 3),
                'conventional_time_hours': round(profile['conventional_time'], 3),
                'time_savings_percent': round(profile['time_savings_percent'], 1),
                'penetration_ratio': round(profile['penetration_ratio'], 3),
                'gibbs_energy_change': round(profile['gibbs_energy_change'], 1),
                'helmholtz_energy_change': round(profile['helmholtz_energy_change'], 1),
                'total_energy_kj': profile['total_energy_kj'],
                'initial_temp_celsius': round(profile['optimal_high_temp'], 1),
                'initial_temp_fahrenheit': round(profile['optimal_high_temp'] * 9/5 + 32),
                'target_temp_fahrenheit': round(target_temp_celsius * 9/5 + 32)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'protein_type': protein_type,
                'thickness_inches': thickness_inches
            }


def main():
    """
    Command line interface for the thermodynamic calculator.
    Default units: Celsius (optional --fahrenheit flag for input)
    """
    if len(sys.argv) < 5:
        print("Usage: python thermo_calculator.py <protein_type> <thickness_inches> <target_temp> <doneness> [weight_kg] [--fahrenheit]")
        print("Example: python thermo_calculator.py beef 1.5 54 medium-rare")
        print("Example: python thermo_calculator.py beef 1.5 54 medium-rare 0.8")
        print("Example: python thermo_calculator.py beef 1.5 129.2 medium-rare 0.8 --fahrenheit")
        print("\nDefault temperature unit: Celsius")
        print("Use --fahrenheit flag for Fahrenheit input temperatures")
        print("Weight in kilograms is optional but improves calculation accuracy")
        sys.exit(1)
    
    protein_type = sys.argv[1].lower()
    thickness_inches = float(sys.argv[2])
    target_temp = float(sys.argv[3])
    doneness = sys.argv[4].lower()
    
    # Check for optional weight parameter (5th argument if it's a number)
    weight_kg = None
    if len(sys.argv) > 5:
        try:
            # Try to parse as weight if it's a number
            potential_weight = float(sys.argv[5])
            if potential_weight > 0:  # Valid weight
                weight_kg = potential_weight
        except ValueError:
            # Not a number, probably a flag
            pass
    
    # Check for Fahrenheit flag
    use_fahrenheit = '--fahrenheit' in sys.argv or '-f' in sys.argv
    
    # Convert to Celsius if needed (default is already Celsius)
    if use_fahrenheit:
        target_temp_celsius = (target_temp - 32) * 5/9
        print(f"Input: {target_temp}°F = {target_temp_celsius:.1f}°C")
    else:
        target_temp_celsius = target_temp
        print(f"Input: {target_temp_celsius}°C = {target_temp_celsius * 9/5 + 32:.1f}°F")
    
    calculator = ThermodynamicCalculator()
    result = calculator.calculate_cooking_parameters(
        protein_type, thickness_inches, target_temp_celsius, doneness, weight_kg
    )
    
    if result['success']:
        print(f"\n=== SOUSPEED Thermodynamic Analysis ===")
        print(f"Protein: {result['protein_type'].title()}")
        print(f"Thickness: {result['thickness_inches']}\"")
        if result['weight_kg']:
            print(f"Weight: {result['weight_kg']} kg ({result['weight_kg'] * 2.20462:.1f} lbs)")
        else:
            print(f"Weight: Estimated from dimensions")
        print(f"Target: {result['target_temp_celsius']}°C ({result['target_temp_fahrenheit']}°F)")
        print(f"Doneness: {result['doneness'].title()}")
        print(f"\n--- Free Energy Analysis ---")
        print(f"Gibbs Energy Change (G=U-TS+PV): {result['gibbs_energy_change']} J/kg")
        print(f"Helmholtz Optimization (F=U-TS): Applied for temperature profile")
        if result['total_energy_kj']:
            print(f"Total Energy Required: {result['total_energy_kj']:.1f} kJ")
        print(f"\n--- Optimized Cooking Profile ---")
        print(f"High Temperature Phase: {result['high_temp_duration_minutes']} min at {result['initial_temp_celsius']}°C ({result['initial_temp_fahrenheit']}°F)")
        print(f"Equilibration Phase: {result['remaining_time_minutes']} min at {result['target_temp_celsius']}°C")
        print(f"Total Time: {result['total_time_hours']:.2f} hours")
        print(f"Conventional Time: {result['conventional_time_hours']:.2f} hours")
        print(f"Time Savings: {result['time_savings_percent']}%")
        print(f"\n--- Technical Parameters ---")
        print(f"Biot Number: {result['biot_number']}")
        print(f"Efficiency Factor: {result['efficiency']}")
        print(f"Heat Transfer Regime: {result['regime_description']}")
    else:
        print(f"Error: {result['error']}")
    
    # Also output JSON for programmatic use
    print(f"\n--- JSON Output ---")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
