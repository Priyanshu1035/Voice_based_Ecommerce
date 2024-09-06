import React from 'react';

function App() {
  const handleButtonClick = () => {
    fetch('/get_email_info', {
      method: 'POST',
    })
    .then(response => {
      if (response.ok) {
        alert('Voice eCommerce app started!');
      } else {
        alert('Failed to start the app.');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Error occurred. Check console for details.');
    });
  };

  return (
    <div style={{ textAlign: 'center', paddingTop: '50px' }}>
      <h1>Voice-Based E-Commerce</h1>
      <button 
        style={{ padding: '15px 30px', fontSize: '20px' }} 
        onClick={handleButtonClick}>
        Start Voice Shopping
      </button>
    </div>
  );
}

export default App;
