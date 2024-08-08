import React, { useState } from 'react';
import { TextField, Button, Container, Typography, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const AddStocks = () => {
  const [stock, setStock] = useState('');
  const [count, setCount] = useState('');
  const [type, setType] = useState('');
  const [_price, setPrice] = useState('');
  const [_date, setDate] = useState('');

    const navigate = useNavigate();
    
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await loginUser(stock, count);
    console.log(result);
  };

  const loginUser = async (stock, count) =>{
    try{
        const token = localStorage.getItem('access');
        const response = await fetch('api/transactions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                product: stock,
                quantity: count,
                transactionType: type,
                price: _price,
                date: _date
            })
        })
        const data = await response.json();
        if (!response.ok){
            throw new Error(data.username || 'Network response was not ok');
        }
        alert('login successful');
        navigate('/');
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
          Login
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="stock"
            variant="outlined"
            margin="normal"
            fullWidth
            value={stock}
            onChange={(e) => setStock(e.target.value)}
          />
          <TextField
            label="count"
            type="count"
            variant="outlined"
            margin="normal"
            fullWidth
            value={count}
            onChange={(e) => setCount(e.target.value)}
          />
          <TextField
            label="type"
            type="count"
            variant="outlined"
            margin="normal"
            fullWidth
            value={type}
            onChange={(e) => setType(e.target.value)}
          />
          <TextField
            label="_price"
            type="count"
            variant="outlined"
            margin="normal"
            fullWidth
            value={_price}
            onChange={(e) => setPrice(e.target.value)}
          />
          <TextField
            label="_date"
            type="count"
            variant="outlined"
            margin="normal"
            fullWidth
            value={_date}
            onChange={(e) => setDate(e.target.value)}
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

export default AddStocks;