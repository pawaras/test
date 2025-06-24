from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime, timedelta
import json
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration - Set these as environment variables in Render
MERCEDES_CLIENT_ID = os.getenv('MERCEDES_CLIENT_ID')
MERCEDES_CLIENT_SECRET = os.getenv('MERCEDES_CLIENT_SECRET')
MERCEDES_REDIRECT_URI = os.getenv('MERCEDES_REDIRECT_URI')
VEHICLE_VIN = os.getenv('VEHICLE_VIN')
API_KEY = os.getenv('API_KEY')  # Your custom API key for Siri requests

# Mercedes-Benz API endpoints
MERCEDES_AUTH_URL = "https://id.mercedes-benz.com/as/authorization.oauth2"
MERCEDES_TOKEN_URL = "https://id.mercedes-benz.com/as/token.oauth2"
MERCEDES_API_BASE = "https://api.mercedes-benz.com/vehicledata/v2"

class MercedesAPI:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    def get_authorization_url(self):
        """Generate the OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': MERCEDES_CLIENT_ID,
            'redirect_uri': MERCEDES_REDIRECT_URI,
            'scope': 'mb:vehicle:mbdata:evstatus mb:vehicle:mbdata:fuelstatus mb:vehicle:mbdata:vehiclestatus mb:vehicle:mbdata:vehiclelock mb:vehicle:mbdata:payasyoudrive offline_access'
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{MERCEDES_AUTH_URL}?{query_string}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': MERCEDES_REDIRECT_URI,
            'client_id': MERCEDES_CLIENT_ID,
            'client_secret': MERCEDES_CLIENT_SECRET
        }
        
        try:
            response = requests.post(MERCEDES_TOKEN_URL, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Successfully obtained access token")
                return True
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            return False
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
            
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': MERCEDES_CLIENT_ID,
            'client_secret': MERCEDES_CLIENT_SECRET
        }
        
        try:
            response = requests.post(MERCEDES_TOKEN_URL, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data['refresh_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Successfully refreshed access token")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return False
    
    def is_token_valid(self):
        """Check if current token is valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.now() < self.token_expires_at
    
    def ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.is_token_valid():
            if not self.refresh_access_token():
                logger.error("Failed to refresh token")
                return False
        return True
    
    def send_remote_start_command(self, vin):
        """Send remote start command to the vehicle"""
        if not self.ensure_valid_token():
            return {'success': False, 'error': 'Authentication failed'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Try different possible endpoints for remote start
        endpoints_to_try = [
            f"{MERCEDES_API_BASE}/vehicles/{vin}/commands/engine-start",
            f"{MERCEDES_API_BASE}/vehicles/{vin}/engine/start",
            f"{MERCEDES_API_BASE}/vehicles/{vin}/remote-start"
        ]
        
        for endpoint in endpoints_to_try:
            payload = {
                'command': 'START'
            }
            
            try:
                logger.info(f"Trying remote start endpoint: {endpoint}")
                response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                
                if response.status_code in [200, 201, 202]:
                    logger.info("Remote start command sent successfully")
                    return {
                        'success': True, 
                        'message': 'Remote start command sent successfully',
                        'endpoint_used': endpoint,
                        'response': response.json() if response.text else {}
                    }
                elif response.status_code == 404:
                    logger.warning(f"Endpoint not found: {endpoint}")
                    continue
                else:
                    logger.error(f"Remote start failed at {endpoint}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Request failed for {endpoint}: {str(e)}")
                continue
        
        # If all endpoints failed
        return {
            'success': False, 
            'error': 'Remote start not available - tried all known endpoints',
            'endpoints_tried': endpoints_to_try
        }
    
    def get_vehicle_status(self, vin):
        """Get current vehicle status"""
        if not self.ensure_valid_token():
            return {'success': False, 'error': 'Authentication failed'}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Try different status endpoints
        endpoints_to_try = [
            f"{MERCEDES_API_BASE}/vehicles/{vin}/containers/vehiclestatus",
            f"{MERCEDES_API_BASE}/vehicles/{vin}/status",
            f"{MERCEDES_API_BASE}/vehicles/{vin}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                logger.info(f"Trying status endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    return {
                        'success': True, 
                        'data': response.json(),
                        'endpoint_used': endpoint
                    }
                elif response.status_code == 404:
                    continue
                else:
                    logger.error(f"Status request failed at {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Status request error for {endpoint}: {str(e)}")
                continue
        
        return {
            'success': False, 
            'error': 'Unable to get vehicle status - tried all known endpoints',
            'endpoints_tried': endpoints_to_try
        }

# Initialize Mercedes API client
mercedes_client = MercedesAPI()

def verify_api_key(request):
    """Verify the API key from the request"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not API_KEY:
        logger.warning("API_KEY environment variable not set")
        return True  # Allow if no API key is configured
    return api_key == API_KEY

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'Mercedes Remote Start API is running',
        'service': '2025 Mercedes-AMG C43 Remote Start',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': '/',
            'auth_url': '/auth/url',
            'auth_callback': '/auth/callback', 
            'remote_start': '/start-engine',
            'vehicle_status': '/vehicle-status'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Detailed health check"""
    config_status = {
        'CLIENT_ID': 'configured' if MERCEDES_CLIENT_ID else 'missing',
        'CLIENT_SECRET': 'configured' if MERCEDES_CLIENT_SECRET else 'missing',
        'REDIRECT_URI': 'configured' if MERCEDES_REDIRECT_URI else 'missing',
        'VEHICLE_VIN': 'configured' if VEHICLE_VIN else 'missing',
        'API_KEY': 'configured' if API_KEY else 'missing'
    }
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'configuration': config_status,
        'token_status': {
            'has_access_token': bool(mercedes_client.access_token),
            'token_valid': mercedes_client.is_token_valid() if mercedes_client.access_token else False
        }
    })

@app.route('/auth/url', methods=['GET'])
def get_auth_url():
    """Get OAuth authorization URL"""
    if not verify_api_key(request):
        return jsonify({'error': 'Invalid API key'}), 401
    
    if not MERCEDES_CLIENT_ID:
        return jsonify({'error': 'Mercedes client ID not configured'}), 500
    
    try:
        auth_url = mercedes_client.get_authorization_url()
        return jsonify({
            'auth_url': auth_url,
            'instructions': [
                '1. Open this URL in your browser',
                '2. Login with your Mercedes me account', 
                '3. Grant permissions to the application',
                '4. Copy the authorization code from the callback URL',
                '5. Use the code with /auth/callback endpoint'
            ]
        })
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        return jsonify({'error': 'Failed to generate authorization URL'}), 500

@app.route('/auth/callback', methods=['GET', 'POST'])
def auth_callback():
    """Handle OAuth callback"""
    # Get code from query params (GET) or form data (POST)
    code = request.args.get('code') or request.form.get('code') or request.json.get('code') if request.json else None
    
    if not code:
        return jsonify({
            'error': 'Authorization code not provided',
            'help': 'Provide the code as: ?code=YOUR_CODE or POST with {"code": "YOUR_CODE"}'
        }), 400
    
    try:
        if mercedes_client.exchange_code_for_token(code):
            return jsonify({
                'success': True,
                'message': 'Authentication successful! You can now use remote start.',
                'token_expires_at': mercedes_client.token_expires_at.isoformat() if mercedes_client.token_expires_at else None
            })
        else:
            return jsonify({'error': 'Authentication failed'}), 400
    except Exception as e:
        logger.error(f"Auth callback error: {str(e)}")
        return jsonify({'error': 'Authentication processing failed'}), 500

@app.route('/start-engine', methods=['POST', 'GET'])
def start_engine():
    """Remote start endpoint for Siri"""
    if not verify_api_key(request):
        return jsonify({'error': 'Invalid API key'}), 401
    
    if not VEHICLE_VIN:
        return jsonify({'error': 'Vehicle VIN not configured'}), 500
    
    if not mercedes_client.access_token:
        return jsonify({
            'error': 'Not authenticated. Please complete OAuth flow first.',
            'auth_url_endpoint': '/auth/url'
        }), 401
    
    try:
        logger.info(f"Remote start requested for VIN: {VEHICLE_VIN}")
        result = mercedes_client.send_remote_start_command(VEHICLE_VIN)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Your Mercedes-AMG C43 is starting up! 🚗',
                'timestamp': datetime.now().isoformat(),
                'details': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'details': result
            }), 400
            
    except Exception as e:
        logger.error(f"Remote start error: {str(e)}")
        return jsonify({'error': 'Remote start request failed'}), 500

@app.route('/vehicle-status', methods=['GET'])
def vehicle_status():
    """Get vehicle status"""
    if not verify_api_key(request):
        return jsonify({'error': 'Invalid API key'}), 401
    
    if not VEHICLE_VIN:
        return jsonify({'error': 'Vehicle VIN not configured'}), 500
    
    if not mercedes_client.access_token:
        return jsonify({
            'error': 'Not authenticated. Please complete OAuth flow first.',
            'auth_url_endpoint': '/auth/url'
        }), 401
    
    try:
        result = mercedes_client.get_vehicle_status(VEHICLE_VIN)
        
        if result['success']:
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'vehicle_vin': VEHICLE_VIN,
                'status': result['data'],
                'endpoint_used': result.get('endpoint_used')
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'details': result
            }), 400
            
    except Exception as e:
        logger.error(f"Vehicle status error: {str(e)}")
        return jsonify({'error': 'Vehicle status request failed'}), 500

@app.route('/test-connection', methods=['GET'])
def test_connection():
    """Test Mercedes API connection"""
    if not verify_api_key(request):
        return jsonify({'error': 'Invalid API key'}), 401
    
    if not mercedes_client.access_token:
        return jsonify({
            'error': 'Not authenticated',
            'message': 'Complete OAuth flow first using /auth/url'
        }), 401
    
    # Test with a simple API call
    headers = {
        'Authorization': f'Bearer {mercedes_client.access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Try to get basic vehicle info
        test_url = f"{MERCEDES_API_BASE}/vehicles/{VEHICLE_VIN}"
        response = requests.get(test_url, headers=headers, timeout=30)
        
        return jsonify({
            'connection_test': 'completed',
            'api_response_code': response.status_code,
            'api_response': response.json() if response.status_code == 200 else response.text,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'connection_test': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health', 
            'GET /auth/url',
            'POST /auth/callback',
            'POST /start-engine',
            'GET /vehicle-status',
            'GET /test-connection'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on our end'
    }), 500

if __name__ == '__main__':
    # Check for required environment variables
    required_vars = ['MERCEDES_CLIENT_ID', 'MERCEDES_CLIENT_SECRET', 'VEHICLE_VIN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Set these environment variables in Render dashboard:")
        for var in missing_vars:
            logger.info(f"- {var}")
        # Don't exit, let Render handle the error
    
    port = int(os.getenv('PORT', 10000))
    logger.info(f"Starting Mercedes Remote Start API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
