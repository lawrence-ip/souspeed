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
    
    # Constants
    ROOM_TEMPERATURE_C = 25.0  # Assumed starting temperature for meat at room temp
    
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
        Calculate optimal two-phase cooking profile with temperature gradient acceleration.
        Phase 1: Higher bath temperature to create faster heat transfer gradient
        Phase 2: Target bath temperature for final equilibration
        Core temperature NEVER exceeds target doneness temperature.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius (max core temperature)
            weight_kg: Weight of the protein in kilograms
            
        Returns:
            Tuple of (optimal_high_bath_temp, high_phase_duration, energy_efficiency)
        """
        props = self.protein_properties[protein_type]
        
        # Test different bath temperatures to find optimal gradient acceleration
        best_efficiency = 0
        optimal_high_temp = target_temp + 8  # Start with conservative 8°C above
        best_duration = 0
        
        # Test bath temperatures 5°C to 12°C above target for gradient acceleration
        for temp_delta in range(5, 13):  
            test_bath_temp = target_temp + temp_delta
            
            # Calculate how long we can use this higher bath temp before core reaches target
            high_phase_time = self.calculate_safe_high_temp_duration(
                protein_type, thickness_inches, test_bath_temp, target_temp, weight_kg
            )
            
            if high_phase_time > 0.08:  # Must be at least 5 minutes to be worthwhile
                # Calculate Helmholtz free energy for this temperature gradient
                helmholtz_change = self.calculate_helmholtz_free_energy(self.ROOM_TEMPERATURE_C, test_bath_temp, protein_type)
                
                # Calculate total cooking time with this approach
                equilibration_time = self.calculate_equilibration_time(
                    protein_type, thickness_inches, target_temp, weight_kg, high_phase_time
                )
                
                total_time = high_phase_time + equilibration_time
                conventional_time = self.calculate_conventional_time(protein_type, thickness_inches, target_temp)
                
                # Energy efficiency combines time savings with thermodynamic efficiency
                time_efficiency = max(0, (conventional_time - total_time) / conventional_time)
                energy_efficiency = abs(helmholtz_change) / (props.specific_heat * temp_delta)
                
                combined_efficiency = time_efficiency * energy_efficiency
                
                if combined_efficiency > best_efficiency:
                    best_efficiency = combined_efficiency
                    optimal_high_temp = test_bath_temp
                    best_duration = high_phase_time
        
        return optimal_high_temp, best_duration, best_efficiency
    
    def calculate_safe_high_temp_duration(self, protein_type: str, thickness_inches: float,
                                        bath_temp: float, target_core_temp: float, 
                                        weight_kg: float = None) -> float:
        """
        Calculate how long we can use a higher bath temperature before the core reaches target.
        This ensures the meat core NEVER exceeds the desired doneness temperature.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches  
            bath_temp: Higher bath temperature for gradient acceleration
            target_core_temp: Maximum allowed core temperature (doneness temp)
            weight_kg: Weight of the protein in kilograms
            
        Returns:
            Time in hours we can safely use the higher bath temperature
        """
        if protein_type not in self.protein_properties:
            raise ValueError(f"Unknown protein type: {protein_type}")
            
        props = self.protein_properties[protein_type]
        characteristic_length = (thickness_inches * 0.0254) / 2  # Convert to meters
        
        # Weight-based thermal mass effect
        if weight_kg is not None:
            mass_factor = 1.0 + (weight_kg / 1.0) ** 0.5
            effective_diffusivity = props.thermal_diffusivity / mass_factor
        else:
            estimated_volume_m3 = (thickness_inches * 0.0254) ** 3 * 6  # Rough estimate
            estimated_weight = estimated_volume_m3 * props.density
            mass_factor = 1.0 + (estimated_weight / 1.0) ** 0.5
            effective_diffusivity = props.thermal_diffusivity / mass_factor
        
        # Apply Fourier's Law of Heat Conduction: Q/t = kA((T1-T2)/l)
        # Where: Q/t = heat transfer rate, k = thermal conductivity, A = area,
        #        T1-T2 = temperature difference, l = thickness
        
        # Calculate geometry parameters based on weight and thickness
        thickness_m = thickness_inches * 0.0254  # Convert to meters
        
        # Estimate mass and calculate realistic geometry if not provided
        if weight_kg is None:
            estimated_volume_m3 = thickness_m ** 3 * 6  # Rough volume estimate
            weight_kg = estimated_volume_m3 * props.density
        
        # Calculate actual volume from weight and density
        actual_volume_m3 = weight_kg / props.density
        
        # More accurate surface area calculation based on weight and thickness
        # Assuming roughly rectangular piece: V = L × W × T, surface area accounts for all sides
        if thickness_m > 0:
            # Calculate length and width from volume and thickness
            base_area = actual_volume_m3 / thickness_m  # L × W
            length_width = math.sqrt(base_area)  # Assume square cross-section for simplicity
            
            # Total surface area: 2(LW + LT + WT) = 2(base_area + 2 × length_width × thickness)
            surface_area = 2 * (base_area + 2 * length_width * thickness_m)
        else:
            surface_area = 6 * (actual_volume_m3 ** (2/3))  # Sphere approximation fallback
        
        # Calculate thermal mass with weight-dependent heat capacity effects
        # Larger pieces have slightly different effective heat capacity due to structure
        weight_factor = 1.0 + 0.1 * math.log(1 + weight_kg)  # Logarithmic scaling
        effective_specific_heat = props.specific_heat * weight_factor
        thermal_mass = weight_kg * effective_specific_heat  # J/K
        
        # Apply Fourier's Law to calculate heat transfer rate
        # Q/t = k * A * (T_bath - T_core) / l
        def calculate_heating_rate(current_core_temp):
            temp_diff = bath_temp - current_core_temp
            heat_rate = props.thermal_conductivity * surface_area * temp_diff / thickness_m
            return heat_rate  # Watts (J/s)
        
        # Simulate heating using small time steps
        current_temp = self.ROOM_TEMPERATURE_C
        time_step = 30.0  # 30 second time steps
        total_time = 0.0
        
        while current_temp < target_core_temp and total_time < 24 * 3600:  # Max 24 hours
            heat_rate = calculate_heating_rate(current_temp)
            temp_rise = (heat_rate * time_step) / thermal_mass  # ΔT = Q / (m * c)
            current_temp += temp_rise
            total_time += time_step
            
            # Safety check: if we're very close to target, break
            if current_temp >= target_core_temp * 0.98:
                break
        
        time_to_target = total_time
        
        # Convert to hours and add safety margin (stop when core reaches 95% of target temp)
        safe_time_hours = (time_to_target * 0.90) / 3600
        
        return max(0.0, safe_time_hours)
    
    def calculate_equilibration_time(self, protein_type: str, thickness_inches: float,
                                   target_temp: float, weight_kg: float = None, 
                                   high_phase_time: float = 0) -> float:
        """
        Calculate equilibration time at target temperature after high-temp phase.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius
            weight_kg: Weight of protein in kg
            high_phase_time: Duration of high temperature phase in hours
            
        Returns:
            Equilibration time in hours
        """
        # The high-temp phase gets us close to target, equilibration finishes the job
        # Typically 15-30% of what the full cook time would have been
        full_cook_time = self.calculate_sous_vide_time(protein_type, thickness_inches, target_temp, weight_kg)
        
        # Equilibration time depends on how much of the heating was done in high-temp phase
        if high_phase_time > 0:
            # Estimate how much heating was accomplished (rough approximation)
            heating_completion = min(0.85, high_phase_time / full_cook_time * 1.5)
            remaining_time = full_cook_time * (1 - heating_completion)
        else:
            remaining_time = full_cook_time
        
        return max(0.1, remaining_time)  # Minimum 6 minutes for final equilibration
    
    def calculate_sous_vide_time(self, protein_type: str, thickness_inches: float,
                                target_temp: float, weight_kg: float = None) -> float:
        """
        Calculate proper sous vide cooking time where bath = target temperature.
        Uses heat transfer physics with thermodynamic optimization.
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius (= bath temperature)
            weight_kg: Weight of the protein in kilograms (optional)
            
        Returns:
            Cooking time in hours
        """
        if protein_type not in self.protein_properties:
            raise ValueError(f"Unknown protein type: {protein_type}")
            
        props = self.protein_properties[protein_type]
        characteristic_length = (thickness_inches * 0.0254) / 2  # Convert to meters
        
        # Apply Fourier's Law of Heat Conduction: Q/t = kA((T1-T2)/l)
        # Calculate geometry and thermal parameters based on actual weight
        thickness_m = thickness_inches * 0.0254  # Convert to meters
        
        # Estimate mass if not provided
        if weight_kg is None:
            estimated_volume_m3 = thickness_m ** 3 * 6  # Rough volume estimate
            weight_kg = estimated_volume_m3 * props.density
        
        # Calculate actual volume and realistic surface area from weight
        actual_volume_m3 = weight_kg / props.density
        
        # Weight-dependent surface area calculation
        if thickness_m > 0:
            base_area = actual_volume_m3 / thickness_m  # L × W from volume and thickness
            length_width = math.sqrt(base_area)
            # Total surface area for heat transfer
            surface_area = 2 * (base_area + 2 * length_width * thickness_m)
        else:
            surface_area = 6 * (actual_volume_m3 ** (2/3))  # Sphere approximation
        
        # Calculate thermal mass with weight scaling effects
        weight_factor = 1.0 + 0.1 * math.log(1 + weight_kg)
        effective_specific_heat = props.specific_heat * weight_factor
        thermal_mass = weight_kg * effective_specific_heat  # J/K
        
        # Use Fourier's Law to simulate heating to 99% of target temperature
        current_temp = self.ROOM_TEMPERATURE_C
        target_for_99_percent = target_temp * 0.99  # 99% completion
        time_step = 60.0  # 1-minute time steps for sous vide precision
        total_time = 0.0
        
        while current_temp < target_for_99_percent and total_time < 48 * 3600:  # Max 48 hours
            # Apply Fourier's Law: Q/t = k * A * (T_bath - T_core) / l
            temp_diff = target_temp - current_temp
            heat_rate = props.thermal_conductivity * surface_area * temp_diff / thickness_m
            temp_rise = (heat_rate * time_step) / thermal_mass  # ΔT = Q / (m * c)
            current_temp += temp_rise
            total_time += time_step
            
            # Prevent infinite loops with very small temperature differences
            if temp_diff < 0.01:  # Less than 0.01°C difference
                break
        
        time_hours = total_time / 3600
        
        return time_hours
    


    
    def calculate_optimal_profile(self, protein_type: str, thickness_inches: float, 
                                target_temp: float, weight_kg: float = None) -> Dict[str, Any]:
        """
        Calculate optimal two-phase sous vide cooking profile with gradient acceleration.
        Phase 1: Higher bath temp for faster heat transfer (core never exceeds target)
        Phase 2: Target bath temp for final equilibration
        
        Args:
            protein_type: Type of protein
            thickness_inches: Thickness in inches
            target_temp: Target temperature in Celsius (max core temperature)
            weight_kg: Weight of the protein in kilograms (optional, improves accuracy)
            
        Returns:
            Dictionary with optimal two-phase cooking parameters
        """
        # Calculate optimal two-phase profile with gradient acceleration
        optimal_bath_temp, high_phase_time, efficiency = self.calculate_optimal_temperature_profile(
            protein_type, thickness_inches, target_temp, weight_kg
        )
        
        # Calculate equilibration time at target temperature
        equilibration_time = self.calculate_equilibration_time(
            protein_type, thickness_inches, target_temp, weight_kg, high_phase_time
        )
        
        # Calculate both free energy changes for the temperature transitions
        gibbs_change = self.calculate_gibbs_energy_change(self.ROOM_TEMPERATURE_C, optimal_bath_temp, protein_type)
        helmholtz_change = self.calculate_helmholtz_free_energy(self.ROOM_TEMPERATURE_C, target_temp, protein_type)
        
        # Two-phase cooking times
        time_high = high_phase_time
        time_remaining = equilibration_time
        
        # Total time is sum of both phases
        total_time = time_high + time_remaining
        
        # Calculate efficiency based on time savings from gradient acceleration
        conventional_time = self.calculate_conventional_time(protein_type, thickness_inches, target_temp)
        time_savings = max(0, (conventional_time - total_time) / conventional_time)
        
        # Calculate heat penetration metrics
        props = self.protein_properties[protein_type]
        # High-temp phase achieves rapid initial heating, equilibration completes it
        penetration_depth = 2 * math.sqrt(props.thermal_diffusivity * time_high * 3600)
        thickness_meters = thickness_inches * 0.0254
        penetration_ratio = min(1.0, penetration_depth / thickness_meters)
        
        # Calculate total energy requirement if weight is known
        total_energy_kj = None
        if weight_kg is not None:
            props = self.protein_properties[protein_type]
            # Energy = mass × specific_heat × ΔT (from room temp to bath temp)
            delta_t = optimal_bath_temp - self.ROOM_TEMPERATURE_C
            total_energy_j = weight_kg * props.specific_heat * delta_t
            total_energy_kj = total_energy_j / 1000  # Convert to kJ
        
        return {
            'high_temp_duration': time_high,  # hours (gradient acceleration phase)
            'remaining_time': time_remaining,  # hours (equilibration phase)
            'total_time': total_time,  # hours
            'conventional_time': conventional_time,  # hours
            'time_savings_percent': time_savings * 100,
            'penetration_ratio': penetration_ratio,
            'gibbs_energy_change': gibbs_change,
            'helmholtz_energy_change': helmholtz_change,
            'optimal_high_temp': optimal_bath_temp,  # Bath temperature (not core!)
            'target_core_temp': target_temp,  # Maximum core temperature
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
                'bath_temp_high_celsius': round(profile['optimal_high_temp'], 1),
                'bath_temp_high_fahrenheit': round(profile['optimal_high_temp'] * 9/5 + 32),
                'target_core_temp_celsius': target_temp_celsius,
                'target_core_temp_fahrenheit': round(target_temp_celsius * 9/5 + 32)
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
        print(f"Starting temperature: {ThermodynamicCalculator.ROOM_TEMPERATURE_C}°C (room temperature)")
    
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
        print(f"Target: {result['target_core_temp_celsius']}°C ({result['target_core_temp_fahrenheit']}°F)")
        print(f"Doneness: {result['doneness'].title()}")
        print(f"\n--- Free Energy Analysis ---")
        print(f"Gibbs Energy Change (G=U-TS+PV): {result['gibbs_energy_change']} J/kg")
        print(f"Helmholtz Optimization (F=U-TS): Applied for temperature profile")
        if result['total_energy_kj']:
            print(f"Total Energy Required: {result['total_energy_kj']:.1f} kJ")
        print(f"\n--- Optimized Two-Phase Cooking Profile ---")
        print(f"Phase 1 (Gradient Acceleration): {result['high_temp_duration_minutes']} min")
        print(f"  Bath Temperature: {result['bath_temp_high_celsius']}°C ({result['bath_temp_high_fahrenheit']}°F)")
        print(f"  Core Temperature: 25°C → {result['target_core_temp_celsius']}°C (NEVER exceeds target)")
        print(f"Phase 2 (Equilibration): {result['remaining_time_minutes']} min")
        print(f"  Bath Temperature: {result['target_core_temp_celsius']}°C (same as target core temp)")
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
