#!/usr/bin/env python3
"""
Test script for the thermodynamic calculator.
"""

from thermo_calculator import ThermodynamicCalculator
import json

def test_calculator():
    """Test the thermodynamic calculator with sample inputs."""
    
    print("🧪 Testing Thermodynamic Calculator...")
    print("=" * 50)
    
    calculator = ThermodynamicCalculator()
    
    # Test cases
    test_cases = [
        {
            'name': 'Beef Steak (1 inch, medium-rare)',
            'protein': 'beef',
            'thickness': 1.0,
            'temp': 54,
            'doneness': 'medium-rare'
        },
        {
            'name': 'Chicken Breast (1.5 inch, medium)',
            'protein': 'chicken',
            'thickness': 1.5,
            'temp': 65,
            'doneness': 'medium'
        },
        {
            'name': 'Salmon Fillet (0.8 inch, medium)',
            'protein': 'fish',
            'thickness': 0.8,
            'temp': 52,
            'doneness': 'medium'
        }
    ]
    
    for test in test_cases:
        print(f"\n📊 {test['name']}")
        print("-" * 40)
        
        result = calculator.calculate_cooking_parameters(
            test['protein'], 
            test['thickness'], 
            test['temp'], 
            test['doneness']
        )
        
        if result['success']:
            print(f"✅ Calculation successful!")
            print(f"   Biot Number: {result['biot_number']}")
            print(f"   Efficiency: {result['efficiency'] * 100:.1f}%")
            print(f"   High Temp Phase: {result['high_temp_duration_minutes']:.1f} minutes")
            print(f"   Total Time: {result['total_time_hours']:.2f} hours")
            print(f"   Heat Transfer: {result['regime_description']}")
        else:
            print(f"❌ Calculation failed: {result['error']}")
    
    print("\n🎯 Testing complete!")

if __name__ == "__main__":
    test_calculator()
