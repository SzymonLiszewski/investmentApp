import React, { useState } from 'react';
import { TextField, Button, Container, Typography, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../AuthContext';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { isLoggedIn, login } = useAuth();
    
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await loginUser(email, password);
    console.log(result);
    localStorage.setItem('access', result.access);
    localStorage.setItem('refresh', result.refresh);
  };

  const loginUser = async (email, password) =>{
    
    try{
        const response = await fetch('api/token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: email,
                password: password
            })
        })
        const data = await response.json();
        if (!response.ok){
            throw new Error(data.username || 'Network response was not ok');
        }
        alert('login successful');
        login()
        navigate('/');
        return data;
    }catch (error){
        alert(error);
    }
  }

  return (
    <Container maxWidth="xs" sx={{ width: '100%' }}>
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Login
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Email"
            variant="outlined"
            margin="normal"
            fullWidth
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            label="Password"
            type="password"
            variant="outlined"
            margin="normal"
            fullWidth
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            style={{ marginTop: '16px' }}
          >
            Login
          </Button>
        </form>
      </Box>
    </Container>
  );
};

export default LoginForm;