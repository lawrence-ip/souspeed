/**
 * SousSpeed Calculator
 * Uses heat transfer equations to calculate sous vide cooking times
 */

// Thermal properties for different meat types
const MEAT_PROPERTIES = {
    beef: {
        name: 'Beef Steak',
        thermalDiffusivity: 1.4e-7, // m²/s
        density: 1050, // kg/m³
        specificHeat: 3500, // J/(kg·K)
        safeTemp: 54 // Minimum safe temperature
    },
    pork: {
        name: 'Pork Chop',
        thermalDiffusivity: 1.3e-7,
        density: 1030,
        specificHeat: 3600,
        safeTemp: 60
    },
    chicken: {
        name: 'Chicken Breast',
        thermalDiffusivity: 1.35e-7,
        density: 1000,
        specificHeat: 3800,
        safeTemp: 65
    },
    fish: {
        name: 'Fish Fillet',
        thermalDiffusivity: 1.2e-7,
        density: 1040,
        specificHeat: 3700,
        safeTemp: 50
    },
    lamb: {
        name: 'Lamb Chop',
        thermalDiffusivity: 1.38e-7,
        density: 1040,
        specificHeat: 3550,
        safeTemp: 56
    }
};

/**
 * Calculate cooking time using heat transfer equation
 * Based on Fourier's law of heat conduction for infinite slab geometry
 * 
 * @param {number} thickness - Thickness in cm
 * @param {number} startTemp - Starting temperature in °C
 * @param {number} waterTemp - Water bath temperature in °C
 * @param {number} thermalDiffusivity - Thermal diffusivity in m²/s
 * @returns {object} Calculation results
 */
function calculateCookingTime(thickness, startTemp, waterTemp, thermalDiffusivity) {
    // Convert thickness from cm to meters
    const L = thickness / 100 / 2; // Half-thickness for slab geometry
    
    // Temperature difference
    const deltaT = waterTemp - startTemp;
    
    // For 99% temperature equilibrium at center (Fo = 0.6)
    // Fourier number: Fo = α * t / L²
    // Where α is thermal diffusivity, t is time, L is characteristic length
    const fourierNumber99 = 0.6; // For 99% equilibrium
    const fourierNumber90 = 0.4; // For 90% equilibrium
    
    // Calculate time for 99% equilibrium (t = Fo * L² / α)
    const time99 = (fourierNumber99 * L * L) / thermalDiffusivity;
    
    // Calculate time for 90% equilibrium
    const time90 = (fourierNumber90 * L * L) / thermalDiffusivity;
    
    // Convert from seconds to minutes and hours
    const minutes99 = time99 / 60;
    const hours99 = minutes99 / 60;
    
    const minutes90 = time90 / 60;
    const hours90 = minutes90 / 60;
    
    return {
        time99Seconds: time99,
        time99Minutes: minutes99,
        time99Hours: hours99,
        time90Seconds: time90,
        time90Minutes: minutes90,
        time90Hours: hours90,
        deltaT: deltaT,
        fourierNumber: fourierNumber99
    };
}

/**
 * Format time into human-readable string
 */
function formatTime(hours, minutes) {
    if (hours >= 1) {
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        if (m === 0) {
            return `${h} hour${h !== 1 ? 's' : ''}`;
        }
        return `${h} hour${h !== 1 ? 's' : ''} ${m} minute${m !== 1 ? 's' : ''}`;
    } else {
        const m = Math.round(minutes);
        return `${m} minute${m !== 1 ? 's' : ''}`;
    }
}

/**
 * Generate explanation text
 */
function generateExplanation(meatType, results, waterTemp, thickness) {
    const meat = MEAT_PROPERTIES[meatType];
    let explanation = `For ${meat.name} at ${thickness}cm thickness, heat will penetrate from the surface to the core. `;
    
    if (waterTemp < meat.safeTemp) {
        explanation += `⚠️ Note: Water temperature (${waterTemp}°C) is below recommended safe temperature (${meat.safeTemp}°C) for ${meat.name}. Consider increasing water temperature for food safety. `;
    }
    
    explanation += `The calculation uses thermal diffusivity (α = ${(meat.thermalDiffusivity * 1e7).toFixed(2)} × 10⁻⁷ m²/s) `;
    explanation += `and the heat conduction equation to determine when the center reaches target temperature. `;
    explanation += `Add 30-60 minutes to pasteurization time for food safety.`;
    
    return explanation;
}

// Form submission handler
document.getElementById('calculatorForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get form values
    const meatType = document.getElementById('meatType').value;
    const thickness = parseFloat(document.getElementById('thickness').value);
    const startTemp = parseFloat(document.getElementById('startTemp').value);
    const waterTemp = parseFloat(document.getElementById('waterTemp').value);
    
    // Validate inputs
    if (!meatType) {
        alert('Please select a meat type');
        return;
    }
    
    if (thickness <= 0 || thickness > 10) {
        alert('Please enter a valid thickness between 0.5 and 10 cm');
        return;
    }
    
    if (waterTemp <= startTemp) {
        alert('Water temperature must be higher than starting temperature');
        return;
    }
    
    // Get meat properties
    const meat = MEAT_PROPERTIES[meatType];
    
    // Calculate cooking time
    const results = calculateCookingTime(
        thickness,
        startTemp,
        waterTemp,
        meat.thermalDiffusivity
    );
    
    // Display results
    const cookingTimeText = formatTime(results.time99Hours, results.time99Minutes);
    const coreTimeText = formatTime(results.time90Hours, results.time90Minutes);
    
    document.getElementById('cookingTime').textContent = cookingTimeText;
    document.getElementById('coreTime').textContent = coreTimeText;
    document.getElementById('thermalDiff').textContent = 
        `${(meat.thermalDiffusivity * 1e7).toFixed(2)} × 10⁻⁷ m²/s`;
    document.getElementById('explanation').textContent = 
        generateExplanation(meatType, results, waterTemp, thickness);
    
    // Show results section
    const resultsDiv = document.getElementById('results');
    resultsDiv.classList.add('show');
    
    // Smooth scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});

// Add input validation for real-time feedback
document.getElementById('thickness').addEventListener('input', function(e) {
    const value = parseFloat(e.target.value);
    if (value > 10) {
        e.target.value = 10;
    } else if (value < 0) {
        e.target.value = 0.5;
    }
});

document.getElementById('waterTemp').addEventListener('input', function(e) {
    const value = parseFloat(e.target.value);
    const startTemp = parseFloat(document.getElementById('startTemp').value);
    if (value <= startTemp && startTemp) {
        e.target.setCustomValidity('Water temperature must be higher than starting temperature');
    } else {
        e.target.setCustomValidity('');
    }
});
