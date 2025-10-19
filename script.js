// Mobile navigation toggle
const mobileMenu = document.getElementById('mobile-menu');
const navMenu = document.querySelector('.nav-menu');

mobileMenu.addEventListener('click', () => {
    mobileMenu.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Scroll to calculator function
function scrollToCalculator() {
    document.getElementById('calculator').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Scroll to theory function
function scrollToTheory() {
    document.getElementById('theory').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Sous vide calculation logic
const sousVideData = {
    beef: {
        'rare': { temp: 129, tempC: 54, time: 1.5, texture: 'Very tender & juicy' },
        'medium-rare': { temp: 134, tempC: 57, time: 2, texture: 'Tender & juicy' },
        'medium': { temp: 140, tempC: 60, time: 2.5, texture: 'Firm but juicy' },
        'medium-well': { temp: 145, tempC: 63, time: 3, texture: 'Firm texture' },
        'well-done': { temp: 155, tempC: 68, time: 3.5, texture: 'Well-done texture' }
    },
    chicken: {
        'rare': { temp: 140, tempC: 60, time: 1.5, texture: 'Tender & safe' },
        'medium-rare': { temp: 145, tempC: 63, time: 2, texture: 'Juicy & safe' },
        'medium': { temp: 150, tempC: 66, time: 2.5, texture: 'Perfectly cooked' },
        'medium-well': { temp: 155, tempC: 68, time: 3, texture: 'Firm but moist' },
        'well-done': { temp: 165, tempC: 74, time: 3.5, texture: 'Fully cooked' }
    },
    pork: {
        'rare': { temp: 135, tempC: 57, time: 2, texture: 'Tender & juicy' },
        'medium-rare': { temp: 140, tempC: 60, time: 2.5, texture: 'Very tender' },
        'medium': { temp: 145, tempC: 63, time: 3, texture: 'Perfectly cooked' },
        'medium-well': { temp: 150, tempC: 66, time: 3.5, texture: 'Firm texture' },
        'well-done': { temp: 160, tempC: 71, time: 4, texture: 'Well-done' }
    },
    fish: {
        'rare': { temp: 104, tempC: 40, time: 0.5, texture: 'Delicate & flaky' },
        'medium-rare': { temp: 115, tempC: 46, time: 0.75, texture: 'Tender & moist' },
        'medium': { temp: 125, tempC: 52, time: 1, texture: 'Flaky texture' },
        'medium-well': { temp: 130, tempC: 54, time: 1.25, texture: 'Firm but moist' },
        'well-done': { temp: 140, tempC: 60, time: 1.5, texture: 'Fully cooked' }
    },
    vegetables: {
        'rare': { temp: 183, tempC: 84, time: 0.5, texture: 'Crisp-tender' },
        'medium-rare': { temp: 183, tempC: 84, time: 1, texture: 'Tender-crisp' },
        'medium': { temp: 185, tempC: 85, time: 1.5, texture: 'Perfectly tender' },
        'medium-well': { temp: 185, tempC: 85, time: 2, texture: 'Very tender' },
        'well-done': { temp: 185, tempC: 85, time: 2.5, texture: 'Soft texture' }
    }
};

// Pricing plan restrictions
const pricingPlans = {
    free: {
        allowedProteins: ['beef'],
        permanent: true
    },
    proChef: {
        allowedProteins: ['chicken', 'pork', 'fish', 'vegetables'],
        price: 10,
        billing: 'yearly'
    }
};

// Current user plan (in a real app, this would come from authentication)
let currentPlan = 'free';

// Update calculation based on user inputs
async function updateCalculation() {
    const proteinType = document.getElementById('protein-type').value;
    const thickness = parseFloat(document.getElementById('thickness').value);
    const doneness = document.getElementById('doneness').value;
    const weight = parseFloat(document.getElementById('weight').value);
    
    // Check if protein type is allowed for current plan
    if (currentPlan === 'free' && !pricingPlans.free.allowedProteins.includes(proteinType)) {
        showUpgradeMessage(proteinType);
        return;
    }
    
    // Reset any upgrade styling
    showNormalResults();
    
    const baseData = sousVideData[proteinType][doneness];
    
    try {
        // Use Python API for precise thermodynamic calculations
        const thermoData = await fetchThermodynamicCalculation(proteinType, thickness, baseData.tempC, doneness, weight);
        
        if (thermoData.success) {
            // Use scientifically calculated time
            const adjustedTime = thermoData.total_time_hours;
            
            // Store thermodynamic data for instructions
            window.currentThermoData = {
                highTempDuration: thermoData.high_temp_duration_hours,
                totalTime: thermoData.total_time_hours,
                equilibriumTime: thermoData.equilibrium_time_hours,
                efficiency: thermoData.efficiency,
                biotNumber: thermoData.biot_number,
                penetrationRatio: thermoData.penetration_ratio,
                regime: thermoData.regime,
                regimeDescription: thermoData.regime_description,
                adjustedTime: adjustedTime
            };
            
            // Update display with scientific calculations
            document.getElementById('temp-result').textContent = `${baseData.temp}°F (${baseData.tempC}°C)`;
            document.getElementById('time-result').textContent = formatTime(adjustedTime);
            document.getElementById('texture-result').textContent = baseData.texture;
            
        } else {
            // Fallback to JavaScript calculations if API fails
            console.warn('Python API failed, using JavaScript fallback:', thermoData.error);
            await updateCalculationFallback();
            return;
        }
        
    } catch (error) {
        console.warn('Failed to connect to Python API, using JavaScript fallback:', error);
        await updateCalculationFallback();
        return;
    }
    
    // Show thermodynamic indicator
    const thermoIndicator = document.getElementById('thermo-indicator');
    if (thermoIndicator) {
        thermoIndicator.style.display = 'flex';
    }
}

// Fallback function using JavaScript calculations
async function updateCalculationFallback() {
    const proteinType = document.getElementById('protein-type').value;
    const thickness = parseFloat(document.getElementById('thickness').value);
    const doneness = document.getElementById('doneness').value;
    const weight = parseFloat(document.getElementById('weight').value);
    const baseData = sousVideData[proteinType][doneness];
    
    // Use original JavaScript thermodynamic calculator
    const thermoData = thermoCalc.calculateOptimalProfile(proteinType, thickness, baseData.tempC);
    const equilibriumTime = thermoCalc.calculateEquilibriumTime(proteinType, thickness, baseData.tempC, 20);
    
    // Adjust time based on thermodynamic calculations
    const adjustedTime = Math.max(baseData.time, equilibriumTime * 1.1); // 10% safety margin
    
    // Store thermodynamic data for instructions
    window.currentThermoData = {
        ...thermoData,
        equilibriumTime: equilibriumTime,
        efficiency: thermoCalc.calculateEfficiency(proteinType, thickness),
        adjustedTime: adjustedTime
    };
    
    // Update display
    document.getElementById('temp-result').textContent = `${baseData.temp}°F (${baseData.tempC}°C)`;
    document.getElementById('time-result').textContent = formatTime(adjustedTime);
    document.getElementById('texture-result').textContent = baseData.texture;
}

// Fetch calculations from Python API
async function fetchThermodynamicCalculation(proteinType, thicknessInches, targetTempC, doneness, weightKg) {
    const apiUrl = 'http://localhost:5000/api/calculate';
    
    const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            protein_type: proteinType,
            thickness_inches: thicknessInches,
            target_temp_celsius: targetTempC,
            doneness: doneness,
            weight_kg: weightKg
        })
    });
    
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }
    
    return await response.json();
}

// Show upgrade message for restricted content
function showUpgradeMessage(proteinType) {
    const proteinNames = {
        chicken: 'Chicken',
        pork: 'Pork', 
        fish: 'Fish',
        vegetables: 'Vegetables'
    };
    
    const resultCard = document.querySelector('.result-card');
    resultCard.classList.add('upgrade-required');
    
    document.getElementById('temp-result').textContent = '🔒 Upgrade Required';
    document.getElementById('time-result').textContent = 'Pro Chef Plan';
    document.getElementById('texture-result').innerHTML = `
        ${proteinNames[proteinType]} calculations require Pro Chef plan
        <div class="upgrade-message">
            <div>Unlock all meat types for just $10/year</div>
            <button class="upgrade-btn" onclick="scrollToPricing()">Upgrade for $10/year</button>
        </div>
    `;
}

// Scroll to pricing section
function scrollToPricing() {
    document.getElementById('pricing').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Reset result card styling when showing normal results
function showNormalResults() {
    const resultCard = document.querySelector('.result-card');
    resultCard.classList.remove('upgrade-required');
}

// Format time display
function formatTime(hours) {
    if (hours < 1) {
        return `${Math.round(hours * 60)} minutes`;
    } else if (hours < 2) {
        const minutes = Math.round((hours - Math.floor(hours)) * 60);
        return minutes > 0 ? `${Math.floor(hours)} hour ${minutes} minutes` : `${Math.floor(hours)} hour`;
    } else {
        const minutes = Math.round((hours - Math.floor(hours)) * 60);
        return minutes > 0 ? `${Math.floor(hours)} hours ${minutes} minutes` : `${Math.floor(hours)} hours`;
    }
}

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    const animateElements = document.querySelectorAll('.feature-card, .pricing-card');
    
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Initialize calculator with default values
    updateCalculation();
});

// Form validation and enhanced interactions
document.querySelectorAll('input, select').forEach(element => {
    element.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });
    
    element.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
});

// Add loading states for buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function(e) {
        if (this.textContent.includes('Trial') || this.textContent.includes('Started')) {
            e.preventDefault();
            const originalText = this.textContent;
            this.textContent = 'Loading...';
            this.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                this.textContent = originalText;
                this.disabled = false;
                alert('Feature coming soon! Thanks for your interest.');
            }, 2000);
        }
    });
});

// Enhanced calculator with validation
function validateInputs() {
    const thickness = document.getElementById('thickness').value;
    const thicknessNum = parseFloat(thickness);
    
    if (thicknessNum < 0.5 || thicknessNum > 6) {
        alert('Please enter a thickness between 0.5 and 6 inches');
        return false;
    }
    
    return true;
}

// Add input validation
document.getElementById('thickness').addEventListener('change', function() {
    if (!validateInputs()) {
        this.value = 1; // Reset to default
    }
    updateCalculation();
});

// Keyboard navigation support
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        // Close mobile menu if open
        navMenu.classList.remove('active');
        mobileMenu.classList.remove('active');
    }
});

// Performance optimization: Debounce scroll events
let scrollTimeout;
window.addEventListener('scroll', () => {
    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
    }
    scrollTimeout = setTimeout(() => {
        // Scroll-based animations can go here
    }, 16); // ~60fps
});

// Thermodynamic Equilibrium Calculator
class ThermodynamicCalculator {
    constructor() {
        // Material properties for different proteins
        this.proteinProperties = {
            beef: {
                density: 1050, // kg/m³
                specificHeat: 3400, // J/(kg·K)
                thermalConductivity: 0.45, // W/(m·K)
                thermalDiffusivity: 1.27e-7 // m²/s
            },
            chicken: {
                density: 1020,
                specificHeat: 3600,
                thermalConductivity: 0.42,
                thermalDiffusivity: 1.14e-7
            },
            pork: {
                density: 1030,
                specificHeat: 3500,
                thermalConductivity: 0.43,
                thermalDiffusivity: 1.19e-7
            },
            fish: {
                density: 980,
                specificHeat: 3800,
                thermalConductivity: 0.48,
                thermalDiffusivity: 1.29e-7
            },
            vegetables: {
                density: 900,
                specificHeat: 4000,
                thermalConductivity: 0.55,
                thermalDiffusivity: 1.53e-7
            }
        };
        
        // Water properties
        this.waterProperties = {
            density: 998, // kg/m³ at 60°C
            specificHeat: 4180, // J/(kg·K)
            thermalConductivity: 0.65 // W/(m·K)
        };
    }
    
    // Calculate heat transfer coefficient
    calculateHeatTransferCoefficient(temperature) {
        // Natural convection in water (simplified)
        const grashofNumber = this.calculateGrashofNumber(temperature);
        const prandtlNumber = 4.3; // For water at typical sous vide temperatures
        const nusseltNumber = 0.54 * Math.pow(grashofNumber * prandtlNumber, 0.25);
        
        return (nusseltNumber * this.waterProperties.thermalConductivity) / 0.01; // Characteristic length ~1cm
    }
    
    // Calculate Grashof number for natural convection
    calculateGrashofNumber(temperature) {
        const g = 9.81; // gravity
        const beta = 0.0002; // thermal expansion coefficient for water
        const deltaT = 5; // temperature difference
        const L = 0.01; // characteristic length (1cm)
        const kinematicViscosity = 4.78e-7; // m²/s for water at 60°C
        
        return (g * beta * deltaT * Math.pow(L, 3)) / Math.pow(kinematicViscosity, 2);
    }
    
    // Calculate Biot number to determine heat transfer regime
    calculateBiotNumber(proteinType, thickness) {
        const props = this.proteinProperties[proteinType];
        const h = this.calculateHeatTransferCoefficient(60); // Approximate temperature
        const characteristicLength = thickness * 0.0254 / 2; // Convert inches to meters, half thickness
        
        return (h * characteristicLength) / props.thermalConductivity;
    }
    
    // Calculate time to reach thermal equilibrium using Fourier number
    calculateEquilibriumTime(proteinType, thickness, targetTemp, ambientTemp) {
        const props = this.proteinProperties[proteinType];
        const biotNumber = this.calculateBiotNumber(proteinType, thickness);
        const characteristicLength = thickness * 0.0254 / 2; // Convert to meters
        
        // For infinite cylinder approximation (most food shapes)
        let fourierNumber;
        if (biotNumber < 0.1) {
            // Lumped capacitance method
            fourierNumber = -Math.log(0.01); // 99% equilibrium
        } else {
            // Use first eigenvalue for infinite cylinder
            const eigenvalue = this.getFirstEigenvalue(biotNumber);
            fourierNumber = -Math.log(0.01) / Math.pow(eigenvalue, 2);
        }
        
        // Time calculation
        const time = (fourierNumber * Math.pow(characteristicLength, 2)) / props.thermalDiffusivity;
        
        return time / 3600; // Convert to hours
    }
    
    // Get first eigenvalue for infinite cylinder (approximation)
    getFirstEigenvalue(biotNumber) {
        // Empirical correlation for first eigenvalue
        if (biotNumber < 0.1) return Math.sqrt(biotNumber);
        if (biotNumber < 10) return 1.256 * Math.sqrt(biotNumber);
        return 1.571 + 0.5 / biotNumber; // Approaches π/2 for large Bi
    }
    
    // Calculate optimal two-temperature profile
    calculateOptimalProfile(proteinType, thickness, targetTemp) {
        const equilibriumTime = this.calculateEquilibriumTime(proteinType, thickness, targetTemp + 10, 20);
        const props = this.proteinProperties[proteinType];
        
        // Optimal high temperature phase (based on heat penetration)
        const optimalHighTempTime = Math.min(equilibriumTime * 0.3, 0.5); // Max 30 minutes
        
        // Calculate heat penetration depth
        const penetrationDepth = 2 * Math.sqrt(props.thermalDiffusivity * optimalHighTempTime * 3600);
        const thicknessMeters = thickness * 0.0254;
        
        // Adjust based on penetration ratio
        const penetrationRatio = penetrationDepth / thicknessMeters;
        const adjustedHighTempTime = optimalHighTempTime * Math.min(2, 1 / penetrationRatio);
        
        return {
            highTempDuration: adjustedHighTempTime,
            totalTime: equilibriumTime,
            penetrationRatio: penetrationRatio,
            biotNumber: this.calculateBiotNumber(proteinType, thickness)
        };
    }
    
    // Calculate heat transfer efficiency
    calculateEfficiency(proteinType, thickness) {
        const biotNumber = this.calculateBiotNumber(proteinType, thickness);
        
        // Efficiency based on Biot number
        if (biotNumber < 0.1) return 0.95; // Very efficient
        if (biotNumber < 1) return 0.85; // Good efficiency
        if (biotNumber < 10) return 0.70; // Moderate efficiency
        return 0.55; // Lower efficiency for thick/low conductivity items
    }
}

// Initialize thermodynamic calculator
const thermoCalc = new ThermodynamicCalculator();

// Instructions generation functionality
function generateInstructions() {
    const proteinType = document.getElementById('protein-type').value;
    const thickness = parseFloat(document.getElementById('thickness').value);
    const doneness = document.getElementById('doneness').value;
    
    // Check if protein type is allowed for current plan
    if (currentPlan === 'free' && !pricingPlans.free.allowedProteins.includes(proteinType)) {
        alert('Please upgrade to Pro Chef to access instructions for this protein type.');
        return;
    }
    
    const baseData = sousVideData[proteinType][doneness];
    const adjustedTime = baseData.time * (thickness / 1);
    
    // Update summary
    updateInstructionSummary(proteinType, thickness, doneness, baseData, adjustedTime);
    
    // Generate cooking steps
    generateCookingSteps(proteinType, thickness, baseData, adjustedTime);
    
    // Generate tips
    generateTips(proteinType, doneness);
    
    // Generate safety guidelines
    generateSafetyGuidelines(proteinType);
    
    // Show instructions section
    document.getElementById('instructions').style.display = 'block';
    document.getElementById('instructions').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

function updateInstructionSummary(proteinType, thickness, doneness, baseData, adjustedTime) {
    const initialTempC = baseData.tempC + 10;
    const initialTempF = Math.round((initialTempC * 9/5) + 32);
    
    document.getElementById('summary-protein').textContent = proteinType.charAt(0).toUpperCase() + proteinType.slice(1);
    document.getElementById('summary-temp').innerHTML = `
        <div>Initial: ${initialTempF}°F (${initialTempC}°C)</div>
        <div>Final: ${baseData.temp}°F (${baseData.tempC}°C)</div>
    `;
    document.getElementById('summary-time').textContent = formatTime(adjustedTime);
    document.getElementById('summary-thickness').textContent = `${thickness} inch${thickness !== 1 ? 'es' : ''}`;
}

function generateCookingSteps(proteinType, thickness, baseData, adjustedTime) {
    const steps = getCookingSteps(proteinType, thickness, baseData, adjustedTime);
    const stepsContainer = document.getElementById('cooking-steps');
    
    stepsContainer.innerHTML = steps.map((step, index) => `
        <div class="instruction-step">
            <div class="step-number">${index + 1}</div>
            <div class="step-content">
                <h4>${step.title}</h4>
                <p>${step.description}</p>
                ${step.duration ? `<span class="step-duration">${step.duration}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function getCookingSteps(proteinType, thickness, baseData, adjustedTime) {
    // Calculate initial higher temperature (10°C hotter)
    const initialTempC = baseData.tempC + 10;
    const initialTempF = Math.round((initialTempC * 9/5) + 32);
    
    // Use thermodynamic data if available
    const thermoData = window.currentThermoData;
    const highTempDuration = thermoData ? thermoData.highTempDuration * 60 : 20; // Convert to minutes or use default
    
    const commonSteps = [
        {
            title: "Prepare the Water Bath",
            description: "Fill your sous vide container with water and attach your immersion circulator. Set the temperature to the initial higher specification.",
            duration: "10 minutes"
        },
        {
            title: "Season Your Protein",
            description: `Season your ${proteinType} with salt, pepper, and any desired herbs or spices. Let it rest at room temperature (25°C/77°F) for 15-30 minutes to ensure even cooking. All cooking times are calculated based on this starting temperature.`,
            duration: "15-30 minutes"
        },
        {
            title: "Vacuum Seal",
            description: "Place the seasoned protein in a vacuum-sealable bag. Add a small amount of oil or butter if desired. Remove all air and seal tightly.",
            duration: "5 minutes"
        },
        {
            title: "Preheat to Initial Temperature",
            description: `Heat the water bath to ${initialTempF}°F (${initialTempC}°C) - this is 10°C higher than the final target temperature. Wait for the temperature to stabilize before proceeding.`,
            duration: "15-20 minutes"
        },
        {
            title: "Start High-Temperature Phase",
            description: `Submerge the sealed bag in the water bath at ${initialTempF}°F (${initialTempC}°C). Cook at this higher temperature for exactly ${Math.round(highTempDuration)} minutes to achieve optimal heat penetration based on thermodynamic calculations.`,
            duration: `${Math.round(highTempDuration)} minutes`
        },
        {
            title: "Quick Temperature Reduction",
            description: `After ${Math.round(highTempDuration)} minutes, remove approximately half of the hot water from the bath. Replace it with room temperature water to quickly cool the bath. Set your circulator to ${baseData.temp}°F (${baseData.tempC}°C).`,
            duration: "5-8 minutes"
        },
        {
            title: "Temperature Stabilization",
            description: `Allow the water bath to stabilize at the target temperature of ${baseData.temp}°F (${baseData.tempC}°C). This should happen quickly due to the room temperature water addition.`,
            duration: "5-10 minutes"
        },
        {
            title: "Continue Cooking at Target Temperature",
            description: `Continue cooking at the target temperature of ${baseData.temp}°F (${baseData.tempC}°C) for the remaining ${formatTime(adjustedTime - (highTempDuration/60) - 0.25)} (total cook time: ${formatTime(adjustedTime)}).`,
            duration: formatTime(adjustedTime - (highTempDuration/60) - 0.25)
        }
    ];

    // Add protein-specific finishing steps
    const finishingSteps = getFinishingSteps(proteinType);
    
    return [...commonSteps, ...finishingSteps];
}

function getFinishingSteps(proteinType) {
    const steps = {
        beef: [
            {
                title: "Rest and Sear",
                description: "Remove from bag and pat completely dry. Heat a cast iron pan over high heat with oil. Sear for 1-2 minutes per side for a beautiful crust.",
                duration: "5 minutes"
            },
            {
                title: "Rest and Serve",
                description: "Let the beef rest for 2-3 minutes before slicing. Serve immediately while hot.",
                duration: "3 minutes"
            }
        ],
        chicken: [
            {
                title: "Check Temperature",
                description: "Ensure internal temperature has reached at least 140°F (60°C) for safety. Pat dry thoroughly.",
                duration: "2 minutes"
            },
            {
                title: "Crisp the Skin",
                description: "For skin-on chicken, sear skin-side down in a hot pan for 2-3 minutes until crispy.",
                duration: "3 minutes"
            },
            {
                title: "Rest and Serve",
                description: "Let rest for 2 minutes before serving to allow juices to redistribute.",
                duration: "2 minutes"
            }
        ],
        pork: [
            {
                title: "Pat Dry and Sear",
                description: "Remove from bag and pat completely dry. Sear in a hot pan with oil for 2-3 minutes per side.",
                duration: "6 minutes"
            },
            {
                title: "Rest and Slice",
                description: "Allow to rest for 3-5 minutes before slicing against the grain.",
                duration: "5 minutes"
            }
        ],
        fish: [
            {
                title: "Gentle Removal",
                description: "Carefully remove fish from bag as it will be very delicate. Pat dry gently with paper towels.",
                duration: "2 minutes"
            },
            {
                title: "Optional Sear",
                description: "For a crispy exterior, quickly sear in a hot pan for 30-60 seconds per side. Be very gentle.",
                duration: "2 minutes"
            },
            {
                title: "Serve Immediately",
                description: "Serve the fish immediately while hot. Garnish with fresh herbs or lemon.",
                duration: "1 minute"
            }
        ],
        vegetables: [
            {
                title: "Check Texture",
                description: "Test doneness by gently pressing the vegetables. They should yield slightly but maintain structure.",
                duration: "1 minute"
            },
            {
                title: "Season and Serve",
                description: "Remove from bag, season with finishing salt if desired, and serve hot as a side dish.",
                duration: "2 minutes"
            }
        ]
    };
    
    return steps[proteinType] || steps.beef;
}

function generateTips(proteinType, doneness) {
    const tips = getTipsForProtein(proteinType, doneness);
    const tipsContainer = document.getElementById('cooking-tips');
    
    tipsContainer.innerHTML = tips.map(tip => `
        <div class="tip-card">
            <h4>${tip.title}</h4>
            <p>${tip.description}</p>
        </div>
    `).join('');
}

function getTipsForProtein(proteinType, doneness) {
    const thermoData = window.currentThermoData;
    
    const commonTips = [
        {
            title: "Thermodynamic Optimization",
            description: `Based on heat transfer calculations, your ${proteinType} has ${thermoData ? `${(thermoData.efficiency * 100).toFixed(0)}% heat transfer efficiency` : 'optimal heat transfer characteristics'}. The timing has been scientifically calculated for your specific thickness.`
        },
        {
            title: "Two-Temperature Technique",
            description: `Starting at a higher temperature for ${thermoData ? Math.round(thermoData.highTempDuration * 60) : 20} minutes accelerates heat penetration, then quickly reducing to target temperature ensures perfect doneness without overcooking.`
        },
        {
            title: "Quick Temperature Reduction",
            description: "Replacing half the hot water with room temperature water is the fastest way to cool your bath. This prevents overcooking during the temperature transition."
        },
        {
            title: "Water Level Management",
            description: "When replacing water, maintain proper water levels. Keep the food submerged at least 1 inch and don't exceed your container's maximum fill line."
        },
        {
            title: "Bag Placement",
            description: "Use clips or weights to keep bags submerged and prevent floating. Air pockets can cause uneven cooking."
        }
    ];
    
    // Add thermodynamic-specific tip if data available
    if (thermoData && thermoData.biotNumber) {
        const biotTip = {
            title: "Heat Transfer Analysis",
            description: `Your protein has a Biot number of ${thermoData.biotNumber.toFixed(2)}. ${
                thermoData.biotNumber < 0.1 ? 'This means heat transfers very quickly and evenly throughout.' :
                thermoData.biotNumber < 1 ? 'This indicates good heat transfer with minimal temperature gradients.' :
                'This suggests longer cooking times are needed for complete heat penetration.'
            }`
        };
        commonTips.splice(1, 0, biotTip);
    }

    const proteinSpecificTips = {
        beef: [
            {
                title: "Dry Aging Effect",
                description: "For longer cooks (24+ hours), you can achieve a dry-aged flavor. Use high-quality beef for best results."
            },
            {
                title: "Fat Rendering",
                description: "Higher fat cuts like ribeye benefit from slightly higher temperatures to render fat properly."
            }
        ],
        chicken: [
            {
                title: "Food Safety",
                description: "Chicken must reach safe pasteurization times. Lower temperatures require longer cooking times for safety."
            },
            {
                title: "Skin Preparation",
                description: "Remove skin before cooking, or dry thoroughly and sear at high heat for crispiness."
            }
        ],
        fish: [
            {
                title: "Delicate Handling",
                description: "Fish cooks quickly and can become mushy if overcooked. Monitor timing carefully."
            },
            {
                title: "Oil Addition",
                description: "A small amount of olive oil or butter in the bag helps with heat transfer and adds flavor."
            }
        ],
        pork: [
            {
                title: "Connective Tissue",
                description: "Tougher cuts like pork shoulder benefit from longer cooking times to break down collagen."
            }
        ],
        vegetables: [
            {
                title: "Blanching First",
                description: "Some vegetables benefit from a quick blanch before sous vide to preserve color and texture."
            }
        ]
    };

    return [...commonTips, ...(proteinSpecificTips[proteinType] || [])];
}

function generateSafetyGuidelines(proteinType) {
    const guidelines = getSafetyGuidelines(proteinType);
    const safetyContainer = document.getElementById('safety-guidelines');
    
    safetyContainer.innerHTML = guidelines.map(guideline => `
        <div class="safety-alert ${guideline.type}">
            <h5>${guideline.level}</h5>
            <p>${guideline.description}</p>
        </div>
    `).join('');
}

function getSafetyGuidelines(proteinType) {
    const commonGuidelines = [
        {
            type: 'info',
            level: 'Two-Temperature Method',
            description: 'The initial higher temperature phase (20 minutes) is safe and effective. The water replacement method quickly cools the bath without shocking the food.'
        },
        {
            type: 'warning',
            level: 'Water Replacement Safety',
            description: 'When replacing hot water with room temperature water, do it gradually and keep the food bag submerged. Never use ice-cold water as this can cause thermal shock.'
        },
        {
            type: 'danger',
            level: 'Critical',
            description: 'Never leave sous vide cooking unattended for extended periods. Ensure your device has safety shutoffs and alarms.'
        },
        {
            type: 'warning',
            level: 'Important',
            description: 'Always use food-grade vacuum bags rated for high temperatures. Regular plastic bags can leach chemicals and break down.'
        },
        {
            type: 'info',
            level: 'Best Practice',
            description: 'Label your bags with contents, both temperatures, and start time. This helps track cooking progress and ensures food safety.'
        }
    ];

    const proteinSpecificGuidelines = {
        chicken: [
            {
                type: 'danger',
                level: 'Food Safety',
                description: 'Chicken must reach proper pasteurization. At 140°F, cook for at least 30 minutes. At 165°F, pasteurization is immediate.'
            }
        ],
        pork: [
            {
                type: 'warning',
                level: 'Temperature',
                description: 'Modern pork is safe at 145°F, but traditional guidelines recommended 160°F. Choose based on your comfort level.'
            }
        ],
        fish: [
            {
                type: 'info',
                level: 'Quality',
                description: 'Use the freshest fish possible. Sous vide concentrates flavors, including any off-flavors from older fish.'
            }
        ]
    };

    return [...commonGuidelines, ...(proteinSpecificGuidelines[proteinType] || [])];
}

function hideInstructions() {
    document.getElementById('instructions').style.display = 'none';
    document.getElementById('calculator').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Interactive Theory Graphs
let temperatureChart = null;
let energyChart = null;

// Protein thermal properties (matching Python calculator)
const proteinProperties = {
    beef: { density: 1050, specificHeat: 3400, thermalConductivity: 0.45, thermalDiffusivity: 1.27e-7 },
    chicken: { density: 1020, specificHeat: 3600, thermalConductivity: 0.42, thermalDiffusivity: 1.14e-7 },
    pork: { density: 1040, specificHeat: 3500, thermalConductivity: 0.43, thermalDiffusivity: 1.18e-7 },
    fish: { density: 980, specificHeat: 3800, thermalConductivity: 0.50, thermalDiffusivity: 1.34e-7 }
};

function initializeGraphs() {
    // Wait for Chart.js to load
    if (typeof Chart === 'undefined') {
        setTimeout(initializeGraphs, 100);
        return;
    }
    
    // Initialize temperature chart
    const tempCtx = document.getElementById('temperatureChart');
    if (tempCtx) {
        temperatureChart = new Chart(tempCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Core Temperature (°C)',
                        data: [],
                        borderColor: '#dc2626',
                        backgroundColor: 'rgba(220, 38, 38, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Bath Temperature (°C)',
                        data: [],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Sous Vide Temperature Profile - Core Never Exceeds Target'
                    },
                    legend: {
                        display: true,
                        labels: {
                            generateLabels: function(chart) {
                                const original = Chart.defaults.plugins.legend.labels.generateLabels;
                                const labels = original.call(this, chart);
                                
                                // Add explanation for target line
                                labels.forEach(label => {
                                    if (label.text.includes('Target Max')) {
                                        label.text += ' - NEVER EXCEEDED';
                                    }
                                });
                                
                                return labels;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time (minutes)'
                        }
                    }
                }
            }
        });
    }
    
    // Initialize energy chart
    const energyCtx = document.getElementById('energyChart');
    if (energyCtx) {
        energyChart = new Chart(energyCtx, {
            type: 'bar',
            data: {
                labels: ['Gibbs Energy (G)', 'Helmholtz Energy (F)', 'Total Energy Required'],
                datasets: [{
                    label: 'Energy (kJ)',
                    data: [-9.8, -0.33, 114.2],
                    backgroundColor: [
                        'rgba(220, 38, 38, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    borderColor: [
                        '#dc2626',
                        '#3b82f6',
                        '#10b981'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Thermodynamic Energy Analysis'
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Energy (kJ or kJ/kg)'
                        }
                    }
                }
            }
        });
    }
    
    updateGraph();
}

function updateGraph() {
    const protein = document.getElementById('proteinSelect')?.value || 'beef';
    const thickness = parseFloat(document.getElementById('thicknessSlider')?.value || 1.5);
    const weight = parseFloat(document.getElementById('weightSlider')?.value || 0.8);
    
    // Update display values
    if (document.getElementById('thicknessValue')) {
        document.getElementById('thicknessValue').textContent = thickness + '"';
    }
    if (document.getElementById('weightValue')) {
        document.getElementById('weightValue').textContent = weight + 'kg';
    }
    
    // Simulate thermodynamic calculations
    const targetTemp = getTargetTemp(protein);
    const highTemp = targetTemp + 8; // High temperature phase
    const props = proteinProperties[protein];
    
    // Calculate cooking times (simplified from Python calculator)
    const thermalMass = weight * props.specificHeat;
    const massFactor = 1.0 + Math.pow(weight / 2.0, 0.7);
    const highPhaseTime = (thickness * thickness * 15 * massFactor) / (props.thermalDiffusivity * 1e7); // minutes
    const equilibrationTime = 6; // Fixed 6 minutes
    
    // Generate temperature profile data
    const timePoints = [];
    const coreTemps = [];
    const bathTemps = [];
    
    const totalTime = highPhaseTime + equilibrationTime;
    const points = 50;
    
    for (let i = 0; i <= points; i++) {
        const time = (i / points) * totalTime;
        timePoints.push(Math.round(time));
        
        if (time <= highPhaseTime) {
            // High temperature phase - Core NEVER exceeds target temperature
            bathTemps.push(highTemp);
            const progress = time / highPhaseTime;
            // Core approaches target temperature but never exceeds it
            const maxCoreReach = targetTemp * 0.98; // 98% of target max
            const coreTemp = 25 + (maxCoreReach - 25) * (1 - Math.exp(-progress * 2.5));
            coreTemps.push(Math.min(targetTemp, Math.round(coreTemp * 10) / 10));
        } else {
            // Equilibration phase - Core reaches exactly target temperature
            bathTemps.push(targetTemp);
            const equilibrationProgress = (time - highPhaseTime) / equilibrationTime;
            const startTemp = targetTemp * 0.98; // Start from 98% of target
            const coreTemp = startTemp + (targetTemp - startTemp) * equilibrationProgress;
            // Ensure core never exceeds target, even during equilibration
            coreTemps.push(Math.min(targetTemp, Math.round(coreTemp * 10) / 10));
        }
    }
    
    // Update temperature chart
    if (temperatureChart) {
        temperatureChart.data.labels = timePoints;
        temperatureChart.data.datasets[0].data = coreTemps;
        temperatureChart.data.datasets[1].data = bathTemps;
        
        // Add target temperature reference line
        if (!temperatureChart.data.datasets[2]) {
            temperatureChart.data.datasets.push({
                label: `Target Max (${targetTemp}°C)`,
                data: new Array(timePoints.length).fill(targetTemp),
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                borderDash: [5, 5],
                pointRadius: 0,
                tension: 0
            });
        } else {
            temperatureChart.data.datasets[2].data = new Array(timePoints.length).fill(targetTemp);
            temperatureChart.data.datasets[2].label = `Target Max (${targetTemp}°C)`;
        }
        
        temperatureChart.update();
    }
    
    // Calculate free energies (simplified)
    const deltaT = highTemp - 25;
    const gibbsEnergy = -(props.specificHeat * deltaT * Math.log((highTemp + 273.15) / (25 + 273.15))) / 1000; // kJ/kg
    const helmholtzEnergy = gibbsEnergy * 0.034; // Simplified relationship
    const totalEnergy = weight * props.specificHeat * deltaT / 1000; // kJ
    
    // Update energy chart
    if (energyChart) {
        energyChart.data.datasets[0].data = [gibbsEnergy, helmholtzEnergy, totalEnergy];
        energyChart.update();
    }
}

function getTargetTemp(protein) {
    const temps = {
        beef: 54,
        chicken: 65,
        pork: 60,
        fish: 52
    };
    return temps[protein] || 54;
}

// Initialize graphs when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Delay initialization to ensure Chart.js is loaded
    setTimeout(initializeGraphs, 500);
});
