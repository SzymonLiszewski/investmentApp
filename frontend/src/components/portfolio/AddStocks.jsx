import React, { useState } from 'react';
import { TextField, Button, Container, Typography, Box, MenuItem, Select, FormControl, InputLabel } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import '../styles/AddStocks.css';

const AddStocks = () => {
  const [assetType, setAssetType] = useState('stocks');
  const [symbol, setSymbol] = useState('');
  const [name, setName] = useState('');
  const [count, setCount] = useState('');
  const [type, setType] = useState('B');
  const [_price, setPrice] = useState('');
  const [_date, setDate] = useState('');

  const navigate = useNavigate();
    
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await addAssetAndTransaction();
    console.log(result);
  };

  const addAssetAndTransaction = async () => {
    try {
      const token = localStorage.getItem('access');
      
      // Prepare transaction data with asset information
      const transactionData = {
        quantity: parseFloat(count),
        transactionType: type,
        price: _price ? parseFloat(_price) : null,
        date: _date || new Date().toISOString().split('T')[0],
        asset_type: assetType,
        name: name
      };

      // Add symbol if provided
      if (assetType === 'stocks' || (assetType === 'bonds' || assetType === 'cryptocurrencies') && symbol) {
        transactionData.symbol = symbol;
      }

      // Create transaction - backend will handle asset creation if needed
      const transactionResponse = await fetch('api/transactions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(transactionData)
      });

      const data = await transactionResponse.json();
      if (!transactionResponse.ok) {
        throw new Error(JSON.stringify(data) || 'Network response was not ok');
      }

      alert('Asset added successfully');
      navigate('/');
      return data;
    } catch (error) {
      alert('Error: ' + error.message);
    }
  }

  return (
    <div className="add-stocks-container">
      <Container maxWidth="xs" sx={{ width: '100%' }}>
        <Box
          display="flex"
          flexDirection="column"
          justifyContent="center"
          alignItems="center"
          width="100%"
        >
          <Typography variant="h4" component="h1" gutterBottom>
            Add Assets
          </Typography>
          <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Asset Type</InputLabel>
            <Select
              value={assetType}
              label="Asset Type"
              onChange={(e) => setAssetType(e.target.value)}
            >
              <MenuItem value="stocks">Stocks</MenuItem>
              <MenuItem value="bonds">Bonds</MenuItem>
              <MenuItem value="cryptocurrencies">Cryptocurrencies</MenuItem>
            </Select>
          </FormControl>

          {assetType === 'stocks' && (
            <>
              <TextField
                label="Symbol *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
              />
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </>
          )}

          {assetType === 'bonds' && (
            <>
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <TextField
                label="Symbol (optional)"
                variant="outlined"
                margin="normal"
                fullWidth
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
              />
            </>
          )}

          {assetType === 'cryptocurrencies' && (
            <>
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <TextField
                label="Symbol (optional)"
                variant="outlined"
                margin="normal"
                fullWidth
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
              />
            </>
          )}

          <TextField
            label="Quantity *"
            type="number"
            variant="outlined"
            margin="normal"
            fullWidth
            required
            value={count}
            onChange={(e) => setCount(e.target.value)}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Transaction Type</InputLabel>
            <Select
              value={type}
              label="Transaction Type"
              onChange={(e) => setType(e.target.value)}
            >
              <MenuItem value="B">Buy</MenuItem>
              <MenuItem value="S">Sell</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Price"
            type="number"
            variant="outlined"
            margin="normal"
            fullWidth
            value={_price}
            onChange={(e) => setPrice(e.target.value)}
          />
          <TextField
            label="Date"
            type="date"
            variant="outlined"
            margin="normal"
            fullWidth
            InputLabelProps={{
              shrink: true,
            }}
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
            Add Assets
          </Button>
          </form>
        </Box>
      </Container>
    </div>
  );
};

export default AddStocks;