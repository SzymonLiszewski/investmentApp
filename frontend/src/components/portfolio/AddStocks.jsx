import React, { useState, useEffect, useCallback } from 'react';
import { TextField, Button, Container, Typography, Box, MenuItem, Select, FormControl, InputLabel, Autocomplete } from '@mui/material';
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
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);

  const navigate = useNavigate();

  // Debounced search function
  const searchAssets = useCallback(async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('access');
      const params = new URLSearchParams({
        q: query,
        asset_type: assetType,
        limit: '20'
      });
      
      const response = await fetch(`api/assets/search/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data);
      } else {
        setSuggestions([]);
      }
    } catch (error) {
      console.error('Error searching assets:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, [assetType]);

  // Debounce effect
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery) {
        searchAssets(searchQuery);
      } else {
        setSuggestions([]);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery, searchAssets]);

  // Reset search when asset type changes
  useEffect(() => {
    setSearchQuery('');
    setSuggestions([]);
    setSelectedAsset(null);
    setSymbol('');
    setName('');
  }, [assetType]);

  // Handle asset selection from autocomplete
  const handleAssetSelect = (event, value) => {
    if (value) {
      setSelectedAsset(value);
      setSymbol(value.symbol || '');
      setName(value.name || '');
      setSearchQuery(value.symbol || value.name || '');
    } else {
      setSelectedAsset(null);
      setSymbol('');
      setName('');
      setSearchQuery('');
    }
  };

  // Handle manual input change
  const handleSearchInputChange = (event, newValue) => {
    setSearchQuery(newValue || '');
    if (!newValue) {
      setSelectedAsset(null);
      setSymbol('');
      setName('');
    }
  };
    
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
              <Autocomplete
                freeSolo
                options={suggestions}
                getOptionLabel={(option) => {
                  if (typeof option === 'string') return option;
                  return `${option.symbol} - ${option.name}`;
                }}
                loading={loading}
                value={selectedAsset}
                inputValue={searchQuery}
                onInputChange={handleSearchInputChange}
                onChange={handleAssetSelect}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search by Symbol or Name *"
                    variant="outlined"
                    margin="normal"
                    required
                    helperText="Start typing to search for stocks"
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props} key={option.id}>
                    <Box>
                      <Typography variant="body1" fontWeight="bold">
                        {option.symbol}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {option.name}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
              <TextField
                label="Symbol *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={!!selectedAsset}
              />
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!!selectedAsset}
              />
            </>
          )}

          {assetType === 'bonds' && (
            <>
              <Autocomplete
                freeSolo
                options={suggestions}
                getOptionLabel={(option) => {
                  if (typeof option === 'string') return option;
                  return option.symbol ? `${option.symbol} - ${option.name}` : option.name;
                }}
                loading={loading}
                value={selectedAsset}
                inputValue={searchQuery}
                onInputChange={handleSearchInputChange}
                onChange={handleAssetSelect}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search by Symbol or Name *"
                    variant="outlined"
                    margin="normal"
                    required
                    helperText="Start typing to search for bonds"
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props} key={option.id}>
                    <Box>
                      {option.symbol && (
                        <Typography variant="body1" fontWeight="bold">
                          {option.symbol}
                        </Typography>
                      )}
                      <Typography variant="body2" color="text.secondary">
                        {option.name}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!!selectedAsset}
              />
              <TextField
                label="Symbol (optional)"
                variant="outlined"
                margin="normal"
                fullWidth
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={!!selectedAsset}
              />
            </>
          )}

          {assetType === 'cryptocurrencies' && (
            <>
              <Autocomplete
                freeSolo
                options={suggestions}
                getOptionLabel={(option) => {
                  if (typeof option === 'string') return option;
                  return option.symbol ? `${option.symbol} - ${option.name}` : option.name;
                }}
                loading={loading}
                value={selectedAsset}
                inputValue={searchQuery}
                onInputChange={handleSearchInputChange}
                onChange={handleAssetSelect}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search by Symbol or Name *"
                    variant="outlined"
                    margin="normal"
                    required
                    helperText="Start typing to search for cryptocurrencies"
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props} key={option.id}>
                    <Box>
                      {option.symbol && (
                        <Typography variant="body1" fontWeight="bold">
                          {option.symbol}
                        </Typography>
                      )}
                      <Typography variant="body2" color="text.secondary">
                        {option.name}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
              <TextField
                label="Name *"
                variant="outlined"
                margin="normal"
                fullWidth
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!!selectedAsset}
              />
              <TextField
                label="Symbol (optional)"
                variant="outlined"
                margin="normal"
                fullWidth
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={!!selectedAsset}
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