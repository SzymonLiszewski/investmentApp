import React, { useState } from 'react';
import { TextField, Button, Container, Typography, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../AuthContext';

const XtbLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { isLoggedIn, login } = useAuth();
    
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await loginUser(email, password);
    //console.log(result);
  };

  const loginUser = async (email, passwd) =>{
    
    try{
        const response = await fetch('api/analytics/integration/xtb/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'userId': email,
                'password': passwd
            },
            
        })
        const data = await response.json();
        console.log(data)
        if (!response.ok){
            throw new Error(data.username || 'Network response was not ok');
        }
        if (data['status']==true){
            alert('login successful');
            localStorage.setItem('id', email)
            localStorage.setItem('pwd', passwd)
            navigate('/portfolio');
            return data
        }
        if (data['status'] == false){
            console.log(email)
            alert("incorrect password or id")
            return data;
        }

        return data;
    }catch (error){
        alert(error);
    }
  }

  return (
    <Container maxWidth="xs">
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Login to xtb account
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="id"
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

export default XtbLogin;