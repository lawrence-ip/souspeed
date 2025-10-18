# SousSpeed - Sous Vide Optimization Calculator

Professional-grade sous vide calculator with thermodynamic optimization for chefs who demand precision.

## 🌟 Features

### 🔬 **Scientific Precision**
- **Thermodynamic calculations** using heat transfer physics
- **Biot number analysis** for optimal cooking times
- **Material property database** for different proteins
- **Two-temperature optimization** for faster, better results

### 💡 **Smart Interface**
- **Interactive calculator** with real-time results
- **Step-by-step instructions** generated dynamically
- **Professional tips** based on thermodynamic analysis
- **Mobile-responsive** design for kitchen use

### 🎯 **Pricing Tiers**
- **Free Forever**: Beef calculations permanently
- **Pro Chef ($10/year)**: All proteins + advanced features
- **No trial limits** - use beef calculations indefinitely

## 🚀 Quick Start

### Option 1: Simple Web Server
```bash
# Start just the web interface
python3 -m http.server 8000
```
Visit: http://localhost:8000

### Option 2: Full System (Recommended)
```bash
# Install dependencies
pip3 install -r requirements.txt

# Start both web and API servers
./start.sh
```
- Web Interface: http://localhost:8000
- API Server: http://localhost:5000

## 🏗️ Architecture

### Frontend (JavaScript/HTML/CSS)
- **Interactive calculator** with form validation
- **Responsive design** with red color scheme
- **Instructions generator** with step-by-step guidance
- **Thermodynamic integration** with visual indicators

### Backend (Python)
- **Flask API server** for thermodynamic calculations
- **Scientific calculator** using heat transfer physics
- **Material properties database** for accurate modeling
- **REST endpoints** for easy integration

### Files Structure
```
├── index.html              # Main landing page
├── styles.css              # Responsive styling
├── script.js               # Frontend logic & calculator
├── thermo_calculator.py    # Python thermodynamic engine
├── api_server.py           # Flask API server
├── test_calculator.py      # Testing utilities
├── start.sh                # Startup script
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🧪 Thermodynamic Engine

### Heat Transfer Physics
- **Grashof number** calculations for natural convection
- **Nusselt number** correlations for heat transfer
- **Fourier analysis** for thermal equilibrium timing
- **Biot number** analysis for cooking regimes

### Protein Properties Database
```python
Material Properties:
├── Beef: ρ=1050 kg/m³, cp=3400 J/(kg·K), k=0.45 W/(m·K)
├── Chicken: ρ=1020 kg/m³, cp=3600 J/(kg·K), k=0.42 W/(m·K)  
├── Pork: ρ=1030 kg/m³, cp=3500 J/(kg·K), k=0.43 W/(m·K)
├── Fish: ρ=980 kg/m³, cp=3800 J/(kg·K), k=0.48 W/(m·K)
└── Vegetables: ρ=900 kg/m³, cp=4000 J/(kg·K), k=0.55 W/(m·K)
```

### Cooking Optimization
- **Two-temperature method**: Start hot, then reduce
- **Dynamic timing**: Based on heat penetration depth  
- **Efficiency analysis**: Heat transfer effectiveness
- **Safety margins**: 10% additional time for food safety

## 📡 API Endpoints

### POST /api/calculate
Calculate optimal cooking parameters.

**Request:**
```json
{
    "protein_type": "beef",
    "thickness_inches": 1.5,
    "target_temp_celsius": 54,
    "doneness": "medium-rare"
}
```

**Response:**
```json
{
    "success": true,
    "biot_number": 20.534,
    "efficiency": 0.55,
    "high_temp_duration_minutes": 15.6,
    "total_time_hours": 0.64,
    "regime_description": "Longer cooking times needed for complete heat penetration"
}
```

### GET /api/health
Health check and available proteins.

### GET /api/protein-properties  
Get thermal properties for all proteins.

## 🎨 Design Features

### Red Color Scheme
- **Primary**: `#dc2626` (Red-600)
- **Gradient**: `#dc2626` → `#991b1b`
- **Hover states**: Consistent red theming
- **Accent colors**: Orange for highlights

### Responsive Layout
- **Mobile-first** design approach
- **Grid layouts** for features and pricing
- **Collapsible navigation** for mobile
- **Touch-friendly** buttons and inputs

### Animations
- **Smooth scrolling** between sections
- **Hover effects** on cards and buttons  
- **Loading states** for API calls
- **Rotating atom** for thermodynamic indicator

## 🧮 Usage Examples

### Command Line Calculator
```bash
# Calculate beef steak parameters
python3 thermo_calculator.py beef 1.5 54 medium-rare

# Calculate chicken breast  
python3 thermo_calculator.py chicken 1.0 65 medium

# Test all calculations
python3 test_calculator.py
```

### JavaScript Integration
```javascript
// Fetch from API
const result = await fetch('http://localhost:5000/api/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        protein_type: 'beef',
        thickness_inches: 1.5,
        target_temp_celsius: 54,
        doneness: 'medium-rare'
    })
});
```

### Two-Temperature Instructions
1. **Start at target + 10°C** for optimal heat penetration
2. **Cook for calculated duration** (15-40 minutes typically)
3. **Replace half water** with room temperature water  
4. **Continue at target temperature** for remaining time
5. **Professional finishing** with searing techniques

## 🔒 Plan Restrictions

### Free Forever Plan
- **Protein access**: Beef only
- **All features**: Calculator, instructions, tips
- **No time limits**: Use indefinitely
- **Mobile access**: Full responsive experience

### Pro Chef Plan ($10/year)
- **All proteins**: Chicken, pork, fish, vegetables  
- **Advanced features**: Recipe analytics, team sharing
- **Priority support**: Email assistance
- **API access**: For integration projects

## 🛡️ Food Safety

### Temperature Guidelines
- **Beef**: 129-155°F (54-68°C) depending on doneness
- **Chicken**: 140-165°F (60-74°C) with pasteurization times
- **Pork**: 135-160°F (57-71°C) modern safety standards  
- **Fish**: 104-140°F (40-60°C) delicate texture preservation
- **Vegetables**: 183-185°F (84-85°C) for optimal texture

### Safety Features
- **Pasteurization calculations** for poultry
- **Time-temperature relationships** for food safety
- **Visual alerts** for critical safety information
- **Professional guidelines** from culinary standards

## 🚀 Development

### Local Development
```bash
# Clone repository  
git clone https://github.com/lawrence-ip/souspeed.git
cd souspeed

# Install dependencies
pip3 install -r requirements.txt

# Start development servers
./start.sh
```

### Testing
```bash
# Test Python calculator
python3 test_calculator.py

# Test API endpoints
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"protein_type":"beef","thickness_inches":1.5,"target_temp_celsius":54,"doneness":"medium-rare"}'
```

### Deployment
The application can be deployed using:
- **Static hosting** (GitHub Pages, Netlify) for frontend only
- **Heroku/Railway** for full-stack with Python API
- **Docker containers** for scalable deployment
- **CDN distribution** for global performance

## 📚 Scientific Background

### Heat Transfer Theory
- **Fourier's Law**: Heat conduction through food materials
- **Newton's Law of Cooling**: Surface heat transfer  
- **Infinite cylinder model**: Most accurate for food shapes
- **Lumped capacitance**: For thin/high-conductivity items

### Thermodynamic Principles  
- **Thermal diffusivity**: Rate of temperature change
- **Biot number**: Internal vs external thermal resistance
- **Eigenvalue solutions**: Precise timing calculations
- **Penetration depth**: Heat distribution analysis

---

**SousSpeed** - Where culinary art meets thermal science. 🔬👨‍🍳
