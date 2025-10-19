#!/usr/bin/env python3
"""
Production Flask application for SousSpeed deployment on Digital Ocean.
Serves both static files and API endpoints.
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import json
import os
from thermo_calculator import ThermodynamicCalculator

app = Flask(__name__)
CORS(app)

# Initialize calculator
calculator = ThermodynamicCalculator()

@app.route('/')
def index():
    """Serve the main HTML page."""
    try:
        with open('index.html', 'r') as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return """
        <h1>SousSpeed - Sous Vide Optimization Tool</h1>
        <p>Welcome to SousSpeed! The advanced thermodynamic calculator for sous vide cooking.</p>
        <p>API is running at <a href="/api/health">/api/health</a></p>
        """, 200

@app.route('/styles.css')
def serve_css():
    """Serve CSS file."""
    try:
        return send_from_directory('.', 'styles.css', mimetype='text/css')
    except FileNotFoundError:
        return "", 404

@app.route('/script.js')
def serve_js():
    """Serve JavaScript file."""
    try:
        return send_from_directory('.', 'script.js', mimetype='application/javascript')
    except FileNotFoundError:
        return "", 404

@app.route('/api/calculate', methods=['POST'])
def calculate_cooking_parameters():
    """
    Calculate optimal cooking parameters based on input parameters.
    
    Expected JSON payload:
    {
        "protein_type": "beef",
        "thickness_inches": 1.5,
        "target_temp_celsius": 54,
        "doneness": "medium-rare",
        "weight_kg": 0.8  // optional
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
        weight_kg = data.get('weight_kg', None)
        if weight_kg is not None:
            weight_kg = float(weight_kg)
        
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
        
        # Calculate parameters with weight support
        result = calculator.calculate_cooking_parameters(
            protein_type, thickness_inches, target_temp_celsius, doneness, weight_kg
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
    """Health check endpoint for load balancers."""
    return jsonify({
        'status': 'healthy',
        'calculator': 'ready',
        'available_proteins': list(calculator.protein_properties.keys()),
        'features': ['weight_calculation', 'thermodynamic_optimization', 'celsius_fahrenheit']
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

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting SousSpeed Production Server...")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print("   Available endpoints:")
    print("     GET  / - Main application")
    print("     POST /api/calculate - Calculate cooking parameters")
    print("     GET  /api/health - Health check")
    print("     GET  /api/protein-properties - Protein properties")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
