import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || window.location.origin;

export default function Register() {
  const [formData, setFormData] = useState({
    phone_number: '',
    roll_number: '',
    student_name: '',
    hostel_name: '',
    room_number: '',
    email: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    try {
      // Get phone from URL parameter
      const params = new URLSearchParams(window.location.search);
      const phone = params.get('phone');
      
      console.log('URL phone parameter:', phone);
      
      if (phone) {
        // Format phone number correctly
        let formattedPhone = phone;
        if (!formattedPhone.startsWith('whatsapp:')) {
          if (!formattedPhone.startsWith('+')) {
            formattedPhone = `+${formattedPhone}`;
          }
          formattedPhone = `whatsapp:${formattedPhone}`;
        }
        
        console.log('Formatted phone:', formattedPhone);
        
        setFormData(prev => ({ 
          ...prev, 
          phone_number: formattedPhone
        }));
      } else {
        console.log('No phone parameter in URL');
      }
    } catch (err) {
      console.error('Error parsing URL:', err);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate phone number exists
    if (!formData.phone_number) {
      setError('Phone number is missing. Please use the registration link from WhatsApp.');
      setLoading(false);
      return;
    }

    // Create submission data with auto-generated college_id
    const submitData = {
      ...formData,
      college_id: `FIXXO${Date.now()}`
    };

    console.log('Submitting data:', submitData);

    try {
      const response = await axios.post(`${API_URL}/api/register`, submitData);
      console.log('Registration success:', response.data);
      setSuccess(true);
    } catch (err) {
      console.error('Registration error:', err.response?.data);
      setError(err.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '20px',
          padding: '40px',
          maxWidth: '500px',
          width: '100%',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
        }}>
          <div style={{ fontSize: '80px', marginBottom: '20px' }}>✅</div>
          <h1 style={{ fontSize: '32px', color: '#1f2937', marginBottom: '20px' }}>
            Registration Complete!
          </h1>
          <p style={{ fontSize: '18px', color: '#6b7280', marginBottom: '30px' }}>
            You can now send complaints via WhatsApp. We'll automatically use your registered details.
          </p>
          <div style={{
            backgroundColor: '#eff6ff',
            border: '2px solid #3b82f6',
            borderRadius: '10px',
            padding: '20px'
          }}>
            <p style={{ fontSize: '14px', color: '#1e40af', fontWeight: 'bold', marginBottom: '10px' }}>
              Send your complaint to:
            </p>
            <p style={{ fontSize: '24px', color: '#2563eb', fontFamily: 'monospace' }}>
              +1 415 523 8886
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '20px',
        padding: '40px',
        maxWidth: '600px',
        width: '100%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ fontSize: '36px', color: '#1f2937', marginBottom: '10px' }}>
            🏠 Fixxo Registration
          </h1>
          <p style={{ color: '#6b7280' }}>One-time setup for hostel complaint tracking</p>
        </div>

        <form onSubmit={handleSubmit}>
          
          {/* Roll Number */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>
              Roll Number / Student ID *
            </label>
            <input
              type="text"
              required
              value={formData.roll_number}
              onChange={(e) => setFormData({...formData, roll_number: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px'
              }}
              placeholder="e.g., 2023001 or CS001"
            />
          </div>

          {/* Full Name */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>
              Full Name *
            </label>
            <input
              type="text"
              required
              value={formData.student_name}
              onChange={(e) => setFormData({...formData, student_name: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px'
              }}
              placeholder="e.g., Swaraj Kumar Behera"
            />
          </div>

          {/* Hostel Name */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>
              Hostel Name *
            </label>
            <select
              required
              value={formData.hostel_name}
              onChange={(e) => setFormData({...formData, hostel_name: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px'
              }}
            >
              <option value="">Select Hostel</option>
              <option value="Kaveri Hostel">Kaveri Hostel</option>
              <option value="Ganga Hostel">Ganga Hostel</option>
              <option value="Yamuna Hostel">Yamuna Hostel</option>
              <option value="KP-10B">KP-10B</option>
              <option value="Block A">Block A</option>
              <option value="Block B">Block B</option>
              <option value="Block C">Block C</option>
              <option value="Block D">Block D</option>
            </select>
          </div>

          {/* Room Number */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>
              Room Number *
            </label>
            <input
              type="text"
              required
              value={formData.room_number}
              onChange={(e) => setFormData({...formData, room_number: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px'
              }}
              placeholder="e.g., 305"
            />
          </div>

          {/* Email (Optional) */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>
              Email (Optional)
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px'
              }}
              placeholder="your.email@example.com"
            />
          </div>

          {/* WhatsApp Number (Read-only) */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>
              WhatsApp Number
            </label>
            <input
              type="text"
              value={formData.phone_number || 'Not provided - please use registration link from WhatsApp'}
              disabled
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '16px',
                backgroundColor: '#f3f4f6',
                color: '#6b7280'
              }}
            />
            {!formData.phone_number && (
              <p style={{ fontSize: '12px', color: '#dc2626', marginTop: '5px' }}>
                ⚠️ Phone number not detected. Please use the registration link from WhatsApp.
              </p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              backgroundColor: '#fee2e2',
              border: '2px solid #ef4444',
              borderRadius: '8px',
              padding: '15px',
              marginBottom: '20px',
              color: '#991b1b'
            }}>
              ❌ {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !formData.phone_number}
            style={{
              width: '100%',
              background: loading || !formData.phone_number 
                ? 'linear-gradient(135deg, #9ca3af 0%, #6b7280 100%)'
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              fontWeight: 'bold',
              padding: '15px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '18px',
              cursor: loading || !formData.phone_number ? 'not-allowed' : 'pointer',
              opacity: loading || !formData.phone_number ? 0.6 : 1
            }}
          >
            {loading ? 'Registering...' : 'Complete Registration'}
          </button>
        </form>
      </div>
    </div>
  );
}