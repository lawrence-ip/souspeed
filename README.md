# 🥩 SousSpeed - Sous Vide Time Calculator

A web-based calculator that uses thermodynamic formulas to determine optimal sous vide cooking times for different types of meat.

## Features

- **Multiple Meat Types**: Support for beef, pork, chicken, fish, and lamb
- **Accurate Calculations**: Uses heat transfer equations based on thermal diffusivity
- **User-Friendly Interface**: Clean, responsive design with helpful hints
- **Real-Time Results**: Instant calculation of cooking times with detailed explanations

## How It Works

SousSpeed uses Fourier's law of heat conduction to calculate how long it takes for heat to penetrate from the surface of the meat to its core. The calculation considers:

- **Thermal Diffusivity (α)**: How quickly heat spreads through the meat (m²/s)
- **Thickness**: The distance heat must travel to reach the center
- **Temperature Difference**: Between starting temperature and target water bath temperature
- **Fourier Number**: Dimensionless time parameter (Fo = α × t / L²)

### The Formula

For infinite slab geometry (typical for steaks and chops):

```
Time = (Fourier Number × L²) / α

Where:
- L = half-thickness of the meat (m)
- α = thermal diffusivity (m²/s)
- Fo = 0.6 for 99% temperature equilibrium
- Fo = 0.4 for 90% temperature equilibrium
```

## Usage

1. Open `index.html` in a web browser
2. Select your meat type from the dropdown
3. Enter the thickness of your cut (in centimeters)
4. Enter the starting temperature (refrigerated, room temperature, or frozen)
5. Enter your desired water bath temperature
6. Click "Calculate Cooking Time"

The calculator will display:
- Recommended cooking time (99% equilibrium)
- Time to core temperature (90% equilibrium)
- Thermal diffusivity value used
- Detailed explanation of the calculation

## Running Locally

Simply open the `index.html` file in any modern web browser. No build process or dependencies required!

Alternatively, you can serve it with any HTTP server:

```bash
# Using Python
python3 -m http.server 8080

# Using Node.js
npx http-server -p 8080
```

Then navigate to `http://localhost:8080`

## Meat Properties Database

The calculator includes thermal properties for:

| Meat Type | Thermal Diffusivity | Safe Temp |
|-----------|-------------------|-----------|
| Beef | 1.40 × 10⁻⁷ m²/s | 54°C |
| Pork | 1.30 × 10⁻⁷ m²/s | 60°C |
| Chicken | 1.35 × 10⁻⁷ m²/s | 65°C |
| Fish | 1.20 × 10⁻⁷ m²/s | 50°C |
| Lamb | 1.38 × 10⁻⁷ m²/s | 56°C |

## Safety Notes

⚠️ **Important**: The calculated times bring the meat to temperature equilibrium but may not include sufficient pasteurization time. Always add 30-60 minutes to the calculated time for food safety, especially for chicken and pork.

The calculator will warn you if your water bath temperature is below the recommended safe temperature for the selected meat type.

## Technical Details

- Pure HTML, CSS, and JavaScript - no frameworks required
- Responsive design works on desktop and mobile
- Uses CSS Grid and Flexbox for layout
- Smooth animations and transitions
- Form validation and error handling

## License

Open source - feel free to use and modify!
