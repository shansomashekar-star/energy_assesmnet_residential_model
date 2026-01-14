# Frontend Testing Guide

## Quick Start

1. **Start the API server:**
   ```bash
   python main.py
   ```
   The server will start on `http://localhost:8000`

2. **Open the frontend:**
   - Simply open `frontend.html` in your web browser
   - Or use a local server:
     ```bash
     # Python 3
     python -m http.server 8080
     
     # Then open: http://localhost:8080/frontend.html
     ```

3. **Fill out the form** with home information and click "Get Energy Assessment"

## Features

The frontend displays:
- **Energy Score** - Overall grade and percentile
- **Current Usage** - Annual cost, energy use, and EUI
- **Financial Summary** - Investment, savings, and payback
- **Recommendations** - Detailed list with:
  - Priority level (High/Medium/Low)
  - Annual savings
  - Upfront costs
  - Payback period
  - ROI percentage
  - Available rebates

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure:
- The API server is running
- The API URL in `frontend.html` matches your server (default: `http://localhost:8000`)

### API Not Responding
- Check that `main.py` is running without errors
- Verify models are loaded (check console output)
- Ensure all required model files exist in `models_advanced/`

### No Recommendations
- Some home profiles may not trigger recommendations
- Try an older home (pre-1980) with poor insulation for more recommendations

## Testing Different Scenarios

### High-Energy Home (Many Recommendations)
- Year Built: Before 1950
- Insulation: Poor
- Draftiness: Very Drafty
- Multiple refrigerators
- Old equipment

### Efficient Home (Fewer Recommendations)
- Year Built: 2010-2020
- Insulation: Well Insulated
- Draftiness: Not Drafty
- New equipment
- LED lighting
