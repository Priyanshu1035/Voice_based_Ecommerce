from flask import Flask, jsonify
import subprocess
import threading

app = Flask(__name__)

# Function to start the voice-based eCommerce app
def get_email_info():
    # Assuming the voice-based eCommerce script is main.py
    subprocess.call(['python3', 'main.py'])

@app.route('/get_email_info', methods=['POST'])
def start_voice_ecommerce():
    # Start the voice app in a separate thread so that it doesn't block the request
    threading.Thread(target=get_email_info).start()
    return jsonify({'message': 'Voice app started'}), 200

if __name__ == '__main__':
    app.run(debug=True)
