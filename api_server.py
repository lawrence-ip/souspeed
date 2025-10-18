#!/usr/bin/env python3
"""
Flask API server for thermodynamic calculations.
Provides REST endpoints for the sous vide calculator.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from thermo_calculator import ThermodynamicCalculator

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Initialize calculator
calculator = ThermodynamicCalculator()

@app.route('/api/calculate', methods=['POST'])
def calculate_cooking_parameters():
    """
    Calculate optimal cooking parameters based on input parameters.
    
    Expected JSON payload:
    {
        "protein_type": "beef",
        "thickness_inches": 1.5,
        "target_temp_celsius": 54,
        "doneness": "medium-rare"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['protein_type', 'thickness_inches', 'target_temp_celsius', 'doneness']
        for param in required_params:
            if param not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required parameter: {param}'
                }), 400
        
        # Extract parameters
        protein_type = data['protein_type'].lower()
        thickness_inches = float(data['thickness_inches'])
        target_temp_celsius = float(data['target_temp_celsius'])
        doneness = data['doneness'].lower()
        
        # Validate protein type
        valid_proteins = ['beef', 'chicken', 'pork', 'fish', 'vegetables']
        if protein_type not in valid_proteins:
            return jsonify({
                'success': False,
                'error': f'Invalid protein type. Must be one of: {valid_proteins}'
            }), 400
        
        # Validate thickness range
        if thickness_inches < 0.1 or thickness_inches > 10:
            return jsonify({
                'success': False,
                'error': 'Thickness must be between 0.1 and 10 inches'
            }), 400
        
        # Calculate parameters
        result = calculator.calculate_cooking_parameters(
            protein_type, thickness_inches, target_temp_celsius, doneness
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid input value: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Calculation error: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'calculator': 'ready',
        'available_proteins': list(calculator.protein_properties.keys())
    })

@app.route('/api/protein-properties', methods=['GET'])
def get_protein_properties():
    """Get thermal properties for all proteins."""
    properties = {}
    for protein, props in calculator.protein_properties.items():
        properties[protein] = {
            'density': props.density,
            'specific_heat': props.specific_heat,
            'thermal_conductivity': props.thermal_conductivity,
            'thermal_diffusivity': props.thermal_diffusivity
        }
    return jsonify(properties)

if __name__ == '__main__':
    print("Starting Thermodynamic Calculator API Server...")
    print("Available endpoints:")
    print("  POST /api/calculate - Calculate cooking parameters")
    print("  GET /api/health - Health check")
    print("  GET /api/protein-properties - Get protein thermal properties")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
